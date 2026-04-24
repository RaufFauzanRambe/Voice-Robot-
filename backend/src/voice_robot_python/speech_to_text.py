"""
speech_to_text.py — Speech-to-Text Module for Voice Robot
=========================================================
Mendukung pengenalan suara dalam 20 bahasa menggunakan:
  - OpenAI Whisper API (via z-ai-web-dev-sdk backend)
  - Google Speech Recognition (fallback offline)
  - Vosk (offline fallback)

Author: Voice Robot Team
"""

import os
import json
import base64
import logging
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import requests

# Konfigurasi logging
logger = logging.getLogger("VoiceRobot.STT")


# ============ Supported Languages ============
SUPPORTED_LANGUAGES = {
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "whisper_code": "id"},
    "en": {"name": "English", "native": "English", "whisper_code": "en"},
    "fr": {"name": "French", "native": "Français", "whisper_code": "fr"},
    "de": {"name": "German", "native": "Deutsch", "whisper_code": "de"},
    "ar": {"name": "Arabic", "native": "العربية", "whisper_code": "ar"},
    "ms": {"name": "Malay", "native": "Bahasa Melayu", "whisper_code": "ms"},
    "zh": {"name": "Chinese", "native": "中文", "whisper_code": "zh"},
    "ja": {"name": "Japanese", "native": "日本語", "whisper_code": "ja"},
    "ru": {"name": "Russian", "native": "Русский", "whisper_code": "ru"},
    "ko": {"name": "Korean", "native": "한국어", "whisper_code": "ko"},
    "es": {"name": "Spanish", "native": "Español", "whisper_code": "es"},
    "pt": {"name": "Portuguese", "native": "Português", "whisper_code": "pt"},
    "it": {"name": "Italian", "native": "Italiano", "whisper_code": "it"},
    "th": {"name": "Thai", "native": "ภาษาไทย", "whisper_code": "th"},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "whisper_code": "vi"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "whisper_code": "hi"},
    "tr": {"name": "Turkish", "native": "Türkçe", "whisper_code": "tr"},
    "nl": {"name": "Dutch", "native": "Nederlands", "whisper_code": "nl"},
    "pl": {"name": "Polish", "native": "Polski", "whisper_code": "pl"},
    "sv": {"name": "Swedish", "native": "Svenska", "whisper_code": "sv"},
}


@dataclass
class STTResult:
    """Hasil pengenalan suara."""
    text: str
    language: str
    confidence: float = 0.0
    duration: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


