"""
test_ansi.py

ANSI 색상 코드 테스트 스크립트
"""

from ansi_parser import AnsiColor, ansi_to_html


def test_ansi_codes():
    """ANSI 코드 테스트"""

    print("=== ANSI Color Test ===\n")

    # 기본 색상
    print("Basic Colors:")
    print(AnsiColor.colorize("Red Text", AnsiColor.RED))
    print(AnsiColor.colorize("Green Text", AnsiColor.GREEN))
    print(AnsiColor.colorize("Yellow Text", AnsiColor.YELLOW))
    print(AnsiColor.colorize("Blue Text", AnsiColor.BLUE))
    print(AnsiColor.colorize("Magenta Text", AnsiColor.MAGENTA))
    print(AnsiColor.colorize("Cyan Text", AnsiColor.CYAN))
    print()

    # 밝은 색상
    print("Bright Colors:")
    print(AnsiColor.colorize("Bright Red", AnsiColor.BRIGHT_RED))
    print(AnsiColor.colorize("Bright Green", AnsiColor.BRIGHT_GREEN))
    print(AnsiColor.colorize("Bright Yellow", AnsiColor.BRIGHT_YELLOW))
    print(AnsiColor.colorize("Bright Blue", AnsiColor.BRIGHT_BLUE))
    print()

    # 스타일
    print("Styles:")
    print(AnsiColor.colorize("Bold Text", AnsiColor.BOLD))
    print(AnsiColor.colorize("Underline Text", AnsiColor.UNDERLINE))
    print(AnsiColor.colorize("Italic Text", AnsiColor.ITALIC))
    print()

    # 조합
    print("Combinations:")
    print(AnsiColor.colorize("Bold Red", AnsiColor.BOLD, AnsiColor.RED))
    print(AnsiColor.colorize("Underline Green", AnsiColor.UNDERLINE, AnsiColor.GREEN))
    print(AnsiColor.colorize("Bold Underline Blue", AnsiColor.BOLD, AnsiColor.UNDERLINE, AnsiColor.BLUE))
    print()

    # 배경색
    print("Background Colors:")
    print(AnsiColor.colorize("White on Red", AnsiColor.WHITE, AnsiColor.BG_RED))
    print(AnsiColor.colorize("Black on Yellow", AnsiColor.BLACK, AnsiColor.BG_YELLOW))
    print(AnsiColor.colorize("White on Blue", AnsiColor.WHITE, AnsiColor.BG_BLUE))
    print()


def test_html_conversion():
    """HTML 변환 테스트"""

    print("\n=== HTML Conversion Test ===\n")

    test_cases = [
        ("\x1b[31mRed text\x1b[0m", "Simple red text"),
        ("\x1b[1;32mBold Green\x1b[0m", "Bold green"),
        ("\x1b[4;34mUnderline Blue\x1b[0m", "Underline blue"),
        ("\x1b[93mBright Yellow\x1b[0m", "Bright yellow"),
        ("\x1b[41;97mWhite on Red\x1b[0m", "White text on red background"),
        (f"{AnsiColor.GREEN}OK{AnsiColor.RESET} {AnsiColor.RED}ERR{AnsiColor.RESET}", "Mixed colors"),
    ]

    for ansi_text, description in test_cases:
        html = ansi_to_html(ansi_text)
        print(f"{description}:")
        print(f"  ANSI: {repr(ansi_text)}")
        print(f"  HTML: {html}")
        print()


def generate_firmware_examples():
    """펌웨어에서 사용할 ANSI 코드 예제 생성"""

    print("\n=== Firmware Examples (C code) ===\n")

    examples = [
        ("OK", f"{AnsiColor.GREEN}OK{AnsiColor.RESET}"),
        ("ERROR", f"{AnsiColor.RED}ERROR{AnsiColor.RESET}"),
        ("WARNING", f"{AnsiColor.YELLOW}WARNING{AnsiColor.RESET}"),
        ("INFO", f"{AnsiColor.CYAN}INFO{AnsiColor.RESET}"),
        ("Playing", f"{AnsiColor.BOLD}{AnsiColor.GREEN}Playing{AnsiColor.RESET}"),
        ("Stopped", f"{AnsiColor.BOLD}{AnsiColor.RED}Stopped{AnsiColor.RESET}"),
    ]

    print("/* ANSI 색상 코드 정의 (uart_command.h) */")
    print("#define ANSI_RESET      \"\\x1b[0m\"")
    print("#define ANSI_BOLD       \"\\x1b[1m\"")
    print("#define ANSI_RED        \"\\x1b[31m\"")
    print("#define ANSI_GREEN      \"\\x1b[32m\"")
    print("#define ANSI_YELLOW     \"\\x1b[33m\"")
    print("#define ANSI_BLUE       \"\\x1b[34m\"")
    print("#define ANSI_CYAN       \"\\x1b[36m\"")
    print()

    print("/* 사용 예제 */")
    for label, ansi_text in examples:
        c_str = ansi_text.replace('\x1b', '\\x1b')
        print(f'uart_send_response("{c_str}\\r\\n");  // {label}')
    print()

    print("/* 상태 메시지 예제 */")
    print('uart_send_response("Status: " ANSI_GREEN "READY" ANSI_RESET "\\r\\n");')
    print('uart_send_response("Error: " ANSI_RED "File not found" ANSI_RESET "\\r\\n");')
    print('uart_send_response("Upload: " ANSI_CYAN "50%%" ANSI_RESET "\\r\\n");')
    print()


if __name__ == '__main__':
    # ANSI 터미널에서 실행
    test_ansi_codes()

    # HTML 변환 테스트
    test_html_conversion()

    # 펌웨어 예제
    generate_firmware_examples()

    print("\n=== Test Complete ===")
    print("\nTo use in your firmware:")
    print("1. Add ANSI codes to uart_command.h")
    print("2. Use ANSI codes in uart_send_response()")
    print("3. PC program will automatically display colors!")
