"""
main.py

Audio Mux Control Panel - 메인 애플리케이션
"""

import sys
import os
import wave
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox,
                              QComboBox, QPushButton, QLabel, QTableWidgetItem, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5 import uic

from serial_comm import SerialComm, list_serial_ports
from ymodem import YModemSender
from audio_converter import AudioConverter, check_ffmpeg_installed
from ansi_parser import ansi_to_html
from equalizer_widget import EqualizerWidget


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self):
        super().__init__()

        # UI 로드
        ui_path = os.path.join(os.path.dirname(__file__), 'mainwindow.ui')
        uic.loadUi(ui_path, self)

        # 시리얼 통신 객체
        self.serial = SerialComm()
        self.serial.received.connect(self.on_data_received)
        self.serial.error.connect(self.on_serial_error)
        self.serial.connected.connect(self.on_connected)
        self.serial.disconnected.connect(self.on_disconnected)

        # Y-MODEM 전송 객체
        self.ymodem_sender = None

        # 오디오 미리 듣기 플레이어
        self.media_player = QMediaPlayer()
        self.is_playing = False

        # 초기 설정
        self.init_ui()
        self.refresh_ports()

        # 이퀄라이저 위젯 설정 (UI 로드 후)
        self.setup_equalizer()

        # FFmpeg 확인
        if not check_ffmpeg_installed():
            self.log_message("WARNING: FFmpeg not found. Audio conversion may not work.", color='red')
            self.log_message("Download FFmpeg from https://ffmpeg.org/download.html", color='red')

    def init_ui(self):
        """UI 초기화"""
        # 버튼 연결
        self.pushButton_Refresh.clicked.connect(self.refresh_ports)
        self.pushButton_Connect.clicked.connect(self.toggle_connection)
        self.pushButton_Browse.clicked.connect(self.browse_file)
        self.pushButton_Preview.clicked.connect(self.toggle_preview)
        self.pushButton_Upload.clicked.connect(self.upload_file)
        self.pushButton_BrowseInput.clicked.connect(self.browse_input_file)
        self.pushButton_Convert.clicked.connect(self.convert_audio)
        self.pushButton_ClearLog.clicked.connect(self.clear_log)

        # 메뉴 액션 연결
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)

        # 초기 상태
        self.pushButton_Upload.setEnabled(False)
        self.progressBar_Upload.setValue(0)

        # 보드레이트 기본값 설정 (115200)
        self.comboBox_Baudrate.setCurrentIndex(4)

        # 채널 제어 테이블 설정
        self.setup_channel_control()

        # 초기에는 채널 제어 비활성화 (연결 전)
        self.tableWidget_Channels.setEnabled(False)

    def setup_channel_control(self):
        """채널 제어 테이블 초기화"""
        # 채널별 위젯 저장용
        self.channel_widgets = []

        # 테이블 헤더 크기 조정
        self.tableWidget_Channels.setColumnWidth(0, 60)   # 채널
        self.tableWidget_Channels.setColumnWidth(1, 250)  # 파일
        self.tableWidget_Channels.setColumnWidth(2, 80)   # 새로고침
        self.tableWidget_Channels.setColumnWidth(3, 150)  # 제어
        self.tableWidget_Channels.setColumnWidth(4, 100)  # 상태

        # 행 높이 조정 (6개 행에 딱 맞게)
        for i in range(6):
            self.tableWidget_Channels.setRowHeight(i, 30)

        # 6개 채널에 대해 위젯 생성
        for ch in range(6):
            # 채널 번호 (0열)
            channel_item = QTableWidgetItem(f"채널 {ch}")
            channel_item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget_Channels.setItem(ch, 0, channel_item)

            # 파일 선택 콤보박스 (1열)
            file_combo = QComboBox()
            file_combo.addItem("(파일 없음)")
            self.tableWidget_Channels.setCellWidget(ch, 1, file_combo)

            # 새로고침 버튼 (2열)
            refresh_btn = QPushButton("새로고침")
            refresh_btn.clicked.connect(lambda checked, c=ch: self.refresh_channel_files(c))
            self.tableWidget_Channels.setCellWidget(ch, 2, refresh_btn)

            # 제어 버튼 (3열) - 플레이/중지 버튼을 포함하는 위젯
            control_widget = QWidget()
            control_layout = QHBoxLayout()
            control_layout.setContentsMargins(2, 2, 2, 2)

            play_btn = QPushButton("▶ 플레이")
            play_btn.clicked.connect(lambda checked, c=ch: self.play_channel(c))

            stop_btn = QPushButton("■ 중지")
            stop_btn.clicked.connect(lambda checked, c=ch: self.stop_channel(c))

            control_layout.addWidget(play_btn)
            control_layout.addWidget(stop_btn)
            control_widget.setLayout(control_layout)
            self.tableWidget_Channels.setCellWidget(ch, 3, control_widget)

            # 상태 라벨 (4열)
            status_label = QLabel("정지")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("color: gray;")
            self.tableWidget_Channels.setCellWidget(ch, 4, status_label)

            # 위젯 참조 저장
            self.channel_widgets.append({
                'file_combo': file_combo,
                'refresh_btn': refresh_btn,
                'play_btn': play_btn,
                'stop_btn': stop_btn,
                'status_label': status_label
            })

    def setup_equalizer(self):
        """이퀄라이저 위젯 설정"""
        # 기존 widget_Equalizer를 EqualizerWidget으로 교체
        layout = self.widget_Equalizer.parentWidget().layout()

        # 기존 위젯의 위치 찾기 (QGridLayout)
        row, col, rowspan, colspan = -1, -1, 1, 1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == self.widget_Equalizer:
                # QGridLayout에서 위치 정보 가져오기
                row, col, rowspan, colspan = layout.getItemPosition(i)
                # 기존 위젯 제거
                layout.removeWidget(self.widget_Equalizer)
                self.widget_Equalizer.deleteLater()
                break

        # 새 이퀄라이저 위젯 생성
        self.equalizer = EqualizerWidget()
        self.equalizer.setMinimumHeight(100)
        self.equalizer.setMaximumHeight(100)

        # QGridLayout에 추가 (같은 위치에)
        if row >= 0:
            layout.addWidget(self.equalizer, row, col, rowspan, colspan)

    def refresh_ports(self):
        """포트 목록 새로고침"""
        self.comboBox_Port.clear()
        ports = list_serial_ports()

        if ports:
            self.comboBox_Port.addItems(ports)
            self.log_message(f"Found {len(ports)} port(s): {', '.join(ports)}")
        else:
            self.log_message("No serial ports found", color='orange')

    def toggle_connection(self):
        """연결/해제 토글"""
        if self.serial.is_connected():
            # 연결 해제
            self.serial.disconnect()
        else:
            # 연결
            port = self.comboBox_Port.currentText()
            if not port:
                QMessageBox.warning(self, "Error", "Please select a port")
                return

            # 보드레이트 가져오기
            baudrate = int(self.comboBox_Baudrate.currentText())

            self.serial.set_port(port, baudrate=baudrate)
            if self.serial.connect():
                self.log_message(f"Connecting to {port} at {baudrate} baud...", color='blue')
            else:
                QMessageBox.critical(self, "Error", "Failed to connect")

    def on_connected(self):
        """연결됨"""
        self.label_Status.setText("상태: 연결됨")
        self.label_Status.setStyleSheet("color: green;")
        self.pushButton_Connect.setText("연결 해제")
        self.pushButton_Upload.setEnabled(True)

        # 연결 중에는 포트 및 보드레이트 변경 불가
        self.comboBox_Port.setEnabled(False)
        self.comboBox_Baudrate.setEnabled(False)
        self.pushButton_Refresh.setEnabled(False)

        # 채널 제어 활성화
        self.tableWidget_Channels.setEnabled(True)

        # HELLO 명령 전송
        self.serial.send_command("HELLO")

    def on_disconnected(self):
        """연결 해제됨"""
        self.label_Status.setText("상태: 연결 끊김")
        self.label_Status.setStyleSheet("color: red;")
        self.pushButton_Connect.setText("연결")
        self.pushButton_Upload.setEnabled(False)

        # 연결 해제 시 포트 및 보드레이트 변경 가능
        self.comboBox_Port.setEnabled(True)
        self.comboBox_Baudrate.setEnabled(True)
        self.pushButton_Refresh.setEnabled(True)

        # 채널 제어 비활성화
        self.tableWidget_Channels.setEnabled(False)

    def on_data_received(self, data):
        """데이터 수신"""
        # ANSI 이스케이프 시퀀스를 포함한 데이터를 그대로 전달
        self.log_message(f"<< {data}", use_ansi=True)

    def on_serial_error(self, error):
        """시리얼 에러"""
        self.log_message(f"Error: {error}", color='red')

    def refresh_channel_files(self, channel):
        """채널의 파일 목록 새로고침"""
        if not self.serial.is_connected():
            QMessageBox.warning(self, "오류", "장치에 연결되지 않았습니다")
            return

        self.log_message(f">> LS {channel}", color='blue')
        self.serial.send_command(f"LS {channel}")

        # TODO: 응답을 파싱하여 콤보박스에 채우기
        # 실제로는 응답을 대기하고 파싱해야 함
        # 지금은 예시 데이터 사용
        file_combo = self.channel_widgets[channel]['file_combo']
        file_combo.clear()
        file_combo.addItem("(파일 없음)")
        # 응답 파싱 후 파일들을 추가
        # file_combo.addItem("example1.wav")
        # file_combo.addItem("example2.wav")

    def play_channel(self, channel):
        """채널 재생"""
        if not self.serial.is_connected():
            QMessageBox.warning(self, "오류", "장치에 연결되지 않았습니다")
            return

        file_combo = self.channel_widgets[channel]['file_combo']
        selected_file = file_combo.currentText()

        if selected_file == "(파일 없음)":
            QMessageBox.warning(self, "오류", "재생할 파일을 선택해주세요")
            return

        # PLAY 명령 전송
        self.log_message(f">> PLAY {channel} {selected_file}", color='blue')
        self.serial.send_command(f"PLAY {channel} {selected_file}")

        # 상태 업데이트
        status_label = self.channel_widgets[channel]['status_label']
        status_label.setText("재생 중")
        status_label.setStyleSheet("color: green; font-weight: bold;")

    def stop_channel(self, channel):
        """채널 중지"""
        if not self.serial.is_connected():
            QMessageBox.warning(self, "오류", "장치에 연결되지 않았습니다")
            return

        # STOP 명령 전송
        self.log_message(f">> STOP {channel}", color='blue')
        self.serial.send_command(f"STOP {channel}")

        # 상태 업데이트
        status_label = self.channel_widgets[channel]['status_label']
        status_label.setText("정지")
        status_label.setStyleSheet("color: gray;")

    def browse_file(self):
        """파일 선택 - WAV 파일만 허용"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "WAV 파일 선택",
            "",
            "WAV Files (*.wav);;All Files (*.*)"
        )

        if file_path:
            # WAV 파일 스펙 검증
            if self.validate_wav_file(file_path):
                self.lineEdit_FilePath.setText(file_path)
                self.log_message(f"파일 선택: {os.path.basename(file_path)} - 스펙 확인 완료", color='green')
            else:
                # 검증 실패 시 파일 경로는 설정하지 않음
                self.lineEdit_FilePath.clear()

    def validate_wav_file(self, file_path):
        """
        WAV 파일이 메인 보드 스펙에 맞는지 검증
        필수 스펙: 32000Hz, 16-bit, Mono

        Returns:
            bool: 스펙 일치 여부
        """
        try:
            with wave.open(file_path, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()

            # 스펙 확인
            is_valid = True
            errors = []

            if framerate != 32000:
                errors.append(f"샘플레이트: {framerate}Hz (필요: 32000Hz)")
                is_valid = False

            if sample_width != 2:  # 2 bytes = 16-bit
                errors.append(f"비트 깊이: {sample_width*8}bit (필요: 16bit)")
                is_valid = False

            if channels != 1:
                errors.append(f"채널: {channels}ch (필요: 1ch Mono)")
                is_valid = False

            if not is_valid:
                # 경고음 출력
                QApplication.beep()

                # 로그에 에러 출력
                self.log_message("=" * 50, color='red')
                self.log_message("⚠️ WAV 파일 스펙 불일치!", color='red')
                self.log_message(f"파일: {os.path.basename(file_path)}", color='red')
                for error in errors:
                    self.log_message(f"  - {error}", color='red')
                self.log_message("메인 보드 요구사항: 32000Hz, 16-bit, Mono", color='red')
                self.log_message("'오디오 변환기'를 사용하여 변환하세요.", color='orange')
                self.log_message("=" * 50, color='red')

                # 대화상자로도 알림
                QMessageBox.warning(
                    self,
                    "WAV 파일 스펙 불일치",
                    f"선택한 WAV 파일이 메인 보드 스펙에 맞지 않습니다.\n\n"
                    f"현재 파일:\n" + "\n".join(f"  • {e}" for e in errors) + "\n\n"
                    f"필요 스펙: 32000Hz, 16-bit, Mono\n\n"
                    f"'오디오 변환기'를 사용하여 변환하세요."
                )

                return False

            return True

        except wave.Error as e:
            QApplication.beep()
            self.log_message(f"WAV 파일 읽기 오류: {str(e)}", color='red')
            QMessageBox.critical(self, "오류", f"WAV 파일을 읽을 수 없습니다:\n{str(e)}")
            return False

        except Exception as e:
            QApplication.beep()
            self.log_message(f"파일 검증 오류: {str(e)}", color='red')
            QMessageBox.critical(self, "오류", f"파일 검증 중 오류가 발생했습니다:\n{str(e)}")
            return False

    def toggle_preview(self):
        """미리 듣기 토글"""
        if self.is_playing:
            # 재생 중이면 중지
            self.stop_preview()
        else:
            # 재생 시작
            self.start_preview()

    def start_preview(self):
        """오디오 미리 듣기 시작 (오디오 변환기 입력 파일)"""
        file_path = self.lineEdit_InputFile.text()

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "오류", "먼저 오디오 변환기에서 입력 파일을 선택해주세요")
            return

        # 미디어 설정
        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)
        self.media_player.setMedia(content)

        # 재생 시작
        self.media_player.play()
        self.is_playing = True
        self.pushButton_Preview.setText("중지")

        # 이퀄라이저 시작
        self.equalizer.start()

        # 재생 완료 시그널 연결 (한 번만)
        try:
            self.media_player.stateChanged.disconnect()
        except:
            pass
        self.media_player.stateChanged.connect(self.on_media_state_changed)

        self.log_message(f"재생 시작: {os.path.basename(file_path)}", color='blue')

    def stop_preview(self):
        """오디오 미리 듣기 중지"""
        self.media_player.stop()
        self.is_playing = False
        self.pushButton_Preview.setText("미리 듣기")

        # 이퀄라이저 중지
        self.equalizer.stop()

        self.log_message("재생 중지", color='blue')

    def on_media_state_changed(self, state):
        """미디어 재생 상태 변경"""
        # QMediaPlayer.StoppedState = 0
        if state == QMediaPlayer.StoppedState and self.is_playing:
            # 재생 완료 (자연스럽게 끝남)
            self.is_playing = False
            self.pushButton_Preview.setText("미리 듣기")

            # 이퀄라이저 중지
            self.equalizer.stop()

            self.log_message("재생 완료", color='blue')

    def upload_file(self):
        """파일 업로드 (Y-MODEM) - 검증된 WAV 파일만 업로드"""
        file_path = self.lineEdit_FilePath.text()

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "오류", "올바른 WAV 파일을 선택해주세요")
            return

        if not self.serial.is_connected():
            QMessageBox.warning(self, "오류", "장치에 연결되지 않았습니다")
            return

        channel = self.comboBox_Channel.currentIndex()

        # 파일명
        file_name = os.path.basename(file_path)

        # UPLOAD 명령 전송
        self.log_message(f">> UPLOAD {channel} {file_name}", color='blue')
        self.serial.send_command(f"UPLOAD {channel} {file_name}")

        # 잠시 대기 (보드가 Y-MODEM 준비할 시간)
        QApplication.processEvents()
        import time
        time.sleep(0.5)

        # Y-MODEM 전송 시작
        self.start_ymodem_transfer(file_path)

    def start_ymodem_transfer(self, file_path):
        """Y-MODEM 전송 시작"""
        # 이전 전송이 있으면 취소
        if self.ymodem_sender and self.ymodem_sender.isRunning():
            self.ymodem_sender.cancel()
            self.ymodem_sender.wait()

        # 새 전송 시작
        self.ymodem_sender = YModemSender(self.serial, file_path)
        self.ymodem_sender.progress.connect(self.on_ymodem_progress)
        self.ymodem_sender.status.connect(self.on_ymodem_status)
        self.ymodem_sender.finished.connect(self.on_ymodem_finished)

        # UI 비활성화
        self.pushButton_Upload.setEnabled(False)
        self.progressBar_Upload.setValue(0)

        # 전송 시작
        self.ymodem_sender.start()

    def on_ymodem_progress(self, percent):
        """Y-MODEM 진행률"""
        self.progressBar_Upload.setValue(percent)

    def on_ymodem_status(self, status):
        """Y-MODEM 상태"""
        self.log_message(f"Y-MODEM: {status}", color='purple')

    def on_ymodem_finished(self, success, message):
        """Y-MODEM 완료"""
        if success:
            self.log_message(f"Y-MODEM: {message}", color='green')
            QMessageBox.information(self, "Success", message)
        else:
            self.log_message(f"Y-MODEM Error: {message}", color='red')
            QMessageBox.critical(self, "Transfer Failed", message)

        # UI 복원
        self.pushButton_Upload.setEnabled(True)
        self.progressBar_Upload.setValue(0)

    def browse_input_file(self):
        """입력 파일 선택 (변환용)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "변환할 오디오 파일 선택",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.ogg *.m4a);;All Files (*.*)"
        )

        if file_path:
            self.lineEdit_InputFile.setText(file_path)

            # 파일 선택 시 재생 중이면 중지
            if self.is_playing:
                self.stop_preview()

            # 출력 파일명 자동 생성
            base_name = os.path.splitext(file_path)[0]
            output_path = base_name + "_32k16m.wav"
            self.lineEdit_OutputFile.setText(output_path)

    def convert_audio(self):
        """오디오 변환"""
        input_path = self.lineEdit_InputFile.text()
        output_path = self.lineEdit_OutputFile.text()

        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "오류", "올바른 입력 파일을 선택해주세요")
            return

        if not output_path:
            QMessageBox.warning(self, "오류", "출력 파일 경로를 지정해주세요")
            return

        self.log_message(f"변환 중: {input_path} -> {output_path}", color='blue')

        # 변환
        success, message = AudioConverter.convert(input_path, output_path)

        if success:
            self.log_message(message, color='green')
            QMessageBox.information(self, "완료", f"변환이 완료되었습니다!\n\n{message}")
        else:
            self.log_message(f"변환 실패: {message}", color='red')
            QMessageBox.critical(self, "변환 실패", message)

    def log_message(self, message, color='black', use_ansi=False):
        """
        로그 메시지 출력

        Args:
            message: 메시지 텍스트
            color: 기본 색상 ('black', 'red', 'green', 'blue', 'orange', 'purple')
            use_ansi: True면 ANSI 이스케이프 시퀀스 파싱, False면 기본 색상 사용
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        if use_ansi:
            # ANSI 이스케이프 시퀀스를 HTML로 변환
            message_html = ansi_to_html(message)
            html = f'<span>[{timestamp}] {message_html}</span>'
        else:
            # 기본 색상 사용
            color_map = {
                'black': '#000000',
                'red': '#FF0000',
                'green': '#008000',
                'blue': '#0000FF',
                'orange': '#FF8800',
                'purple': '#800080'
            }

            color_code = color_map.get(color, '#000000')

            # HTML 특수문자 이스케이프
            message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # HTML 형식으로 추가
            html = f'<span style="color: {color_code};">[{timestamp}] {message}</span>'

        self.textEdit_Log.append(html)

    def clear_log(self):
        """로그 클리어"""
        self.textEdit_Log.clear()

    def show_about(self):
        """About 다이얼로그"""
        QMessageBox.about(
            self,
            "About Audio Mux Control Panel",
            "Audio Mux Control Panel v1.0\n\n"
            "Multi-channel audio streaming system controller\n\n"
            "Features:\n"
            "- Serial communication with STM32H723\n"
            "- Y-MODEM file transfer\n"
            "- Audio format conversion\n\n"
            "(c) 2025"
        )

    def closeEvent(self, event):
        """종료 이벤트"""
        # 시리얼 연결 해제
        if self.serial.is_connected():
            self.serial.disconnect()
            self.serial.wait()

        # Y-MODEM 전송 취소
        if self.ymodem_sender and self.ymodem_sender.isRunning():
            self.ymodem_sender.cancel()
            self.ymodem_sender.wait()

        # 미디어 재생 중지
        if self.is_playing:
            self.media_player.stop()
            self.equalizer.stop()

        event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
