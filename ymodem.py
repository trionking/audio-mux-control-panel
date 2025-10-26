"""
ymodem.py

Y-MODEM 파일 전송 프로토콜 구현
"""

import os
import time
from PyQt5.QtCore import QThread, pyqtSignal


# Y-MODEM 제어 문자
SOH = 0x01  # 128-byte block
STX = 0x02  # 1024-byte block
EOT = 0x04  # End of transmission
ACK = 0x06  # Acknowledge
NAK = 0x15  # Negative acknowledge
CAN = 0x18  # Cancel
CRC16 = 0x43  # 'C' for CRC mode


class YModemSender(QThread):
    """Y-MODEM 파일 전송 스레드"""

    # 시그널
    progress = pyqtSignal(int)  # 진행률 (0~100)
    status = pyqtSignal(str)  # 상태 메시지
    finished = pyqtSignal(bool, str)  # (성공 여부, 메시지)

    def __init__(self, serial_comm, file_path):
        super().__init__()
        self.serial = serial_comm
        self.file_path = file_path
        self.cancel_flag = False

    def cancel(self):
        """전송 취소"""
        self.cancel_flag = True

    def run(self):
        """Y-MODEM 전송 실행"""
        try:
            # 파일 열기
            if not os.path.exists(self.file_path):
                self.finished.emit(False, "File not found")
                return

            file_size = os.path.getsize(self.file_path)
            file_name = os.path.basename(self.file_path)

            self.status.emit(f"Waiting for receiver... ({file_name}, {file_size} bytes)")

            # 수신측 준비 대기 (C 문자)
            if not self._wait_for_c():
                self.finished.emit(False, "Timeout waiting for receiver")
                return

            # 첫 번째 패킷 (파일 정보) 전송
            if not self._send_file_info_packet(file_name, file_size):
                self.finished.emit(False, "Failed to send file info")
                return

            # 파일 데이터 전송
            with open(self.file_path, 'rb') as f:
                packet_num = 1
                total_packets = (file_size + 1023) // 1024

                while True:
                    if self.cancel_flag:
                        self._send_cancel()
                        self.finished.emit(False, "Cancelled by user")
                        return

                    # 데이터 읽기
                    data = f.read(1024)
                    if not data:
                        break  # 파일 끝

                    # 패킷 전송
                    if not self._send_data_packet(packet_num, data):
                        self.finished.emit(False, f"Failed to send packet {packet_num}")
                        return

                    # 진행률 업데이트
                    progress_pct = int((packet_num / total_packets) * 100)
                    self.progress.emit(progress_pct)
                    self.status.emit(f"Sending... {packet_num}/{total_packets} packets")

                    packet_num += 1

            # EOT 전송
            if not self._send_eot():
                self.finished.emit(False, "Failed to send EOT")
                return

            self.status.emit("Transfer complete!")
            self.progress.emit(100)
            self.finished.emit(True, "File transferred successfully")

        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

    def _wait_for_c(self, timeout=10.0):
        """'C' 문자 대기"""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            data = self.serial.read_raw(1, timeout=0.5)
            if data and len(data) > 0 and data[0] == CRC16:
                return True

        return False

    def _send_file_info_packet(self, file_name, file_size):
        """파일 정보 패킷 전송 (Packet 0)"""
        # 패킷 구성: SOH + 0x00 + 0xFF + filename\0 + size + padding + CRC
        packet = bytearray(128)

        # 파일명 및 크기 저장
        file_info = f"{file_name}\x00{file_size}".encode('utf-8')
        packet[:len(file_info)] = file_info

        # 패킷 전송
        return self._send_packet(0, packet)

    def _send_data_packet(self, packet_num, data):
        """데이터 패킷 전송"""
        # 1024 바이트로 패딩
        packet = bytearray(data)
        if len(packet) < 1024:
            packet.extend(b'\x1A' * (1024 - len(packet)))  # SUB 문자로 패딩

        return self._send_packet(packet_num, packet)

    def _send_packet(self, packet_num, data):
        """패킷 전송 (재시도 포함)"""
        max_retries = 10

        for retry in range(max_retries):
            # 패킷 구성
            if len(data) == 128:
                header = SOH
            else:
                header = STX

            packet_bytes = bytearray()
            packet_bytes.append(header)
            packet_bytes.append(packet_num & 0xFF)
            packet_bytes.append((~packet_num) & 0xFF)
            packet_bytes.extend(data)

            # CRC-16 계산 및 추가
            crc = self._crc16(data)
            packet_bytes.append((crc >> 8) & 0xFF)
            packet_bytes.append(crc & 0xFF)

            # 전송
            if not self.serial.write_raw(bytes(packet_bytes)):
                return False

            # ACK 대기
            response = self.serial.read_raw(1, timeout=5.0)
            if response and len(response) > 0:
                if response[0] == ACK:
                    return True  # 성공
                elif response[0] == NAK:
                    self.status.emit(f"NAK received, retrying... ({retry + 1}/{max_retries})")
                    continue  # 재시도
                elif response[0] == CAN:
                    return False  # 취소

            # 타임아웃
            self.status.emit(f"Timeout, retrying... ({retry + 1}/{max_retries})")

        return False  # 최대 재시도 초과

    def _send_eot(self):
        """EOT 전송"""
        # EOT 전송
        self.serial.write_raw(bytes([EOT]))

        # ACK 대기
        response = self.serial.read_raw(1, timeout=5.0)
        if response and len(response) > 0 and response[0] == ACK:
            # Null 패킷 대기 (일부 수신기)
            self._wait_for_c(timeout=2.0)
            # Null 패킷 전송
            null_packet = bytes([SOH, 0x00, 0xFF] + [0] * 128 + [0, 0])
            self.serial.write_raw(null_packet)
            response = self.serial.read_raw(1, timeout=5.0)
            return True

        return False

    def _send_cancel(self):
        """전송 취소"""
        self.serial.write_raw(bytes([CAN, CAN, CAN, CAN, CAN]))

    def _crc16(self, data):
        """CRC-16 계산"""
        crc = 0

        for byte in data:
            crc ^= byte << 8

            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1

                crc &= 0xFFFF

        return crc
