"""
serial_comm.py

시리얼 통신 모듈
"""

import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal
import time


class SerialComm(QThread):
    """시리얼 통신 스레드"""

    # 시그널 정의
    received = pyqtSignal(str)  # 수신 데이터
    error = pyqtSignal(str)  # 에러 메시지
    connected = pyqtSignal()  # 연결됨
    disconnected = pyqtSignal()  # 연결 해제됨

    def __init__(self):
        super().__init__()
        self.ser = None
        self.is_running = False
        self.port = None
        self.baudrate = 115200

    def set_port(self, port, baudrate=115200):
        """포트 설정"""
        self.port = port
        self.baudrate = baudrate

    def connect(self):
        """시리얼 포트 연결"""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()

            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )

            if self.ser.is_open:
                self.is_running = True
                self.start()  # 수신 스레드 시작
                self.connected.emit()
                return True
            else:
                self.error.emit("Failed to open serial port")
                return False

        except Exception as e:
            self.error.emit(f"Connection error: {str(e)}")
            return False

    def disconnect(self):
        """시리얼 포트 연결 해제"""
        self.is_running = False

        if self.ser and self.ser.is_open:
            time.sleep(0.1)  # 스레드 종료 대기
            self.ser.close()

        self.disconnected.emit()

    def send(self, data):
        """데이터 전송"""
        if not self.ser or not self.ser.is_open:
            self.error.emit("Serial port not connected")
            return False

        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            self.ser.write(data)
            return True

        except Exception as e:
            self.error.emit(f"Send error: {str(e)}")
            return False

    def send_command(self, command):
        """명령 전송 (자동으로 \r\n 추가)"""
        return self.send(command + '\r\n')

    def read_raw(self, size, timeout=1.0):
        """원시 데이터 읽기 (Y-MODEM용)"""
        if not self.ser or not self.ser.is_open:
            return None

        try:
            old_timeout = self.ser.timeout
            self.ser.timeout = timeout
            data = self.ser.read(size)
            self.ser.timeout = old_timeout
            return data

        except Exception as e:
            self.error.emit(f"Read error: {str(e)}")
            return None

    def write_raw(self, data):
        """원시 데이터 쓰기 (Y-MODEM용)"""
        if not self.ser or not self.ser.is_open:
            return False

        try:
            self.ser.write(data)
            return True

        except Exception as e:
            self.error.emit(f"Write error: {str(e)}")
            return False

    def run(self):
        """수신 스레드"""
        rx_buffer = ""

        while self.is_running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    # 데이터 수신
                    data = self.ser.read(self.ser.in_waiting)
                    rx_buffer += data.decode('utf-8', errors='replace')

                    # 줄바꿈으로 분리
                    while '\n' in rx_buffer:
                        line, rx_buffer = rx_buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.received.emit(line)

                time.sleep(0.01)  # CPU 사용률 감소

            except Exception as e:
                self.error.emit(f"Reception error: {str(e)}")
                time.sleep(0.1)

    def is_connected(self):
        """연결 상태 확인"""
        return self.ser and self.ser.is_open


def list_serial_ports():
    """사용 가능한 시리얼 포트 목록 반환"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
