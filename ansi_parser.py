"""
ansi_parser.py

ANSI 이스케이프 시퀀스를 HTML로 변환
"""

import re


class AnsiParser:
    """ANSI 이스케이프 시퀀스 파서"""

    # ANSI 색상 코드 매핑
    FOREGROUND_COLORS = {
        '30': '#000000',  # Black
        '31': '#CD0000',  # Red
        '32': '#00CD00',  # Green
        '33': '#CDCD00',  # Yellow
        '34': '#0000EE',  # Blue
        '35': '#CD00CD',  # Magenta
        '36': '#00CDCD',  # Cyan
        '37': '#E5E5E5',  # White
        '90': '#7F7F7F',  # Bright Black (Gray)
        '91': '#FF0000',  # Bright Red
        '92': '#00FF00',  # Bright Green
        '93': '#FFFF00',  # Bright Yellow
        '94': '#5C5CFF',  # Bright Blue
        '95': '#FF00FF',  # Bright Magenta
        '96': '#00FFFF',  # Bright Cyan
        '97': '#FFFFFF',  # Bright White
    }

    BACKGROUND_COLORS = {
        '40': '#000000',  # Black
        '41': '#CD0000',  # Red
        '42': '#00CD00',  # Green
        '43': '#CDCD00',  # Yellow
        '44': '#0000EE',  # Blue
        '45': '#CD00CD',  # Magenta
        '46': '#00CDCD',  # Cyan
        '47': '#E5E5E5',  # White
        '100': '#7F7F7F',  # Bright Black (Gray)
        '101': '#FF0000',  # Bright Red
        '102': '#00FF00',  # Bright Green
        '103': '#FFFF00',  # Bright Yellow
        '104': '#5C5CFF',  # Bright Blue
        '105': '#FF00FF',  # Bright Magenta
        '106': '#00FFFF',  # Bright Cyan
        '107': '#FFFFFF',  # Bright White
    }

    def __init__(self):
        # 현재 스타일 상태
        self.reset_style()

    def reset_style(self):
        """스타일 리셋"""
        self.fg_color = None
        self.bg_color = None
        self.bold = False
        self.underline = False
        self.italic = False

    def parse_to_html(self, text):
        """
        ANSI 이스케이프 시퀀스를 HTML로 변환

        Args:
            text: ANSI 이스케이프 시퀀스가 포함된 텍스트

        Returns:
            HTML 형식의 텍스트
        """
        # ANSI 이스케이프 시퀀스 패턴: \033[...m 또는 \x1b[...m
        ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')

        html_parts = []
        last_end = 0

        for match in ansi_pattern.finditer(text):
            # 이전 텍스트 추가
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                html_parts.append(self._wrap_with_style(plain_text))

            # ANSI 코드 파싱
            codes = match.group(1).split(';')
            self._apply_codes(codes)

            last_end = match.end()

        # 남은 텍스트 추가
        if last_end < len(text):
            plain_text = text[last_end:]
            html_parts.append(self._wrap_with_style(plain_text))

        return ''.join(html_parts)

    def _apply_codes(self, codes):
        """ANSI 코드 적용"""
        for code in codes:
            if not code:
                continue

            if code == '0':
                # Reset
                self.reset_style()
            elif code == '1':
                # Bold
                self.bold = True
            elif code == '3':
                # Italic
                self.italic = True
            elif code == '4':
                # Underline
                self.underline = True
            elif code == '22':
                # Normal intensity (not bold)
                self.bold = False
            elif code == '23':
                # Not italic
                self.italic = False
            elif code == '24':
                # Not underline
                self.underline = False
            elif code in self.FOREGROUND_COLORS:
                # Foreground color
                self.fg_color = self.FOREGROUND_COLORS[code]
            elif code in self.BACKGROUND_COLORS:
                # Background color
                self.bg_color = self.BACKGROUND_COLORS[code]

    def _wrap_with_style(self, text):
        """현재 스타일로 텍스트를 HTML로 래핑"""
        if not text:
            return ''

        styles = []

        if self.fg_color:
            styles.append(f'color: {self.fg_color}')

        if self.bg_color:
            styles.append(f'background-color: {self.bg_color}')

        if self.bold:
            styles.append('font-weight: bold')

        if self.italic:
            styles.append('font-style: italic')

        if self.underline:
            styles.append('text-decoration: underline')

        if styles:
            style_str = '; '.join(styles)
            # HTML 특수문자 이스케이프
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<span style="{style_str}">{text}</span>'
        else:
            # 스타일이 없으면 그냥 텍스트
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return text


