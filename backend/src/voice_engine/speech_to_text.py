"""
Speech-to-Text Module (ASR)
=============================
Handles audio recording from microphone and transcription using
the Voice Robot ASR API endpoint.

Features:
    - Real-time microphone audio recording
    - Audio format conversion (WebM/PCM)
    - Language-aware speech recognition
    - Noise level detection before recording
    - Support for 20 languages

Classes:
    SpeechToText - Main ASR handler

Usage:
    stt = SpeechToText(api_url="http://localhost:3000/api/asr", language="id")
    transcription = stt.record_and_transcribe()
    # Or with a file:
    transcription = stt.transcribe_file("recording.webm")
"""

import os
import io
import wave
import json
import struct
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

import requests

# Configure logging
logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Speech-to-Text engine that records audio from a microphone
    and transcribes it using the Voice Robot ASR API.

    This module supports recording audio through multiple backends:
    - sounddevice (recommended, cross-platform)
    - pyaudio (alternative)
    - subprocess + arecord/sox (Linux fallback)

    The recorded audio is sent to the ASR API endpoint which
    processes it and returns the transcription text.

    Attributes:
        api_url (str): URL of the ASR API endpoint.
        language (str): Language code for recognition (default: 'id').
        sample_rate (int): Audio sample rate in Hz (default: 16000).
        channels (int): Number of audio channels (default: 1).
        timeout (int): API request timeout in seconds (default: 30).
    """

    # Supported languages mapping
    SUPPORTED_LANGUAGES = {
        "id": "Bahasa Indonesia",
        "en": "English",
        "fr": "Français",
        "de": "Deutsch",
        "ar": "العربية",
        "ms": "Bahasa Melayu",
        "zh": "中文",
        "ja": "日本語",
        "ru": "Русский",
        "ko": "한국어",
        "es": "Español",
        "pt": "Português",
        "it": "Italiano",
        "th": "ภาษาไทย",
        "vi": "Tiếng Việt",
        "hi": "हिन्दी",
        "tr": "Türkçe",
        "nl": "Nederlands",
        "pl": "Polski",
        "sv": "Svenska",
    }

    def __init__(
        self,
        api_url: str = "http://localhost:3000/api/asr",
        language: str = "id",
        sample_rate: int = 16000,
        channels: int = 1,
        timeout: int = 30,
    ):
        """
        Initialize the Speech-to-Text engine.

        Args:
            api_url: URL of the ASR API endpoint.
            language: Language code for speech recognition.
            sample_rate: Audio sample rate in Hz.
            channels: Number of audio channels (1=mono, 2=stereo).
            timeout: API request timeout in seconds.
        """
        self.api_url = api_url
        self.language = language
        self.sample_rate = sample_rate
        self.channels = channels
        self.timeout = timeout
        self._recording = False
        self._audio_buffer = []

        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(
                f"Language '{language}' not in supported list. "
                f"Available: {list(self.SUPPORTED_LANGUAGES.keys())}"
            )

        logger.info(f"SpeechToText initialized - Language: {language}, API: {api_url}")

    def set_language(self, language: str) -> None:
        """
        Change the recognition language.

        Args:
            language: Language code (e.g., 'id', 'en', 'ja').
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            logger.info(f"Language changed to: {language} ({self.SUPPORTED_LANGUAGES[language]})")
        else:
            logger.warning(f"Unsupported language: {language}")

    def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file using the ASR API.

        This method reads an audio file and sends it to the ASR API
        endpoint for transcription. The file can be in WebM, WAV, or
        any format supported by the API.

        Args:
            file_path: Path to the audio file to transcribe.

        Returns:
            Dictionary containing:
                - success (bool): Whether transcription succeeded.
                - transcription (str): The transcribed text.
                - language (str): The language used for recognition.
                - error (str): Error message if failed.

        Example:
            >>> stt = SpeechToText(language="en")
            >>> result = stt.transcribe_file("my_recording.webm")
            >>> print(result["transcription"])
            "Hello, how are you today?"
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "error": f"File not found: {file_path}",
            }

        try:
            logger.info(f"Transcribing file: {file_path}")

            with open(file_path, "rb") as audio_file:
                files = {"audio": (os.path.basename(file_path), audio_file, "audio/webm")}
                data = {"language": self.language}

                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get("transcription", "")
                    logger.info(f"Transcription result: {transcription[:100]}...")
                    return {
                        "success": True,
                        "transcription": transcription,
                        "language": self.language,
                        "error": None,
                    }
                else:
                    error_msg = f"API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "transcription": "",
                        "language": self.language,
                        "error": error_msg,
                    }

        except requests.exceptions.Timeout:
            error_msg = "ASR request timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "error": error_msg,
            }
        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to ASR API at {self.api_url}"
            logger.error(error_msg)
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "error": error_msg,
            }

    def transcribe_audio_data(self, audio_data: bytes, format: str = "webm") -> Dict[str, Any]:
        """
        Transcribe raw audio data bytes using the ASR API.

        This method is useful when audio data is already in memory,
        such as from a streaming source or pre-loaded file.

        Args:
            audio_data: Raw audio bytes to transcribe.
            format: Audio format (e.g., 'webm', 'wav', 'mp3').

        Returns:
            Dictionary containing:
                - success (bool): Whether transcription succeeded.
                - transcription (str): The transcribed text.
                - language (str): The language used for recognition.
                - error (str): Error message if failed.

        Example:
            >>> with open("recording.webm", "rb") as f:
            ...     audio_bytes = f.read()
            >>> result = stt.transcribe_audio_data(audio_bytes)
        """
        try:
            logger.info(f"Transcribing audio data ({len(audio_data)} bytes, format: {format})")

            mime_type = f"audio/{format}"
            filename = f"recording.{format}"

            files = {"audio": (filename, io.BytesIO(audio_data), mime_type)}
            data = {"language": self.language}

            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                transcription = result.get("transcription", "")
                logger.info(f"Transcription result: {transcription[:100]}...")
                return {
                    "success": True,
                    "transcription": transcription,
                    "language": self.language,
                    "error": None,
                }
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "transcription": "",
                    "language": self.language,
                    "error": error_msg,
                }

        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "error": error_msg,
            }

    def record_and_transcribe(
        self,
        duration: float = 5.0,
        silence_threshold: float = 0.02,
        silence_duration: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Record audio from the microphone and transcribe it.

        This method attempts to record audio using available backends
        (sounddevice → pyaudio → arecord), then sends the recorded
        audio to the ASR API for transcription.

        The recording can stop automatically when silence is detected
        for the specified duration, or after the maximum duration.

        Args:
            duration: Maximum recording duration in seconds.
            silence_threshold: RMS amplitude threshold for silence detection.
            silence_duration: Duration of silence before auto-stop in seconds.

        Returns:
            Dictionary containing:
                - success (bool): Whether recording and transcription succeeded.
                - transcription (str): The transcribed text.
                - language (str): The language used for recognition.
                - audio_path (str): Path to the temporary audio file.
                - error (str): Error message if failed.

        Example:
            >>> stt = SpeechToText(language="id")
            >>> result = stt.record_and_transcribe(duration=10)
            >>> if result["success"]:
            ...     print(f"You said: {result['transcription']}")
        """
        logger.info(f"Starting recording (max {duration}s, language: {self.language})")

        # Try different recording backends
        audio_path = None

        try:
            audio_path = self._record_sounddevice(duration, silence_threshold, silence_duration)
        except ImportError:
            logger.debug("sounddevice not available, trying pyaudio...")
            try:
                audio_path = self._record_pyaudio(duration, silence_threshold, silence_duration)
            except ImportError:
                logger.debug("pyaudio not available, trying arecord...")
                audio_path = self._record_arecord(duration)

        if audio_path is None:
            return {
                "success": False,
                "transcription": "",
                "language": self.language,
                "audio_path": None,
                "error": (
                    "No audio recording backend available. "
                    "Install sounddevice, pyaudio, or use arecord (Linux)."
                ),
            }

        # Transcribe the recorded audio
        result = self.transcribe_file(audio_path)
        result["audio_path"] = audio_path

        return result

    def _record_sounddevice(
        self,
        duration: float,
        silence_threshold: float,
        silence_duration: float,
    ) -> Optional[str]:
        """
        Record audio using the sounddevice library.

        Sounddevice is the recommended cross-platform audio recording
        backend. It supports real-time audio callback processing,
        which enables silence detection during recording.

        Args:
            duration: Maximum recording duration in seconds.
            silence_threshold: RMS threshold for silence.
            silence_duration: Silence duration before auto-stop.

        Returns:
            Path to the recorded WAV file, or None on failure.
        """
        import sounddevice as sd
        import numpy as np

        logger.info("Recording with sounddevice...")

        frames = []
        silence_start = None
        self._recording = True

        def audio_callback(indata, frames_count, time_info, status):
            """Callback for sounddevice to process audio frames."""
            if status:
                logger.warning(f"Audio callback status: {status}")

            frames.append(indata.copy())

            # Silence detection
            rms = np.sqrt(np.mean(indata ** 2))
            if rms < silence_threshold:
                if silence_start is None:
                    silence_start = time_info.currentTime
                elif (time_info.currentTime - silence_start) > silence_duration:
                    logger.info("Silence detected, stopping recording...")
                    raise sd.CallbackStop()
            else:
                silence_start = None

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                dtype="float32",
            ):
                sd.sleep(int(duration * 1000))
        except sd.CallbackStop:
            pass  # Silence detected, normal stop
        finally:
            self._recording = False

        if not frames:
            logger.warning("No audio frames recorded")
            return None

        # Convert to WAV and save
        audio_data = np.concatenate(frames, axis=0)
        temp_path = self._save_wav(audio_data)

        logger.info(f"Recording saved to: {temp_path}")
        return temp_path

    def _record_pyaudio(
        self,
        duration: float,
        silence_threshold: float,
        silence_duration: float,
    ) -> Optional[str]:
        """
        Record audio using the PyAudio library.

        PyAudio is an alternative audio recording backend that uses
        PortAudio under the hood. It works on most platforms but
        may have more latency than sounddevice.

        Args:
            duration: Maximum recording duration in seconds.
            silence_threshold: RMS threshold for silence.
            silence_duration: Silence duration before auto-stop.

        Returns:
            Path to the recorded WAV file, or None on failure.
        """
        import pyaudio

        logger.info("Recording with PyAudio...")

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=CHUNK,
            )

            frames = []
            silence_count = 0
            max_silence_chunks = int(silence_duration * self.sample_rate / CHUNK)
            total_chunks = int(duration * self.sample_rate / CHUNK)

            logger.info(f"Recording for up to {duration} seconds...")

            for _ in range(total_chunks):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

                # Simple silence detection
                import audioop
                rms = audioop.rms(data, 2) / 32767.0  # Normalize
                if rms < silence_threshold:
                    silence_count += 1
                    if silence_count >= max_silence_chunks:
                        logger.info("Silence detected, stopping...")
                        break
                else:
                    silence_count = 0

            stream.stop_stream()
            stream.close()

        finally:
            p.terminate()

        if not frames:
            return None

        # Save as WAV
        temp_path = tempfile.mktemp(suffix=".wav")
        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        logger.info(f"Recording saved to: {temp_path}")
        return temp_path

    def _record_arecord(self, duration: float) -> Optional[str]:
        """
        Record audio using arecord (Linux ALSA).

        This is a fallback method for Linux systems where
        sounddevice and pyaudio are not available. It uses
        the ALSA arecord command-line tool.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Path to the recorded WAV file, or None on failure.
        """
        import subprocess

        logger.info("Recording with arecord...")

        temp_path = tempfile.mktemp(suffix=".wav")

        try:
            cmd = [
                "arecord",
                "-f", "S16_LE",
                "-r", str(self.sample_rate),
                "-c", str(self.channels),
                "-d", str(int(duration)),
                temp_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Recording saved to: {temp_path}")
            return temp_path

        except FileNotFoundError:
            logger.warning("arecord not found on system")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"arecord failed: {e.stderr.decode()}")
            return None

    def _save_wav(self, audio_data, path: Optional[str] = None) -> str:
        """
        Save numpy audio data as a WAV file.

        Args:
            audio_data: Numpy array of audio samples (float32).
            path: Optional output path. If None, a temp file is created.

        Returns:
            Path to the saved WAV file.
        """
        import numpy as np

        if path is None:
            path = tempfile.mktemp(suffix=".wav")

        # Convert float32 to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return path

    def is_recording(self) -> bool:
        """Check if currently recording audio."""
        return self._recording

    def stop_recording(self) -> None:
        """Stop the current recording session."""
        self._recording = False
        logger.info("Recording stopped by user")

    @classmethod
    def list_supported_languages(cls) -> Dict[str, str]:
        """
        Get a dictionary of all supported languages.

        Returns:
            Dictionary mapping language codes to language names.

        Example:
            >>> SpeechToText.list_supported_languages()
            {'id': 'Bahasa Indonesia', 'en': 'English', ...}
        """
        return cls.SUPPORTED_LANGUAGES.copy()

    def __repr__(self) -> str:
        return (
            f"SpeechToText(language='{self.language}', "
            f"api_url='{self.api_url}', sample_rate={self.sample_rate})"
        )
