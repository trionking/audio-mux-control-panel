"""
audio_converter.py

오디오 파일 변환 모듈
다양한 형식 → 32kHz 16-bit Mono WAV
FFmpeg를 subprocess로 직접 호출 (Python 3.13 호환)
"""

import os
import subprocess
import shutil
import json


class AudioConverter:
    """오디오 변환기"""

    SAMPLE_RATE = 32000
    SAMPLE_WIDTH = 2  # 16-bit
    CHANNELS = 1  # Mono

    @staticmethod
    def convert(input_path, output_path):
        """
        오디오 파일을 32kHz 16-bit Mono WAV로 변환

        Args:
            input_path: 입력 파일 경로 (MP3, WAV, FLAC, etc.)
            output_path: 출력 WAV 파일 경로

        Returns:
            (success, message): 성공 여부 및 메시지

        """
        try:
            # 입력 파일 확인
            if not os.path.exists(input_path):
                return False, "Input file not found"

            # FFmpeg 확인
            if not check_ffmpeg_installed():
                return False, ("FFmpeg not found. Please install FFmpeg and add to PATH.\n"
                             "Download: https://ffmpeg.org/download.html")

            # 원본 파일 정보 가져오기
            orig_info = AudioConverter.get_audio_info(input_path)

            # FFmpeg 경로 찾기
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                # PATH에 없으면 일반적인 설치 위치 확인
                common_paths = [
                    r"C:\ffmpeg\bin\ffmpeg.exe",
                    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ffmpeg_path = path
                        break

            if not ffmpeg_path:
                return False, ("FFmpeg not found. Please install FFmpeg and add to PATH.\n"
                             "Download: https://ffmpeg.org/download.html")

            # FFmpeg 명령어 구성
            # -i: 입력 파일
            # -ar: 샘플레이트 (32000Hz)
            # -ac: 채널 수 (1 = Mono)
            # -sample_fmt: 샘플 형식 (s16 = 16-bit signed)
            # -y: 기존 파일 덮어쓰기
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-ar', str(AudioConverter.SAMPLE_RATE),
                '-ac', str(AudioConverter.CHANNELS),
                '-sample_fmt', 's16',
                '-y',
                output_path
            ]

            # FFmpeg 실행
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                return False, f"FFmpeg error: {error_msg[:200]}"

            # 변환 정보
            if orig_info:
                message = (f"Converted successfully\n"
                          f"Original: {orig_info.get('sample_rate', 'unknown')}Hz, "
                          f"{orig_info.get('channels', 'unknown')}ch, "
                          f"{orig_info.get('bit_depth', 'unknown')}bit\n"
                          f"Output: {AudioConverter.SAMPLE_RATE}Hz, "
                          f"{AudioConverter.CHANNELS}ch, {AudioConverter.SAMPLE_WIDTH*8}bit")
            else:
                message = "Converted successfully"

            return True, message

        except FileNotFoundError:
            return False, ("FFmpeg not found. Please install FFmpeg and add to PATH.\n"
                         "Download: https://ffmpeg.org/download.html")

        except Exception as e:
            return False, f"Conversion error: {str(e)}"

    @staticmethod
    def get_audio_info(file_path):
        """
        오디오 파일 정보 조회 (ffprobe 사용)

        Args:
            file_path: 오디오 파일 경로

        Returns:
            dict: 오디오 정보 (sample_rate, channels, bit_depth, duration 등)
        """
        try:
            # ffprobe 경로 찾기
            ffprobe_path = shutil.which("ffprobe")
            if not ffprobe_path:
                # PATH에 없으면 일반적인 설치 위치 확인
                common_paths = [
                    r"C:\ffmpeg\bin\ffprobe.exe",
                    r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ffprobe_path = path
                        break

            if not ffprobe_path:
                return None

            # ffprobe 명령어
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if result.returncode != 0:
                return None

            # JSON 파싱
            data = json.loads(result.stdout.decode('utf-8'))

            # 오디오 스트림 찾기
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break

            if not audio_stream:
                return None

            # 샘플 폭 계산 (비트 깊이)
            bits_per_sample = audio_stream.get('bits_per_sample',
                                              audio_stream.get('bits_per_raw_sample', 16))

            return {
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bit_depth': bits_per_sample,
                'sample_width': bits_per_sample // 8,
                'duration_sec': float(audio_stream.get('duration', 0)),
                'format': os.path.splitext(file_path)[1].upper()
            }

        except Exception as e:
            return None

    @staticmethod
    def is_conversion_needed(file_path):
        """
        변환이 필요한지 확인

        Args:
            file_path: 오디오 파일 경로

        Returns:
            bool: 변환 필요 여부
        """
        info = AudioConverter.get_audio_info(file_path)

        if not info:
            return True  # 정보를 가져올 수 없으면 변환 필요

        # 이미 올바른 형식인지 확인
        if (info['sample_rate'] == AudioConverter.SAMPLE_RATE and
            info['channels'] == AudioConverter.CHANNELS and
            info['sample_width'] == AudioConverter.SAMPLE_WIDTH and
            info['format'] == '.WAV'):
            return False  # 변환 불필요

        return True  # 변환 필요


def check_ffmpeg_installed():
    """FFmpeg 설치 여부 확인"""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return True

    # PATH에 없으면 일반적인 설치 위치 확인
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return True

    return False
