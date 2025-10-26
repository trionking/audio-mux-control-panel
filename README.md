# Audio Mux Control Panel

Audio Mux 시스템을 제어하기 위한 PC용 GUI 프로그램

## 기능

- **시리얼 통신**: STM32H723 Main Board와 UART 통신
- **파일 전송**: Y-MODEM 프로토콜로 WAV 파일 업로드
- **오디오 변환**: 다양한 형식 → 32kHz 16-bit Mono WAV 변환
- **로그 출력**: 실시간 통신 로그 모니터링
- **ANSI 색상**: 펌웨어에서 전송하는 ANSI 색상 코드 자동 표시

## 시스템 요구사항

- Windows 10/11
- Python 3.8 이상
- FFmpeg (오디오 변환용)

## 설치 방법

### 1. Python 설치
Python 3.8 이상 설치
- https://www.python.org/downloads/

### 2. FFmpeg 설치 (필수)

FFmpeg은 오디오 변환에 필요합니다.

**방법 1: 수동 설치**
1. https://ffmpeg.org/download.html 에서 다운로드
2. 압축 해제 후 bin 폴더의 경로를 환경 변수 PATH에 추가

**방법 2: Chocolatey 사용 (권장)**
```powershell
choco install ffmpeg
```

**설치 확인**:
```cmd
ffmpeg -version
```

### 3. Python 패키지 설치

프로젝트 폴더에서:
```cmd
cd audio_win_app
pip install -r requirements.txt
```

## 사용 방법

### 1. 프로그램 실행

```cmd
python main.py
```

### 2. Main Board 연결

1. USB-UART 어댑터로 Main Board의 UART2 연결
   - UART2_TX (PD5) → RX
   - UART2_RX (PD6) → TX
   - GND → GND

2. 프로그램에서:
   - Port 선택 (예: COM3)
   - **Refresh** 버튼으로 포트 새로고침
   - **Connect** 버튼 클릭

3. 연결 확인:
   - Status가 "Connected"로 변경
   - 로그에 "OK AUDIO_MUX v1.00" 응답 출력

### 3. 파일 업로드

**방법 1: 자동 변환 사용 (권장)**
1. **Browse** 버튼으로 파일 선택 (MP3, WAV 등)
2. **Auto-convert to 32kHz 16-bit Mono** 체크박스 확인
3. Channel 선택 (0~5)
4. **Upload (Y-MODEM)** 버튼 클릭
5. 전송 진행률 확인

**방법 2: 미리 변환**
1. Audio Converter 섹션에서:
   - Input 파일 선택
   - Output 파일명 입력
   - **Convert to WAV** 버튼 클릭
2. 변환된 파일을 File Upload 섹션에서 업로드

### 4. 로그 확인

- Communication Log 창에서 모든 통신 내용 확인
- **Clear Log** 버튼으로 로그 클리어
- **ANSI 색상 자동 지원**: 펌웨어가 ANSI 색상 코드를 사용하면 자동으로 색상 표시

### 5. ANSI 색상 코드 (펌웨어용)

펌웨어에서 ANSI 색상 코드를 사용하면 PC 로그에 자동으로 색상이 표시됩니다.

**펌웨어 예제**:
```c
#include "ansi_colors.h"

// 성공 메시지 (녹색)
uart_send_response(ANSI_GREEN "OK" ANSI_RESET " Command executed\r\n");

// 에러 메시지 (빨간색)
uart_send_response(ANSI_RED "ERROR" ANSI_RESET " File not found\r\n");

// 상태 메시지 (청록색)
uart_send_response("Status: " ANSI_CYAN "PLAYING" ANSI_RESET "\r\n");
```

**PC 화면**: OK, ERROR, PLAYING이 각각 녹색, 빨간색, 청록색으로 표시됩니다.

자세한 내용은 `ANSI_COLOR_GUIDE.md` 참조

## 파일 구조

```
audio_win_app/
├── main.py              # 메인 애플리케이션
├── mainwindow.ui        # Qt Designer UI 파일
├── serial_comm.py       # 시리얼 통신 모듈
├── ymodem.py            # Y-MODEM 프로토콜
├── audio_converter.py   # 오디오 변환 모듈
├── ansi_parser.py       # ANSI 이스케이프 시퀀스 파서
├── test_ansi.py         # ANSI 색상 테스트 스크립트
├── requirements.txt     # Python 패키지 목록
└── README.md            # 이 파일
```

## UI 수정 방법

### Qt Designer 사용

1. Qt Designer 설치:
```cmd
pip install pyqt5-tools
```

2. UI 파일 열기:
```cmd
designer mainwindow.ui
```

3. UI 수정 후 저장

4. 프로그램 재시작 (자동 반영)

## 지원하는 오디오 형식

### 입력 (변환 가능)
- MP3
- WAV (모든 샘플레이트/비트)
- FLAC
- OGG
- M4A / AAC
- 기타 (FFmpeg 지원 형식)

### 출력
- WAV: 32000Hz, 16-bit, Mono

## 트러블슈팅

### FFmpeg not found 에러

**증상**: 오디오 변환 시 "FFmpeg not found" 에러

**해결**:
1. FFmpeg 설치 확인:
   ```cmd
   ffmpeg -version
   ```

2. 환경 변수 PATH에 ffmpeg.exe 경로 추가

3. 프로그램 재시작

### 포트가 안 보임

**증상**: Port 드롭다운이 비어있음

**해결**:
1. USB-UART 드라이버 설치 확인
2. 장치 관리자에서 포트 확인
3. **Refresh** 버튼 클릭

### 연결 실패

**증상**: Connect 버튼 클릭 시 에러

**해결**:
1. 포트가 다른 프로그램에서 사용 중인지 확인
2. Main Board 전원 확인
3. UART 핀 연결 확인 (TX↔RX 교차)

### Y-MODEM 전송 실패

**증상**: 파일 전송 중 타임아웃

**해결**:
1. Main Board 펌웨어에 Y-MODEM 수신 기능 구현 확인
2. UPLOAD 명령 후 "OK Ready for Y-MODEM" 응답 확인
3. 보드레이트 일치 확인 (115200)

## UART 명령어 참고

프로그램에서 사용하는 주요 명령어:

```
HELLO                      # 연결 확인
STATUS                     # 상태 조회
PLAY <CH> <PATH>          # 재생
STOP <CH>                 # 정지
VOLUME <CH> <LEVEL>       # 볼륨 설정
UPLOAD <CH> <FILE>        # 파일 업로드
LS [PATH]                 # 파일 목록
```

자세한 내용은 `PC_UART_PROTOCOL.md` 참조

## 개발자 정보

### 의존성 업데이트

```cmd
pip install --upgrade -r requirements.txt
```

### 코드 구조

- **main.py**: PyQt5 메인 윈도우 및 이벤트 처리
- **serial_comm.py**: 시리얼 통신 스레드 (QThread)
- **ymodem.py**: Y-MODEM 프로토콜 구현 (QThread)
- **audio_converter.py**: pydub 기반 오디오 변환

### 새 명령 추가

1. Main Board 펌웨어에 명령 추가
2. `PC_UART_PROTOCOL.md`에 문서화
3. UI에 버튼/입력 추가 (mainwindow.ui)
4. `main.py`에 핸들러 추가

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 문의

기술 지원이 필요하면 펌웨어 팀에 문의하세요.

---

**버전**: 1.0
**최종 업데이트**: 2025-10-26
