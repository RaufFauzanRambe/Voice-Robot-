"""
Text-to-Speech Module (TTS)
=============================
Converts text to speech audio using the Voice Robot TTS API endpoint.

Features:
    - Text-to-speech synthesis with 7 voice personalities
    - Speed and volume control
    - Audio playback via multiple backends
    - Audio file saving (WAV format)
    - Async-friendly long text chunking
    - Voice preview support

Classes:
    TextToSpeech - Main TTS engine

Usage:
    tts = TextToSpeech(voice="tongtong", language="id")
    tts.speak("Halo! Namaku TongTong, senang bertemu denganmu!")
    # Or save to file:
    tts.save_to_file("Hello world!", "output.wav")
"""

import os
import io
import wave
import logging
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Text-to-Speech engine using the Voice Robot TTS API.

    This module converts text into spoken audio using 7 different
    voice personalities. It supports speed and volume control,
    audio playback through multiple backends, and file saving.

    Voice Personalities:
        - tongtong: Warm & Friendly (😊)
        - chuichui: Cheerful & Funny (😄)
        - xiaochen: Professional & Calm (💼)
        - jam: English Gentleman (🎩)
        - kazi: Clear & Standard (🎯)
        - douji: Natural & Casual (🌊)
        - luodo: Expressive & Dramatic (🎭)

    Attributes:
        api_url: URL of the TTS API endpoint.
        voice: Current voice personality ID.
        speed: Speech speed multiplier (0.5-2.0).
        volume: Volume level (0.1-1.0).
        language: Language code for text processing.

    Example:
        >>> tts = TextToSpeech(voice="tongtong")
        >>> tts.speak("Halo, apa kabar?")
        >>> tts.save_to_file("Hello world!", "greeting.wav")
    """

    # Voice profile configurations
    VOICE_PROFILES = {
        "tongtong": {
            "name": "TongTong",
            "emoji": "😊",
            "personality": "Warm & Friendly",
            "color": "#10b981",
            "description": "Gentle, warm voice perfect for casual conversations",
        },
        "chuichui": {
            "name": "ChuiChui",
            "emoji": "😄",
            "personality": "Cheerful & Funny",
            "color": "#f59e0b",
            "description": "Energetic, cheerful voice that brings joy",
        },
        "xiaochen": {
            "name": "XiaoChen",
            "emoji": "💼",
            "personality": "Professional & Calm",
            "color": "#6366f1",
            "description": "Stable, authoritative voice for business use",
        },
        "jam": {
            "name": "Jam",
            "emoji": "🎩",
            "personality": "English Gentleman",
            "color": "#8b5cf6",
            "description": "Refined, elegant voice for English conversations",
        },
        "kazi": {
            "name": "Kazi",
            "emoji": "🎯",
            "personality": "Clear & Standard",
            "color": "#06b6d4",
            "description": "Clear pronunciation, ideal for learning",
        },
        "douji": {
            "name": "DouJi",
            "emoji": "🌊",
            "personality": "Natural & Casual",
            "color": "#ec4899",
            "description": "Natural flowing voice, feels very human",
        },
        "luodo": {
            "name": "LuoDo",
            "emoji": "🎭",
            "personality": "Expressive & Dramatic",
            "color": "#ef4444",
            "description": "Expressive, emotional voice for storytelling",
        },
    }

    # Language sample texts for voice previews
    LANGUAGE_SAMPLES = {
        "id": "Halo! Saya Voice Robot, asisten AI Anda. Senang bertemu dengan Anda!",
        "en": "Hello! I am Voice Robot, your AI assistant. Nice to meet you!",
        "fr": "Bonjour! Je suis Voice Robot, votre assistant IA. Enchanté!",
        "de": "Hallo! Ich bin Voice Robot, Ihr KI-Assistent. Schön, Sie kennenzulernen!",
        "ar": "مرحبا! أنا روبوت الصوت، مساعدك الذكي. سعيد بلقائك!",
        "ms": "Helo! Saya Voice Robot, pembantu AI anda. Gembira berjumpa anda!",
        "zh": "你好！我是语音机器人，你的AI助手。很高兴见到你！",
        "ja": "こんにちは！私はボイスロボット、あなたのAIアシスタントです。",
        "ru": "Привет! Я Голосовой Робот, ваш ИИ-помощник. Рад встрече!",
        "ko": "안녕하세요! 저는 음성 로봇, 당신의 AI 어시스턴트입니다.",
        "es": "¡Hola! Soy Voice Robot, tu asistente de IA. ¡Encantado de conocerte!",
        "pt": "Olá! Eu sou o Voice Robot, seu assistente de IA. Prazer em conhecê-lo!",
        "it": "Ciao! Sono Voice Robot, il tuo assistente IA. Piacere di conoscerti!",
        "th": "สวัสดี! ฉันคือ Voice Robot ผู้ช่วย AI ของคุณ",
        "vi": "Xin chào! Tôi là Voice Robot, trợ lý AI của bạn.",
        "hi": "नमस्ते! मैं वॉइस रोबोट हूँ, आपका AI सहायक।",
        "tr": "Merhaba! Ben Voice Robot, yapay zeka asistanınız.",
        "nl": "Hallo! Ik ben Voice Robot, uw AI-assistent.",
        "pl": "Cześć! Jestem Voice Robot, Twój asystent AI.",
        "sv": "Hej! Jag är Voice Robot, din AI-assistent.",
    }

    def __init__(
        self,
        api_url: str = "http://localhost:3000/api/tts",
        voice: str = "tongtong",
        speed: float = 1.0,
        volume: float = 0.8,
        language: str = "id",
        timeout: int = 30,
        max_text_length: int = 1024,
    ):
        """
        Initialize the Text-to-Speech engine.

        Args:
            api_url: URL of the TTS API endpoint.
            voice: Voice personality ID.
            speed: Speech speed (0.5=slow, 1.0=normal, 2.0=fast).
            volume: Volume level (0.1=quiet, 1.0=loud).
            language: Language code for sample text generation.
            timeout: API request timeout in seconds.
            max_text_length: Maximum text length per TTS request.
        """
        self.api_url = api_url
        self.voice = voice
        self.speed = max(0.5, min(2.0, speed))
        self.volume = max(0.1, min(1.0, volume))
        self.language = language
        self.timeout = timeout
        self.max_text_length = max_text_length

        # Validate voice
        if voice not in self.VOICE_PROFILES:
            logger.warning(
                f"Voice '{voice}' not recognized. "
                f"Available: {list(self.VOICE_PROFILES.keys())}"
            )

        logger.info(
            f"TextToSpeech initialized - Voice: {voice}, "
            f"Speed: {speed}x, Volume: {volume*100:.0f}%"
        )

    def set_voice(self, voice: str) -> None:
        """
        Change the voice personality.

        Args:
            voice: Voice ID ('tongtong', 'chuichui', 'xiaochen',
                   'jam', 'kazi', 'douji', 'luodo').
        """
        if voice in self.VOICE_PROFILES:
            self.voice = voice
            profile = self.VOICE_PROFILES[voice]
            logger.info(
                f"Voice changed to: {profile['name']} {profile['emoji']} "
                f"({profile['personality']})"
            )
        else:
            logger.warning(f"Unknown voice: {voice}")

    def set_speed(self, speed: float) -> None:
        """
        Change the speech speed.

        Args:
            speed: Speed multiplier (0.5 to 2.0).
        """
        self.speed = max(0.5, min(2.0, speed))
        logger.info(f"Speed changed to: {self.speed:.1f}x")

    def set_volume(self, volume: float) -> None:
        """
        Change the output volume.

        Args:
            volume: Volume level (0.1 to 1.0).
        """
        self.volume = max(0.1, min(1.0, volume))
        logger.info(f"Volume changed to: {self.volume*100:.0f}%")

    def set_language(self, language: str) -> None:
        """
        Change the language for sample text generation.

        Args:
            language: Language code (e.g., 'id', 'en', 'ja').
        """
        self.language = language
        logger.info(f"Language changed to: {language}")

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text via the TTS API.

        This method sends text to the TTS API and returns
        the audio data as bytes. For long texts that exceed
        the maximum character limit, the text is automatically
        chunked and synthesized in parts.

        Args:
            text: Text to convert to speech.
            voice: Optional voice override for this request.
            speed: Optional speed override for this request.
            volume: Optional volume override for this request.

        Returns:
            Dictionary containing:
                - success (bool): Whether synthesis succeeded.
                - audio_data (bytes): WAV audio data.
                - duration_estimate (float): Estimated audio duration.
                - error (str): Error message if failed.

        Example:
            >>> tts = TextToSpeech()
            >>> result = tts.synthesize("Hello world!")
            >>> if result["success"]:
            ...     with open("output.wav", "wb") as f:
            ...         f.write(result["audio_data"])
        """
        if not text or not text.strip():
            return {
                "success": False,
                "audio_data": b"",
                "duration_estimate": 0.0,
                "error": "Empty text provided",
            }

        text = text.strip()
        voice_id = voice or self.voice
        speed_val = speed or self.speed
        volume_val = volume or self.volume

        # Check if text needs to be chunked
        if len(text) > self.max_text_length:
            return self._synthesize_chunked(text, voice_id, speed_val, volume_val)

        try:
            logger.info(
                f"Synthesizing: {len(text)} chars, "
                f"voice={voice_id}, speed={speed_val:.1f}x"
            )

            payload = {
                "text": text,
                "voice": voice_id,
                "speed": speed_val,
                "volume": volume_val,
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                audio_data = response.content
                # Estimate duration from WAV header
                duration = self._estimate_wav_duration(audio_data)

                logger.info(
                    f"Synthesis complete: {len(audio_data)} bytes, "
                    f"~{duration:.1f}s duration"
                )

                return {
                    "success": True,
                    "audio_data": audio_data,
                    "duration_estimate": duration,
                    "error": None,
                }
            else:
                error_msg = f"TTS API error: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "audio_data": b"",
                    "duration_estimate": 0.0,
                    "error": error_msg,
                }

        except requests.exceptions.Timeout:
            error_msg = "TTS request timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "audio_data": b"",
                "duration_estimate": 0.0,
                "error": error_msg,
            }

        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to TTS API at {self.api_url}"
            logger.error(error_msg)
            return {
                "success": False,
                "audio_data": b"",
                "duration_estimate": 0.0,
                "error": error_msg,
            }

        except Exception as e:
            error_msg = f"TTS synthesis error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "audio_data": b"",
                "duration_estimate": 0.0,
                "error": error_msg,
            }

    def _synthesize_chunked(
        self,
        text: str,
        voice: str,
        speed: float,
        volume: float,
    ) -> Dict[str, Any]:
        """
        Synthesize long text by splitting into chunks.

        For texts longer than max_text_length, the text is split
        at sentence boundaries and each chunk is synthesized
        separately. The audio chunks are then concatenated.

        Args:
            text: Long text to synthesize.
            voice: Voice personality ID.
            speed: Speech speed.
            volume: Volume level.

        Returns:
            Dictionary with concatenated audio data.
        """
        logger.info(f"Chunking text ({len(text)} chars) for synthesis...")

        # Split text into chunks at sentence boundaries
        chunks = self._split_text_into_chunks(text, self.max_text_length)
        audio_chunks: List[bytes] = []
        total_duration = 0.0

        for i, chunk in enumerate(chunks):
            logger.debug(f"Synthesizing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

            result = self.synthesize(chunk, voice=voice, speed=speed, volume=volume)

            if result["success"]:
                audio_chunks.append(result["audio_data"])
                total_duration += result["duration_estimate"]
            else:
                logger.warning(f"Chunk {i+1} failed: {result['error']}")

        if not audio_chunks:
            return {
                "success": False,
                "audio_data": b"",
                "duration_estimate": 0.0,
                "error": "All chunks failed to synthesize",
            }

        # Concatenate WAV files
        combined_audio = self._concatenate_wav(audio_chunks)

        return {
            "success": True,
            "audio_data": combined_audio,
            "duration_estimate": total_duration,
            "error": None,
        }

    def _split_text_into_chunks(self, text: str, max_length: int) -> List[str]:
        """
        Split text into chunks at sentence boundaries.

        Tries to split at sentence-ending punctuation (.!?)
        while keeping each chunk under the maximum length.

        Args:
            text: Text to split.
            max_length: Maximum length per chunk.

        Returns:
            List of text chunks.
        """
        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break

            # Find the last sentence boundary within max_length
            split_pos = max_length
            for punct in [". ", "! ", "? ", "。", "！", "？", "\n"]:
                pos = remaining[:max_length].rfind(punct)
                if pos > 0:
                    split_pos = pos + len(punct)
                    break

            chunks.append(remaining[:split_pos].strip())
            remaining = remaining[split_pos:].strip()

        return chunks

    def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None,
        blocking: bool = True,
    ) -> Dict[str, Any]:
        """
        Synthesize speech and play it through the speakers.

        This is the primary method for producing spoken output.
        It synthesizes the text and then plays the resulting
        audio through the system's audio output.

        Args:
            text: Text to speak.
            voice: Optional voice override.
            speed: Optional speed override.
            volume: Optional volume override.
            blocking: If True, wait until playback finishes.

        Returns:
            Dictionary with synthesis results and playback status.

        Example:
            >>> tts = TextToSpeech(voice="jam")
            >>> tts.speak("Good day! How may I assist you?")
        """
        result = self.synthesize(text, voice=voice, speed=speed, volume=volume)

        if not result["success"]:
            return result

        # Play the audio
        play_result = self._play_audio(result["audio_data"], blocking=blocking)
        result["playback"] = play_result

        return result

    def save_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize speech and save it to a WAV file.

        Args:
            text: Text to synthesize.
            output_path: Path to save the audio file.
            voice: Optional voice override.
            speed: Optional speed override.
            volume: Optional volume override.

        Returns:
            Dictionary with synthesis results and file path.

        Example:
            >>> tts = TextToSpeech()
            >>> result = tts.save_to_file("Hello world!", "greeting.wav")
            >>> print(result["file_path"])
        """
        result = self.synthesize(text, voice=voice, speed=speed, volume=volume)

        if not result["success"]:
            return result

        try:
            # Ensure directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Write audio data to file
            with open(output_path, "wb") as f:
                f.write(result["audio_data"])

            file_size = os.path.getsize(output_path)
            logger.info(f"Audio saved to: {output_path} ({file_size} bytes)")

            result["file_path"] = output_path
            result["file_size"] = file_size

            return result

        except IOError as e:
            error_msg = f"Failed to save file: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result

    def preview_voice(self, voice: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Preview a voice personality with a sample text.

        Plays a short sample in the specified voice to help
        users decide which voice personality they prefer.

        Args:
            voice: Voice ID to preview.
            language: Optional language for sample text.

        Returns:
            Dictionary with synthesis and playback results.

        Example:
            >>> tts = TextToSpeech()
            >>> tts.preview_voice("jam")  # Plays English gentleman sample
        """
        lang = language or self.language
        sample_text = self.LANGUAGE_SAMPLES.get(
            lang, self.LANGUAGE_SAMPLES["en"]
        )

        logger.info(f"Previewing voice: {voice} (language: {lang})")
        return self.speak(sample_text, voice=voice, speed=1.0)

    def _play_audio(self, audio_data: bytes, blocking: bool = True) -> Dict[str, Any]:
        """
        Play audio data through the system speakers.

        Tries multiple playback backends in order:
        1. sounddevice (recommended)
        2. pyaudio
        3. subprocess (aplay/afplay/sox)

        Args:
            audio_data: WAV audio bytes to play.
            blocking: If True, wait until playback finishes.

        Returns:
            Dictionary with playback status.
        """
        # Save to temporary file for playback
        temp_path = tempfile.mktemp(suffix=".wav")
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_data)

            # Try sounddevice first (best quality)
            try:
                return self._play_sounddevice(temp_path, blocking=blocking)
            except ImportError:
                pass

            # Try pyaudio
            try:
                return self._play_pyaudio(temp_path, blocking=blocking)
            except ImportError:
                pass

            # Try system commands
            return self._play_system(temp_path, blocking=blocking)

        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _play_sounddevice(self, file_path: str, blocking: bool = True) -> Dict[str, Any]:
        """
        Play audio using sounddevice library.

        Args:
            file_path: Path to WAV file.
            blocking: Whether to wait for playback to finish.

        Returns:
            Playback status dictionary.
        """
        import sounddevice as sd
        import numpy as np

        with wave.open(file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())

        audio_array = np.frombuffer(frames, dtype=np.int16)
        if channels > 1:
            audio_array = audio_array.reshape(-1, channels)

        sd.play(audio_array, samplerate=sample_rate)

        if blocking:
            sd.wait()

        return {"success": True, "backend": "sounddevice", "blocking": blocking}

    def _play_pyaudio(self, file_path: str, blocking: bool = True) -> Dict[str, Any]:
        """
        Play audio using PyAudio library.

        Args:
            file_path: Path to WAV file.
            blocking: Whether to wait for playback to finish.

        Returns:
            Playback status dictionary.
        """
        import pyaudio

        p = pyaudio.PyAudio()

        try:
            with wave.open(file_path, "rb") as wf:
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )

                chunk_size = 1024
                data = wf.readframes(chunk_size)

                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)

                stream.stop_stream()
                stream.close()

            return {"success": True, "backend": "pyaudio", "blocking": True}

        finally:
            p.terminate()

    def _play_system(self, file_path: str, blocking: bool = True) -> Dict[str, Any]:
        """
        Play audio using system commands (aplay/afplay/sox).

        Args:
            file_path: Path to WAV file.
            blocking: Whether to wait for playback to finish.

        Returns:
            Playback status dictionary.
        """
        import subprocess
        import platform

        system = platform.system()

        if system == "Linux":
            cmd = ["aplay", file_path]
        elif system == "Darwin":
            cmd = ["afplay", file_path]
        else:
            # Try sox as last resort
            cmd = ["play", file_path]

        try:
            if blocking:
                subprocess.run(cmd, check=True, capture_output=True)
            else:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return {"success": True, "backend": "system", "blocking": blocking}

        except FileNotFoundError:
            return {
                "success": False,
                "backend": "system",
                "error": "No audio playback command found (tried aplay/afplay/play)",
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "backend": "system",
                "error": f"Playback command failed: {e.stderr.decode()}",
            }

    def _estimate_wav_duration(self, wav_data: bytes) -> float:
        """
        Estimate the duration of a WAV audio from its binary data.

        Parses the WAV header to extract sample rate, channels,
        and bits per sample, then calculates the duration.

        Args:
            wav_data: WAV file binary data.

        Returns:
            Estimated duration in seconds.
        """
        try:
            with wave.open(io.BytesIO(wav_data), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / max(rate, 1)
        except Exception:
            # Fallback: rough estimate based on data size
            # Assuming 16-bit mono at 22050 Hz
            return len(wav_data) / (22050 * 2)

    def _concatenate_wav(self, wav_chunks: List[bytes]) -> bytes:
        """
        Concatenate multiple WAV audio chunks into one.

        All chunks must have the same sample rate, channels,
        and sample width for proper concatenation.

        Args:
            wav_chunks: List of WAV audio byte data.

        Returns:
            Combined WAV audio bytes.
        """
        if len(wav_chunks) == 1:
            return wav_chunks[0]

        try:
            output = io.BytesIO()

            # Read first chunk for parameters
            with wave.open(io.BytesIO(wav_chunks[0]), "rb") as first:
                params = first.getparams()
                all_frames = first.readframes(first.getnframes())

            # Read remaining chunks
            for chunk_data in wav_chunks[1:]:
                with wave.open(io.BytesIO(chunk_data), "rb") as chunk:
                    all_frames += chunk.readframes(chunk.getnframes())

            # Write combined WAV
            with wave.open(output, "wb") as combined:
                combined.setparams(params)
                combined.writeframes(all_frames)

            return output.getvalue()

        except Exception as e:
            logger.error(f"WAV concatenation failed: {e}")
            # Return the first chunk as fallback
            return wav_chunks[0]

    @classmethod
    def list_voices(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all available voice personalities.

        Returns:
            Dictionary mapping voice IDs to profile info.
        """
        return cls.VOICE_PROFILES.copy()

    @classmethod
    def list_language_samples(cls) -> Dict[str, str]:
        """
        Get sample texts for all supported languages.

        Returns:
            Dictionary mapping language codes to sample texts.
        """
        return cls.LANGUAGE_SAMPLES.copy()

    def __repr__(self) -> str:
        voice_name = self.VOICE_PROFILES.get(self.voice, {}).get("name", self.voice)
        return (
            f"TextToSpeech(voice='{voice_name}', "
            f"speed={self.speed:.1f}x, volume={self.volume*100:.0f}%)"
        )