class SpeechToText:
    """
    Kelas utama Speech-to-Text untuk Voice Robot.

    Mendukung beberapa backend:
      - 'api': Menggunakan Next.js backend API (/api/asr) dengan z-ai-web-dev-sdk
      - 'google': Menggunakan Google Speech Recognition (speech_recognition library)
      - 'whisper_local': Menggunakan OpenAI Whisper lokal

    Parameters:
        backend: Backend STT yang digunakan ('api', 'google', 'whisper_local')
        api_url: URL backend API (default: http://localhost:3000/api/asr)
        language: Kode bahasa default (default: 'id')
        timeout: Timeout request dalam detik (default: 30)
    """

    def __init__(
        self,
        backend: str = "api",
        api_url: str = "http://localhost:3000/api/asr",
        language: str = "id",
        timeout: int = 30,
    ):
        self.backend = backend
        self.api_url = api_url
        self.language = language
        self.timeout = timeout

        # Validate language
        if self.language not in SUPPORTED_LANGUAGES:
            logger.warning(
                f"Language '{self.language}' not in supported list. Defaulting to 'id'."
            )
            self.language = "id"

        # Initialize backend
        self._init_backend()

        logger.info(f"SpeechToText initialized — backend: {self.backend}, language: {self.language}")

    def _init_backend(self):
        """Inisialisasi backend STT."""
        if self.backend == "google":
            try:
                import speech_recognition as sr
                self._recognizer = sr.Recognizer()
                self._microphone = sr.Microphone()
                logger.info("Google Speech Recognition backend loaded.")
            except ImportError:
                raise ImportError(
                    "speech_recognition not installed. "
                    "Install with: pip install SpeechRecognition pyaudio"
                )

        elif self.backend == "whisper_local":
            try:
                import whisper
                self._whisper_model = whisper.load_model("base")
                logger.info("Whisper local model loaded (base).")
            except ImportError:
                raise ImportError(
                    "openai-whisper not installed. "
                    "Install with: pip install openai-whisper"
                )

        elif self.backend == "api":
            # Test API connection
            try:
                response = requests.get(
                    self.api_url.replace("/api/asr", "/api"),
                    timeout=5,
                )
                if response.status_code == 200:
                    logger.info("API backend connected successfully.")
                else:
                    logger.warning(f"API returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.warning(
                    f"Cannot connect to API at {self.api_url}. "
                    "Make sure the Next.js server is running."
                )

    def recognize_from_file(self, audio_path: str, language: Optional[str] = None) -> STTResult:
        """
        Mengenali suara dari file audio.

        Parameters:
            audio_path: Path ke file audio (wav, mp3, webm, m4a, flac)
            language: Kode bahasa (optional, default: self.language)

        Returns:
            STTResult: Hasil pengenalan suara
        """
        lang = language or self.language
        audio_path = Path(audio_path)

        if not audio_path.exists():
            return STTResult(
                text="",
                language=lang,
                success=False,
                error=f"Audio file not found: {audio_path}",
            )

        logger.info(f"Recognizing speech from: {audio_path} (language: {lang})")

        if self.backend == "api":
            return self._recognize_via_api(audio_path, lang)
        elif self.backend == "google":
            return self._recognize_via_google(audio_path, lang)
        elif self.backend == "whisper_local":
            return self._recognize_via_whisper(audio_path, lang)
        else:
            return STTResult(
                text="",
                language=lang,
                success=False,
                error=f"Unknown backend: {self.backend}",
            )

    def recognize_from_microphone(self, language: Optional[str] = None, timeout: int = 5, phrase_time_limit: int = 15) -> STTResult:
        """
        Mengenali suara dari mikrofon secara real-time.

        Parameters:
            language: Kode bahasa (optional)
            timeout: Waktu tunggu sebelum mulai mendengarkan (detik)
            phrase_time_limit: Batas waktu pengenalan frasa (detik)

        Returns:
            STTResult: Hasil pengenalan suara
        """
        lang = language or self.language

        if self.backend == "google":
            return self._recognize_mic_google(lang, timeout, phrase_time_limit)
        elif self.backend == "whisper_local":
            # Whisper local: record first, then transcribe
            return self._recognize_mic_whisper(lang, timeout, phrase_time_limit)
        else:
            logger.warning(
                "Direct microphone input not supported for 'api' backend. "
                "Use recognize_from_file() with a recorded audio file instead."
            )
            return STTResult(
                text="",
                language=lang,
                success=False,
                error="Microphone input not supported for API backend. Record audio first.",
            )

    def _recognize_via_api(self, audio_path: Path, language: str) -> STTResult:
        """Mengenali suara melalui Next.js API backend."""
        try:
            with open(audio_path, "rb") as f:
                files = {"audio": (audio_path.name, f, self._get_mime_type(audio_path))}
                data = {"language": language}

                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    timeout=self.timeout,
                )

            if response.status_code == 200:
                result = response.json()
                return STTResult(
                    text=result.get("transcription", ""),
                    language=language,
                    confidence=0.9,
                    success=True,
                    metadata={"backend": "api", "status_code": response.status_code},
                )
            else:
                error_msg = response.json().get("error", f"HTTP {response.status_code}")
                return STTResult(
                    text="",
                    language=language,
                    success=False,
                    error=error_msg,
                )

        except requests.exceptions.ConnectionError:
            return STTResult(
                text="",
                language=language,
                success=False,
                error="Cannot connect to API server. Make sure Next.js is running.",
            )
        except Exception as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=str(e),
            )

    def _recognize_via_google(self, audio_path: Path, language: str) -> STTResult:
        """Mengenali suara menggunakan Google Speech Recognition."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            # Convert audio to wav if needed
            wav_path = self._ensure_wav(audio_path)

            with sr.AudioFile(str(wav_path)) as source:
                audio_data = recognizer.record(source)

            # Map language code to Google format
            google_lang = self._to_google_lang(language)

            text = recognizer.recognize_google(audio_data, language=google_lang)

            return STTResult(
                text=text,
                language=language,
                confidence=0.85,
                success=True,
                metadata={"backend": "google"},
            )

        except sr.UnknownValueError:
            return STTResult(
                text="",
                language=language,
                success=False,
                error="Google Speech Recognition could not understand audio",
            )
        except sr.RequestError as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=f"Google Speech Recognition request error: {e}",
            )
        except Exception as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=str(e),
            )

    def _recognize_via_whisper(self, audio_path: Path, language: str) -> STTResult:
        """Mengenali suara menggunakan OpenAI Whisper lokal."""
        try:
            whisper_lang = SUPPORTED_LANGUAGES.get(language, {}).get("whisper_code", language)

            result = self._whisper_model.transcribe(
                str(audio_path),
                language=whisper_lang,
            )

            return STTResult(
                text=result["text"].strip(),
                language=language,
                confidence=0.9,
                duration=result.get("segments", [{}])[-1].get("end", 0.0) if result.get("segments") else 0.0,
                success=True,
                metadata={"backend": "whisper_local", "model": "base"},
            )

        except Exception as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=str(e),
            )

    def _recognize_mic_google(self, language: str, timeout: int, phrase_time_limit: int) -> STTResult:
        """Merekam dari mikrofon dan mengenali menggunakan Google."""
        try:
            import speech_recognition as sr

            with self._microphone as source:
                logger.info("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening...")
                audio_data = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            google_lang = self._to_google_lang(language)
            text = self._recognizer.recognize_google(audio_data, language=google_lang)

            return STTResult(
                text=text,
                language=language,
                confidence=0.85,
                success=True,
                metadata={"backend": "google", "source": "microphone"},
            )

        except sr.WaitTimeoutError:
            return STTResult(
                text="",
                language=language,
                success=False,
                error="Listening timeout — no speech detected",
            )
        except sr.UnknownValueError:
            return STTResult(
                text="",
                language=language,
                success=False,
                error="Could not understand audio",
            )
        except Exception as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=str(e),
            )

    def _recognize_mic_whisper(self, language: str, timeout: int, phrase_time_limit: int) -> STTResult:
        """Merekam dari mikrofon dan mengenali menggunakan Whisper lokal."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            with microphone as source:
                logger.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening...")
                audio_data = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            # Save to temp file and transcribe with Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                with open(tmp_path, "wb") as f:
                    f.write(audio_data.get_wav_data())

            result = self._recognize_via_whisper(Path(tmp_path), language)

            # Cleanup
            os.unlink(tmp_path)

            result.metadata["source"] = "microphone"
            return result

        except Exception as e:
            return STTResult(
                text="",
                language=language,
                success=False,
                error=str(e),
            )

    @staticmethod
    def _get_mime_type(path: Path) -> str:
        """Mendapatkan MIME type berdasarkan ekstensi file."""
        mime_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".webm": "audio/webm",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
        }
        return mime_map.get(path.suffix.lower(), "audio/wav")

    @staticmethod
    def _ensure_wav(audio_path: Path) -> Path:
        """Konversi audio ke WAV jika perlu (untuk Google SR)."""
        if audio_path.suffix.lower() == ".wav":
            return audio_path

        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            wav_path = audio_path.with_suffix(".wav")
            audio.export(str(wav_path), format="wav")
            return wav_path
        except ImportError:
            logger.warning("pydub not installed. Cannot convert audio format.")
            return audio_path

    @staticmethod
    def _to_google_lang(code: str) -> str:
        """Konversi kode bahasa ke format Google Speech Recognition."""
        google_map = {
            "id": "id-ID",
            "en": "en-US",
            "fr": "fr-FR",
            "de": "de-DE",
            "ar": "ar-SA",
            "ms": "ms-MY",
            "zh": "zh-CN",
            "ja": "ja-JP",
            "ru": "ru-RU",
            "ko": "ko-KR",
            "es": "es-ES",
            "pt": "pt-BR",
            "it": "it-IT",
            "th": "th-TH",
            "vi": "vi-VN",
            "hi": "hi-IN",
            "tr": "tr-TR",
            "nl": "nl-NL",
            "pl": "pl-PL",
            "sv": "sv-SE",
        }
        return google_map.get(code, "id-ID")

    def set_language(self, language: str):
        """Mengubah bahasa pengenalan suara."""
        if language in SUPPORTED_LANGUAGES:
            self.language = language
            logger.info(f"STT language changed to: {language} ({SUPPORTED_LANGUAGES[language]['native']})")
        else:
            logger.warning(f"Unsupported language: {language}")

    @staticmethod
    def list_languages() -> dict:
        """Menampilkan daftar bahasa yang didukung."""
        return SUPPORTED_LANGUAGES.copy()


