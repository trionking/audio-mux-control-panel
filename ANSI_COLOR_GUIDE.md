# ANSI 색상 코드 사용 가이드

**작성일**: 2025-10-26
**대상**: 펌웨어 개발자 & PC 프로그램 사용자

---

## 📋 목차
1. [개요](#1-개요)
2. [펌웨어 사용 방법](#2-펌웨어-사용-방법)
3. [PC 프로그램 지원](#3-pc-프로그램-지원)
4. [색상 코드 참조](#4-색상-코드-참조)
5. [예제](#5-예제)

---

## 1. 개요

### 1.1 ANSI 이스케이프 시퀀스란?

ANSI 이스케이프 시퀀스는 터미널에서 텍스트 색상, 스타일, 커서 위치 등을 제어하는 표준 방법입니다.

**형식**: `\x1b[<CODE>m`

예:
- `\x1b[31m` - 빨간색 텍스트
- `\x1b[1m` - 굵은 텍스트
- `\x1b[0m` - 스타일 리셋

### 1.2 왜 사용하나요?

- ✅ **가독성 향상**: 중요한 메시지 강조
- ✅ **상태 구분**: 성공/실패/경고를 색상으로 표시
- ✅ **디버깅 편의**: 로그 분석 시 중요 정보 빠르게 파악
- ✅ **표준 기술**: 대부분의 터미널/콘솔 지원

---

## 2. 펌웨어 사용 방법

### 2.1 헤더 파일 포함

```c
#include "ansi_colors.h"
```

### 2.2 기본 사용법

#### 단순 색상
```c
// OK 메시지 (녹색)
uart_send_response(ANSI_GREEN "OK" ANSI_RESET "\r\n");

// 에러 메시지 (빨간색)
uart_send_response(ANSI_RED "ERROR" ANSI_RESET "\r\n");

// 경고 메시지 (노란색)
uart_send_response(ANSI_YELLOW "WARNING" ANSI_RESET "\r\n");
```

#### 조합 사용
```c
// 굵은 녹색
uart_send_response(ANSI_BOLD ANSI_GREEN "Playing" ANSI_RESET "\r\n");

// 밑줄 파란색
uart_send_response(ANSI_UNDERLINE ANSI_BLUE "Channel 0" ANSI_RESET "\r\n");

// 흰색 텍스트, 빨간색 배경
uart_send_response(ANSI_WHITE ANSI_BG_RED "CRITICAL" ANSI_RESET "\r\n");
```

#### 편의 매크로
```c
// 미리 정의된 매크로 사용
uart_send_response(ANSI_OK "\r\n");          // OK (녹색)
uart_send_response(ANSI_ERROR "\r\n");       // ERROR (빨간색)
uart_send_response(ANSI_WARNING "\r\n");     // WARNING (노란색)
uart_send_response(ANSI_INFO "\r\n");        // INFO (청록색)
```

### 2.3 command_handler.c 수정 예제

#### HELLO 명령
```c
void execute_command(UartCommand_t *cmd)
{
    if (strcmp(cmd->command, "HELLO") == 0) {
        uart_send_response(ANSI_BOLD ANSI_CYAN
                          "OK AUDIO_MUX v1.00 STM32H723"
                          ANSI_RESET "\r\n");
    }
}
```

#### STATUS 명령
```c
else if (strcmp(cmd->command, "STATUS") == 0) {
    uart_send_response(ANSI_BOLD "OK STATUS" ANSI_RESET "\r\n");

    for (int i = 0; i < 6; i++) {
        if (channels[i].is_playing) {
            uart_send_response("CH%d: " ANSI_GREEN "PLAYING" ANSI_RESET
                              " %s\r\n", i, channels[i].filename);
        } else {
            uart_send_response("CH%d: " ANSI_BRIGHT_BLACK "IDLE" ANSI_RESET "\r\n", i);
        }
    }
}
```

#### PLAY 명령
```c
else if (strcmp(cmd->command, "PLAY") == 0) {
    // ... 인수 확인 ...

    if (audio_load_file(channel, path, 0) == 0) {
        audio_play(channel);
        uart_send_response(ANSI_GREEN "OK" ANSI_RESET
                          " Playing ch%d: " ANSI_CYAN "%s" ANSI_RESET "\r\n",
                          channel, path);
    } else {
        uart_send_response(ANSI_RED "ERR 404" ANSI_RESET
                          " File not found\r\n");
    }
}
```

#### Y-MODEM 진행률
```c
// ymodem.c에서 진행률 출력
void ymodem_receive(...)
{
    // ...

    // 진행률 (10%, 20%, ...)
    if (packet_number % 10 == 0) {
        int progress = (packet_number * 100) / total_packets;
        uart_send_response(ANSI_CYAN "INFO:" ANSI_RESET
                          " Receiving... %d%%\r\n", progress);
    }

    // 완료
    uart_send_response(ANSI_GREEN "INFO:" ANSI_RESET
                      " Transfer complete (%lu bytes)\r\n", total_bytes);
}
```

### 2.4 주의사항

1. **항상 RESET 사용**: 색상 코드 후에는 반드시 `ANSI_RESET`
2. **문자열 연결**: C 문자열 연결 사용 (인접한 문자열은 자동 연결)
3. **메모리 사용**: ANSI 코드는 추가 바이트 (약 4~8 bytes/color)

---

## 3. PC 프로그램 지원

### 3.1 자동 변환

PC GUI 프로그램은 ANSI 이스케이프 시퀀스를 **자동으로 HTML로 변환**하여 표시합니다.

```
펌웨어 출력: \x1b[31mERROR\x1b[0m
        ↓
PC 화면 표시: ERROR (빨간색으로 표시됨)
```

### 3.2 지원 기능

- ✅ 전경색 (16색)
- ✅ 배경색 (16색)
- ✅ 굵기 (Bold)
- ✅ 밑줄 (Underline)
- ✅ 기울임 (Italic)
- ✅ 스타일 조합

### 3.3 사용 방법

PC 프로그램을 실행하고 Main Board와 연결하면 자동으로 색상이 표시됩니다.

**특별한 설정 불필요!**

---

## 4. 색상 코드 참조

### 4.1 스타일

| 매크로 | 코드 | 효과 |
|--------|------|------|
| `ANSI_RESET` | `\x1b[0m` | 모든 스타일 리셋 |
| `ANSI_BOLD` | `\x1b[1m` | 굵게 |
| `ANSI_ITALIC` | `\x1b[3m` | 기울임 |
| `ANSI_UNDERLINE` | `\x1b[4m` | 밑줄 |

### 4.2 일반 전경색

| 매크로 | 코드 | 색상 | 용도 예시 |
|--------|------|------|-----------|
| `ANSI_BLACK` | `\x1b[30m` | 검은색 | - |
| `ANSI_RED` | `\x1b[31m` | 빨간색 | 에러, 실패 |
| `ANSI_GREEN` | `\x1b[32m` | 녹색 | 성공, OK |
| `ANSI_YELLOW` | `\x1b[33m` | 노란색 | 경고, 주의 |
| `ANSI_BLUE` | `\x1b[34m` | 파란색 | 정보 |
| `ANSI_MAGENTA` | `\x1b[35m` | 자홍색 | 중요 |
| `ANSI_CYAN` | `\x1b[36m` | 청록색 | 상태, 진행 |
| `ANSI_WHITE` | `\x1b[37m` | 흰색 | 일반 |

### 4.3 밝은 전경색

| 매크로 | 코드 | 색상 |
|--------|------|------|
| `ANSI_BRIGHT_BLACK` | `\x1b[90m` | 회색 |
| `ANSI_BRIGHT_RED` | `\x1b[91m` | 밝은 빨강 |
| `ANSI_BRIGHT_GREEN` | `\x1b[92m` | 밝은 녹색 |
| `ANSI_BRIGHT_YELLOW` | `\x1b[93m` | 밝은 노랑 |
| `ANSI_BRIGHT_BLUE` | `\x1b[94m` | 밝은 파랑 |
| `ANSI_BRIGHT_MAGENTA` | `\x1b[95m` | 밝은 자홍 |
| `ANSI_BRIGHT_CYAN` | `\x1b[96m` | 밝은 청록 |
| `ANSI_BRIGHT_WHITE` | `\x1b[97m` | 밝은 흰색 |

### 4.4 배경색

| 매크로 | 코드 | 색상 |
|--------|------|------|
| `ANSI_BG_BLACK` | `\x1b[40m` | 검은색 배경 |
| `ANSI_BG_RED` | `\x1b[41m` | 빨간색 배경 |
| `ANSI_BG_GREEN` | `\x1b[42m` | 녹색 배경 |
| `ANSI_BG_YELLOW` | `\x1b[43m` | 노란색 배경 |
| `ANSI_BG_BLUE` | `\x1b[44m` | 파란색 배경 |
| `ANSI_BG_MAGENTA` | `\x1b[45m` | 자홍색 배경 |
| `ANSI_BG_CYAN` | `\x1b[46m` | 청록색 배경 |
| `ANSI_BG_WHITE` | `\x1b[47m` | 흰색 배경 |

---

## 5. 예제

### 5.1 상태 메시지

```c
// 시스템 준비
uart_send_response("System: " ANSI_GREEN "READY" ANSI_RESET "\r\n");

// SD 카드 마운트
uart_send_response("SD Card: " ANSI_CYAN "Mounted" ANSI_RESET
                  " (%lu MB free)\r\n", free_mb);

// 채널 상태
uart_send_response("CH0: " ANSI_BOLD ANSI_GREEN "PLAYING" ANSI_RESET
                  " - test.wav\r\n");

uart_send_response("CH1: " ANSI_BRIGHT_BLACK "IDLE" ANSI_RESET "\r\n");
```

**출력 예시**:
```
System: READY (녹색)
SD Card: Mounted (청록색) (15234 MB free)
CH0: PLAYING (굵은 녹색) - test.wav
CH1: IDLE (회색)
```

### 5.2 에러 메시지

```c
// 파일 없음
uart_send_response(ANSI_RED "ERR 404" ANSI_RESET
                  " File not found: %s\r\n", path);

// 채널 오류
uart_send_response(ANSI_RED "ERR 402" ANSI_RESET
                  " Invalid channel: %d "
                  ANSI_BRIGHT_BLACK "(must be 0~5)" ANSI_RESET "\r\n",
                  channel);

// SD 카드 에러
uart_send_response(ANSI_BG_RED ANSI_WHITE " CRITICAL " ANSI_RESET
                  " SD card error\r\n");
```

**출력 예시**:
```
ERR 404 (빨간색) File not found: /audio/missing.wav
ERR 402 (빨간색) Invalid channel: 7 (must be 0~5) (회색)
 CRITICAL (흰색 텍스트, 빨간색 배경) SD card error
```

### 5.3 진행 상황

```c
// 파일 로딩
uart_send_response(ANSI_CYAN "Loading..." ANSI_RESET "\r\n");

// 진행률
uart_send_response(ANSI_CYAN "Progress: " ANSI_RESET
                  "%d%% "
                  ANSI_BRIGHT_BLACK "(%d/%d)" ANSI_RESET "\r\n",
                  percent, current, total);

// 완료
uart_send_response(ANSI_BOLD ANSI_GREEN "✓ Complete" ANSI_RESET "\r\n");
```

**출력 예시**:
```
Loading... (청록색)
Progress: 50% (1024/2048) (회색)
✓ Complete (굵은 녹색)
```

### 5.4 파일 목록

```c
// LS 명령 응답
uart_send_response(ANSI_BOLD "OK LS /audio" ANSI_RESET "\r\n");

DIR dir;
FILINFO fno;
f_opendir(&dir, "/audio");

while (f_readdir(&dir, &fno) == FR_OK && fno.fname[0]) {
    if (fno.fattrib & AM_DIR) {
        // 디렉토리 (파란색)
        uart_send_response(ANSI_BLUE "[DIR]" ANSI_RESET " %s\r\n", fno.fname);
    } else {
        // 파일 (기본색)
        uart_send_response("      %s "
                          ANSI_BRIGHT_BLACK "(%lu KB)" ANSI_RESET "\r\n",
                          fno.fname, fno.fsize / 1024);
    }
}

f_closedir(&dir);
uart_send_response(ANSI_BRIGHT_BLACK "END" ANSI_RESET "\r\n");
```

**출력 예시**:
```
OK LS /audio (굵게)
[DIR] (파란색) ch0
[DIR] (파란색) ch1
      test.wav (1024 KB) (회색)
END (회색)
```

---

## 6. 테스트 방법

### 6.1 Python 테스트 스크립트

```bash
cd audio_win_app
python test_ansi.py
```

이 스크립트는:
- ANSI 색상 코드 예제 출력
- HTML 변환 테스트
- 펌웨어용 C 코드 생성

### 6.2 PC 프로그램에서 확인

1. PC 프로그램 실행
2. Main Board 연결
3. 명령 전송 및 응답 확인
4. 로그 창에서 색상 확인

---

## 7. 권장 사용 가이드

### 7.1 색상 선택

| 용도 | 색상 | 매크로 |
|------|------|--------|
| 성공, OK | 녹색 | `ANSI_GREEN` |
| 에러, 실패 | 빨간색 | `ANSI_RED` |
| 경고 | 노란색 | `ANSI_YELLOW` |
| 정보, 상태 | 청록색 | `ANSI_CYAN` |
| 중요 | 굵게 | `ANSI_BOLD` |
| 비활성 | 회색 | `ANSI_BRIGHT_BLACK` |

### 7.2 Best Practices

1. **일관성**: 같은 상태는 같은 색상
2. **가독성**: 너무 많은 색상 사용 자제
3. **대비**: 배경색 사용 시 전경색 고려
4. **리셋**: 항상 `ANSI_RESET`으로 종료

### 7.3 나쁜 예시

```c
// ❌ 너무 많은 색상
uart_send_response(ANSI_RED "This " ANSI_GREEN "is "
                  ANSI_BLUE "too " ANSI_YELLOW "colorful" ANSI_RESET "\r\n");

// ❌ 리셋 없음
uart_send_response(ANSI_RED "Error\r\n");  // 다음 출력도 빨간색!

// ❌ 읽기 어려움
uart_send_response(ANSI_YELLOW ANSI_BG_YELLOW "Can't read" ANSI_RESET "\r\n");
```

### 7.4 좋은 예시

```c
// ✅ 명확한 상태 표시
uart_send_response(ANSI_GREEN "OK" ANSI_RESET " Command executed\r\n");

// ✅ 중요한 부분만 강조
uart_send_response("Playing: " ANSI_CYAN "%s" ANSI_RESET "\r\n", filename);

// ✅ 적절한 리셋
uart_send_response(ANSI_RED "ERROR" ANSI_RESET ": File not found\r\n");
```

---

## 8. 참고 자료

- ANSI 이스케이프 시퀀스: https://en.wikipedia.org/wiki/ANSI_escape_code
- 터미널 색상 가이드: https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797

---

**문서 버전**: 1.0
**최종 수정일**: 2025-10-26
**작성자**: System Integration Team