# 편의 함수
_global_parser = AnsiParser()


def ansi_to_html(text):
    """
    ANSI 텍스트를 HTML로 변환 (전역 파서 사용)

    Args:
        text: ANSI 이스케이프 시퀀스가 포함된 텍스트

    Returns:
        HTML 형식의 텍스트
    """
    global _global_parser
    _global_parser.reset_style()
    return _global_parser.parse_to_html(text)


def strip_ansi(text):
    """
    ANSI 이스케이프 시퀀스 제거

    Args:
        text: ANSI 이스케이프 시퀀스가 포함된 텍스트

    Returns:
        순수 텍스트
    """
    ansi_pattern = re.compile(r'\x1b\[[0-9;]+m')
    return ansi_pattern.sub('', text)


# ANSI 색상 코드 생성 헬퍼
class AnsiColor:
    """ANSI 색상 코드 생성"""

    # Reset
    RESET = '\x1b[0m'

    # 스타일
    BOLD = '\x1b[1m'
    ITALIC = '\x1b[3m'
    UNDERLINE = '\x1b[4m'

    # 전경색 (일반)
    BLACK = '\x1b[30m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    WHITE = '\x1b[37m'

    # 전경색 (밝음)
    BRIGHT_BLACK = '\x1b[90m'
    BRIGHT_RED = '\x1b[91m'
    BRIGHT_GREEN = '\x1b[92m'
    BRIGHT_YELLOW = '\x1b[93m'
    BRIGHT_BLUE = '\x1b[94m'
    BRIGHT_MAGENTA = '\x1b[95m'
    BRIGHT_CYAN = '\x1b[96m'
    BRIGHT_WHITE = '\x1b[97m'

    # 배경색
    BG_BLACK = '\x1b[40m'
    BG_RED = '\x1b[41m'
    BG_GREEN = '\x1b[42m'
    BG_YELLOW = '\x1b[43m'
    BG_BLUE = '\x1b[44m'
    BG_MAGENTA = '\x1b[45m'
    BG_CYAN = '\x1b[46m'
    BG_WHITE = '\x1b[47m'

    @staticmethod
    def colorize(text, *codes):
        """
        텍스트에 ANSI 색상 코드 적용

        Args:
            text: 텍스트
            *codes: ANSI 코드들 (예: AnsiColor.RED, AnsiColor.BOLD)

        Returns:
            ANSI 코드가 적용된 텍스트
        """
        return ''.join(codes) + text + AnsiColor.RESET


if __name__ == '__main__':
    # 테스트
    test_texts = [
        '\x1b[31mRed text\x1b[0m',
        '\x1b[1;32mBold Green\x1b[0m',
        '\x1b[4;34mUnderline Blue\x1b[0m',
        '\x1b[93mBright Yellow\x1b[0m',
        '\x1b[41;97mWhite on Red\x1b[0m',
        AnsiColor.colorize('Red and Bold', AnsiColor.RED, AnsiColor.BOLD),
        f'{AnsiColor.GREEN}Green{AnsiColor.RESET} Normal {AnsiColor.BLUE}Blue{AnsiColor.RESET}',
    ]

    parser = AnsiParser()

    print("=== ANSI to HTML Conversion Test ===\n")

    for text in test_texts:
        html = parser.parse_to_html(text)
        plain = strip_ansi(text)
        print(f"Original: {repr(text)}")
        print(f"HTML:     {html}")
        print(f"Plain:    {plain}")
        print()