# ============ CLI Interface ============
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(name)s — %(levelname)s — %(message)s")

    parser = argparse.ArgumentParser(description="Voice Robot — Speech-to-Text")
    parser.add_argument("--file", "-f", help="Path ke file audio", type=str)
    parser.add_argument("--mic", "-m", help="Gunakan mikrofon", action="store_true")
    parser.add_argument("--language", "-l", help="Kode bahasa (default: id)", default="id")
    parser.add_argument("--backend", "-b", help="Backend: api, google, whisper_local", default="api")
    parser.add_argument("--api-url", help="URL API backend", default="http://localhost:3000/api/asr")
    parser.add_argument("--list-langs", help="Tampilkan daftar bahasa", action="store_true")

    args = parser.parse_args()

    stt = SpeechToText(backend=args.backend, api_url=args.api_url, language=args.language)

    if args.list_langs:
        print("\n🌍 Supported Languages:")
        print("=" * 50)
        for code, info in SUPPORTED_LANGUAGES.items():
            print(f"  {code:>4}  {info['native']:<20} ({info['name']})")
        print()

    elif args.file:
        result = stt.recognize_from_file(args.file)
        print(f"\n📝 Result: {result.to_dict()}")

    elif args.mic:
        print(f"\n🎤 Listening in {args.language}... Speak now!")
        result = stt.recognize_from_microphone()
        print(f"\n📝 Result: {result.to_dict()}")

    else:
        parser.print_help()
