"""
equalizer_widget.py

그래픽 이퀄라이저 위젯
"""

import random
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QLinearGradient


class EqualizerWidget(QWidget):
    """그래픽 이퀄라이저 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 이퀄라이저 설정
        self.num_bars = 20  # 막대 개수
        self.bar_values = [0.0] * self.num_bars  # 각 막대의 높이 (0.0 ~ 1.0)
        self.is_playing = False

        # 애니메이션 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_bars)
        self.timer.setInterval(50)  # 50ms (20 FPS)

        # 색상 그라디언트
        self.colors = [
            QColor(0, 255, 0),      # 녹색 (낮은 주파수)
            QColor(255, 255, 0),    # 노란색 (중간 주파수)
            QColor(255, 0, 0)       # 빨간색 (높은 주파수)
        ]

    def start(self):
        """이퀄라이저 애니메이션 시작"""
        self.is_playing = True
        self.timer.start()

    def stop(self):
        """이퀄라이저 애니메이션 중지"""
        self.is_playing = False
        self.timer.stop()
        # 모든 막대를 0으로 초기화
        self.bar_values = [0.0] * self.num_bars
        self.update()

    def update_bars(self):
        """막대 값 업데이트 (애니메이션)"""
        if not self.is_playing:
            return

        # 각 막대에 랜덤한 값 설정 (부드러운 움직임을 위해 이전 값 고려)
        for i in range(self.num_bars):
            # 타겟 값 (0.1 ~ 1.0)
            target = random.uniform(0.1, 1.0)

            # 부드러운 전환 (이전 값의 70% + 새 값의 30%)
            self.bar_values[i] = self.bar_values[i] * 0.7 + target * 0.3

        # 화면 업데이트
        self.update()

    def paintEvent(self, event):
        """이퀄라이저 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 배경색
        painter.fillRect(self.rect(), QColor(26, 26, 26))

        if not self.is_playing and all(v == 0.0 for v in self.bar_values):
            # 재생 중이 아니면 중앙에 텍스트 표시
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "이퀄라이저 (미리 듣기 시 표시)")
            return

        # 막대 그리기
        width = self.width()
        height = self.height()

        bar_width = width / self.num_bars
        spacing = 2  # 막대 간격

        for i in range(self.num_bars):
            # 막대 위치 및 크기
            x = i * bar_width + spacing / 2
            bar_height = self.bar_values[i] * (height - 10)
            y = height - bar_height - 5

            # 막대 색상 (그라디언트)
            color = self.get_bar_color(self.bar_values[i])

            # 막대 그리기
            painter.fillRect(
                int(x),
                int(y),
                int(bar_width - spacing),
                int(bar_height),
                color
            )

    def get_bar_color(self, value):
        """막대 높이에 따른 색상 반환 (그라디언트)"""
        if value < 0.33:
            # 녹색
            return QColor(0, 255, 0)
        elif value < 0.66:
            # 녹색 → 노란색
            ratio = (value - 0.33) / 0.33
            r = int(255 * ratio)
            g = 255
            b = 0
            return QColor(r, g, b)
        else:
            # 노란색 → 빨간색
            ratio = (value - 0.66) / 0.34
            r = 255
            g = int(255 * (1 - ratio))
            b = 0
            return QColor(r, g, b)
