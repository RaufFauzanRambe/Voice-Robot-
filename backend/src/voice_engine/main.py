"""
Voice Engine - Main Orchestrator
==================================
Main module that orchestrates the complete voice interaction pipeline:
Speech → ASR → NLP → AI Response → TTS → Audio Playback

This module ties together all voice engine components into a
seamless conversational AI experience supporting 20 languages
and 7 voice personalities.

Features:
    - Complete voice interaction loop (speak → listen → respond)
    - 20 language support with automatic detection
    - 7 voice personalities
    - Interactive CLI mode
    - Single query mode
    - Conversation history management
    - Configurable AI parameters

Classes:
    VoiceEngine - Main orchestrator class

Usage:
    # Interactive mode
    engine = VoiceEngine(language="id", voice="tongtong")
    engine.run()

    # Single query
    engine = VoiceEngine()
    engine.chat("Hello, how are you?")

    # Change language mid-conversation
    engine.set_language("ja")
    engine.chat("こんにちは！")

CLI Usage:
    python -m voice_engine.main --language en --voice jam --interactive
    python -m voice_engine.main --text "Halo, apa kabar?" --language id
    python -m voice_engine.main --list-languages
    python -m voice_engine.main --list-voices
"""

import sys
import time
import json
import logging
import argparse
from typing import Optional, Dict, Any, List
from datetime import datetime

from .speech_to_text import SpeechToText
from .nlp_engine import NLPEngine
from .response_generator import ResponseGenerator
from .text_to_speech import TextToSpeech

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Main Voice Engine orchestrator that combines all modules.

    This class manages the complete voice interaction pipeline,
    from speech recognition through NLP analysis to AI response
    generation and text-to-speech playback.

    The engine supports:
    - 20 languages with automatic detection
    - 7 voice personalities
    - Interactive and single-query modes
    - Automatic and manual language switching
    - Conversation history management

    Attributes:
        language: Current language code.
        voice: Current voice personality ID.
        stt: SpeechToText instance.
        nlp: NLPEngine instance.
        generator: ResponseGenerator instance.
        tts: TextToSpeech instance.

    Example:
        >>> engine = VoiceEngine(language="id", voice="tongtong")
        >>> engine.chat("Halo Robot!")
        >>> engine.run()  # Interactive mode
    """

    # Supported languages
    LANGUAGES = {
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

    # Voice profiles
    VOICES = {
        "tongtong": "TongTong 😊 (Warm & Friendly)",
        "chuichui": "ChuiChui 😄 (Cheerful & Funny)",
        "xiaochen": "XiaoChen 💼 (Professional)",
        "jam": "Jam 🎩 (English Gentleman)",
        "kazi": "Kazi 🎯 (Clear & Standard)",
        "douji": "DouJi 🌊 (Natural & Casual)",
        "luodo": "LuoDo 🎭 (Expressive & Dramatic)",
    }

    def __init__(
        self,
        language: str = "id",
        voice: str = "tongtong",
        base_url: str = "http://localhost:3000",
        auto_speak: bool = True,
        auto_detect_language: bool = False,
        speed: float = 1.0,
        volume: float = 0.8,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """
        Initialize the Voice Engine.

        Args:
            language: Default language code.
            voice: Default voice personality ID.
            base_url: Base URL of the Voice Robot API server.
            auto_speak: Whether to automatically speak AI responses.
            auto_detect_language: Whether to auto-detect user's language.
            speed: TTS speech speed multiplier.
            volume: TTS volume level.
            temperature: AI response creativity (0.0-2.0).
            max_tokens: Maximum AI response length.
        """
        self.language = language
        self.voice = voice
        self.base_url = base_url
        self.auto_speak = auto_speak
        self.auto_detect_language = auto_detect_language

        # Initialize all modules
        self.stt = SpeechToText(
            api_url=f"{base_url}/api/asr",
            language=language,
        )

        self.nlp = NLPEngine(default_language=language)

        self.generator = ResponseGenerator(
            api_url=f"{base_url}/api/chat",
            language=language,
            voice=voice,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.tts = TextToSpeech(
            api_url=f"{base_url}/api/tts",
            voice=voice,
            speed=speed,
            volume=volume,
            language=language,
        )

        # Conversation stats
        self._conversation_start = datetime.now()
        self._total_queries = 0
        self._total_errors = 0

        logger.info(
            f"VoiceEngine initialized - "
            f"Language: {language} ({self.LANGUAGES.get(language, '?')}), "
            f"Voice: {voice}, Auto-speak: {auto_speak}"
        )

    def chat(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        speak: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Send a text message and get an AI response.

        This is the primary method for text-based interaction.
        It processes the text through NLP, generates an AI
        response, and optionally speaks it.

        Args:
            text: User message text.
            language: Optional language override for this message.
            voice: Optional voice override for this response.
            speak: Whether to speak the response (overrides auto_speak).

        Returns:
            Dictionary containing:
                - user_text: The user's input text.
                - ai_text: The AI's response text.
                - nlp: NLP analysis results.
                - language: Language used.
                - voice: Voice used.
                - success: Whether the interaction succeeded.
                - error: Error message if failed.

        Example:
            >>> engine = VoiceEngine(language="en")
            >>> result = engine.chat("What is machine learning?")
            >>> print(result["ai_text"])
        """
        lang = language or self.language
        voice_id = voice or self.voice
        should_speak = speak if speak is not None else self.auto_speak

        result = {
            "user_text": text,
            "ai_text": "",
            "nlp": None,
            "language": lang,
            "voice": voice_id,
            "success": False,
            "error": None,
        }

        self._total_queries += 1

        try:
            # Step 1: NLP Analysis
            nlp_result = self.nlp.process(text, language_hint=lang)
            result["nlp"] = {
                "detected_language": nlp_result.detected_language,
                "language_confidence": nlp_result.language_confidence,
                "intent": nlp_result.intent,
                "intent_confidence": nlp_result.intent_confidence,
                "sentiment": nlp_result.sentiment,
                "sentiment_score": nlp_result.sentiment_score,
                "keywords": nlp_result.keywords,
                "is_question": nlp_result.is_question,
            }

            # Auto-detect language if enabled
            detected_lang = nlp_result.detected_language
            if self.auto_detect_language and nlp_result.language_confidence > 0.5:
                if detected_lang in self.LANGUAGES and detected_lang != lang:
                    logger.info(
                        f"Auto-detected language: {detected_lang} "
                        f"({nlp_result.language_confidence:.2f})"
                    )
                    lang = detected_lang
                    self.generator.set_language(lang)
                    result["language"] = lang

            # Step 2: Generate AI Response
            self.generator.set_language(lang)
            self.generator.set_voice(voice_id)

            response = self.generator.generate(text)

            if not response.success:
                result["error"] = response.error
                self._total_errors += 1
                return result

            result["ai_text"] = response.text
            result["success"] = True

            # Step 3: Text-to-Speech (if enabled)
            if should_speak and response.text:
                self.tts.set_voice(voice_id)
                self.tts.set_language(lang)
                tts_result = self.tts.speak(response.text)

                result["tts"] = {
                    "success": tts_result["success"],
                    "duration": tts_result.get("duration_estimate", 0),
                }

            logger.info(
                f"Chat complete: lang={lang}, intent={nlp_result.intent}, "
                f"response={len(response.text)} chars"
            )

            return result

        except Exception as e:
            error_msg = f"Chat error: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            self._total_errors += 1
            return result

    def voice_chat(
        self,
        duration: float = 5.0,
        language: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record voice, transcribe, generate AI response, and speak it.

        This is the complete voice interaction pipeline:
        1. Record audio from microphone
        2. Transcribe via ASR
        3. Process through NLP
        4. Generate AI response
        5. Speak the response via TTS

        Args:
            duration: Maximum recording duration in seconds.
            language: Optional language override.
            voice: Optional voice override.

        Returns:
            Dictionary with complete interaction results.

        Example:
            >>> engine = VoiceEngine(language="id")
            >>> result = engine.voice_chat(duration=10)
            >>> if result["success"]:
            ...     print(f"You said: {result['user_text']}")
            ...     print(f"Robot said: {result['ai_text']}")
        """
        lang = language or self.language
        voice_id = voice or self.voice

        result = {
            "user_text": "",
            "ai_text": "",
            "nlp": None,
            "language": lang,
            "voice": voice_id,
            "success": False,
            "error": None,
            "asr": None,
            "tts": None,
        }

        self._total_queries += 1

        try:
            # Step 1: Record and transcribe
            logger.info(f"🎤 Listening... (language: {lang}, max {duration}s)")
            self.stt.set_language(lang)
            asr_result = self.stt.record_and_transcribe(duration=duration)
            result["asr"] = {
                "success": asr_result["success"],
                "transcription": asr_result.get("transcription", ""),
                "error": asr_result.get("error"),
            }

            if not asr_result["success"] or not asr_result.get("transcription", "").strip():
                result["error"] = asr_result.get("error", "No speech detected")
                return result

            transcription = asr_result["transcription"].strip()
            result["user_text"] = transcription

            logger.info(f"👤 You: {transcription}")

            # Step 2-5: Chat pipeline (NLP + AI + TTS)
            chat_result = self.chat(
                transcription,
                language=lang,
                voice=voice_id,
                speak=self.auto_speak,
            )

            result.update({
                "ai_text": chat_result["ai_text"],
                "nlp": chat_result["nlp"],
                "success": chat_result["success"],
                "error": chat_result.get("error"),
                "tts": chat_result.get("tts"),
            })

            return result

        except Exception as e:
            error_msg = f"Voice chat error: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            self._total_errors += 1
            return result

    def set_language(self, language: str) -> None:
        """
        Change the active language for all modules.

        This updates the language across all engine components:
        STT, NLP, Response Generator, and TTS.

        Args:
            language: Language code (e.g., 'id', 'en', 'ja').
        """
        if language not in self.LANGUAGES:
            logger.warning(f"Unsupported language: {language}")
            return

        self.language = language
        self.stt.set_language(language)
        self.nlp.default_language = language
        self.generator.set_language(language)
        self.tts.set_language(language)

        lang_name = self.LANGUAGES[language]
        logger.info(f"🌐 Language changed to: {language} ({lang_name})")

    def set_voice(self, voice: str) -> None:
        """
        Change the active voice personality.

        Args:
            voice: Voice ID ('tongtong', 'chuichui', etc.).
        """
        if voice not in self.VOICES:
            logger.warning(f"Unknown voice: {voice}")
            return

        self.voice = voice
        self.generator.set_voice(voice)
        self.tts.set_voice(voice)

        logger.info(f"🎙️ Voice changed to: {self.VOICES[voice]}")

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.generator.clear_history()
        logger.info("🗑️ Conversation history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Returns:
            Dictionary with stats including total queries,
            errors, duration, and history summary.
        """
        duration = (datetime.now() - self._conversation_start).total_seconds()
        history_summary = self.generator.get_history_summary()

        return {
            "total_queries": self._total_queries,
            "total_errors": self._total_errors,
            "success_rate": (
                (self._total_queries - self._total_errors) / max(self._total_queries, 1)
            ),
            "duration_seconds": duration,
            "language": self.language,
            "voice": self.voice,
            "history": history_summary,
        }

    def run_interactive(self) -> None:
        """
        Run the voice engine in interactive CLI mode.

        This starts a REPL-style interactive session where
        users can type messages or use voice input. Special
        commands are available for changing settings.

        Commands:
            /lang <code>    - Change language (e.g., /lang en)
            /voice <id>     - Change voice (e.g., /voice jam)
            /speak          - Toggle auto-speak
            /mic            - Use voice input
            /history        - Show conversation history
            /stats          - Show conversation statistics
            /clear          - Clear conversation history
            /help           - Show help message
            /quit           - Exit the engine

        Example:
            >>> engine = VoiceEngine(language="id")
            >>> engine.run_interactive()
        """
        lang_name = self.LANGUAGES.get(self.language, "?")
        voice_name = self.VOICES.get(self.voice, "?")

        print("\n" + "=" * 60)
        print("  🤖 Voice Robot - Interactive Mode")
        print("=" * 60)
        print(f"  Language: {self.language} ({lang_name})")
        print(f"  Voice:    {voice_name}")
        print(f"  Auto-speak: {'ON' if self.auto_speak else 'OFF'}")
        print("-" * 60)
        print("  Commands:")
        print("    /lang <code>   - Change language")
        print("    /voice <id>    - Change voice")
        print("    /speak         - Toggle auto-speak")
        print("    /mic           - Voice input mode")
        print("    /history       - Show history")
        print("    /stats         - Show statistics")
        print("    /clear         - Clear history")
        print("    /help          - Show help")
        print("    /quit          - Exit")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input(f"👤 [{self.language}] You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # Text chat
                result = self.chat(user_input)

                if result["success"]:
                    voice_label = self.VOICES.get(self.voice, self.voice)
                    print(f"🤖 {voice_label}: {result['ai_text']}\n")
                else:
                    print(f"❌ Error: {result['error']}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Sampai jumpa!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

    def _handle_command(self, command: str) -> None:
        """
        Handle interactive mode commands.

        Args:
            command: Command string starting with '/'.
        """
        parts = command.lower().split()
        cmd = parts[0]

        if cmd == "/quit" or cmd == "/exit":
            print("👋 Goodbye! Sampai jumpa!")
            sys.exit(0)

        elif cmd == "/lang" and len(parts) > 1:
            lang_code = parts[1]
            if lang_code in self.LANGUAGES:
                self.set_language(lang_code)
                print(f"🌐 Language: {lang_code} ({self.LANGUAGES[lang_code]})\n")
            else:
                print(f"❌ Unknown language: {lang_code}")
                print(f"   Available: {', '.join(self.LANGUAGES.keys())}\n")

        elif cmd == "/voice" and len(parts) > 1:
            voice_id = parts[1]
            if voice_id in self.VOICES:
                self.set_voice(voice_id)
                print(f"🎙️ Voice: {self.VOICES[voice_id]}\n")
            else:
                print(f"❌ Unknown voice: {voice_id}")
                print(f"   Available: {', '.join(self.VOICES.keys())}\n")

        elif cmd == "/speak":
            self.auto_speak = not self.auto_speak
            print(f"🔊 Auto-speak: {'ON' if self.auto_speak else 'OFF'}\n")

        elif cmd == "/mic":
            print("🎤 Listening... (speak now)")
            result = self.voice_chat(duration=10)
            if result["success"]:
                voice_label = self.VOICES.get(self.voice, self.voice)
                print(f"👤 You: {result['user_text']}")
                print(f"🤖 {voice_label}: {result['ai_text']}\n")
            else:
                print(f"❌ Error: {result.get('error', 'Voice input failed')}\n")

        elif cmd == "/history":
            history = self.generator.get_history()
            if not history:
                print("📭 No conversation history\n")
            else:
                print("📜 Conversation History:")
                for i, msg in enumerate(history):
                    role = "👤 You" if msg["role"] == "user" else "🤖 AI"
                    print(f"  {i+1}. {role}: {msg['content'][:80]}...")
                print()

        elif cmd == "/stats":
            stats = self.get_stats()
            print("📊 Statistics:")
            print(f"  Queries: {stats['total_queries']}")
            print(f"  Errors:  {stats['total_errors']}")
            print(f"  Success: {stats['success_rate']*100:.0f}%")
            print(f"  Duration: {stats['duration_seconds']:.0f}s")
            print()

        elif cmd == "/clear":
            self.clear_history()
            print("🗑️ History cleared\n")

        elif cmd == "/help":
            print("\n  Available commands:")
            print("    /lang <code>   - Change language")
            print("    /voice <id>    - Change voice")
            print("    /speak         - Toggle auto-speak")
            print("    /mic           - Voice input")
            print("    /history       - Show history")
            print("    /stats         - Statistics")
            print("    /clear         - Clear history")
            print("    /quit          - Exit")
            print()

        else:
            print(f"❓ Unknown command: {command}")
            print("   Type /help for available commands\n")

    @classmethod
    def list_languages(cls) -> None:
        """Print all supported languages."""
        print("\n🌐 Supported Languages (20):")
        print("-" * 40)
        for code, name in cls.LANGUAGES.items():
            print(f"  {code:>2}  {name}")
        print()

    @classmethod
    def list_voices(cls) -> None:
        """Print all available voice personalities."""
        print("\n🎙️ Voice Personalities (7):")
        print("-" * 40)
        for voice_id, description in cls.VOICES.items():
            print(f"  {voice_id:>10}  {description}")
        print()

    def __repr__(self) -> str:
        return (
            f"VoiceEngine(language='{self.language}', "
            f"voice='{self.voice}', "
            f"queries={self._total_queries})"
        )


def main():
    """CLI entry point for the Voice Engine."""
    parser = argparse.ArgumentParser(
        description="Voice Robot - Multilingual AI Voice Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m voice_engine.main --interactive --language id --voice tongtong
  python -m voice_engine.main --text "Hello, how are you?" --language en --voice jam
  python -m voice_engine.main --list-languages
  python -m voice_engine.main --list-voices
        """,
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Text message to send (single query mode)",
    )
    parser.add_argument(
        "--mic", "-m",
        action="store_true",
        help="Use voice input (microphone)",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="id",
        help="Language code (default: id)",
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="tongtong",
        help="Voice personality ID (default: tongtong)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:3000",
        help="Voice Robot API base URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="TTS speed multiplier 0.5-2.0 (default: 1.0)",
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=0.8,
        help="TTS volume 0.1-1.0 (default: 0.8)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="AI creativity 0.0-2.0 (default: 0.7)",
    )
    parser.add_argument(
        "--auto-speak",
        action="store_true",
        default=True,
        help="Auto-speak AI responses (default: True)",
    )
    parser.add_argument(
        "--no-speak",
        action="store_true",
        help="Disable auto-speak",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported languages and exit",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List all voice personalities and exit",
    )
    parser.add_argument(
        "--save-audio",
        type=str,
        default=None,
        help="Save TTS audio to file instead of playing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # List commands
    if args.list_languages:
        VoiceEngine.list_languages()
        return

    if args.list_voices:
        VoiceEngine.list_voices()
        return

    # Initialize engine
    auto_speak = args.auto_speak and not args.no_speak

    engine = VoiceEngine(
        language=args.language,
        voice=args.voice,
        base_url=args.base_url,
        auto_speak=auto_speak,
        speed=args.speed,
        volume=args.volume,
        temperature=args.temperature,
    )

    # Interactive mode
    if args.interactive:
        engine.run_interactive()
        return

    # Microphone mode
    if args.mic:
        print("🎤 Listening...")
        result = engine.voice_chat(duration=10)

        if result["success"]:
            print(f"\n👤 You: {result['user_text']}")
            print(f"🤖 AI:  {result['ai_text']}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Voice input failed')}")
        return

    # Text query mode
    if args.text:
        result = engine.chat(args.text)

        if result["success"]:
            voice_label = engine.VOICES.get(args.voice, args.voice)
            print(f"\n🤖 {voice_label}: {result['ai_text']}")

            # Save audio if requested
            if args.save_audio and result["ai_text"]:
                tts_result = engine.tts.save_to_file(
                    result["ai_text"], args.save_audio
                )
                if tts_result.get("success"):
                    print(f"💾 Audio saved to: {args.save_audio}")

            # Show NLP analysis if verbose
            if args.verbose and result.get("nlp"):
                nlp = result["nlp"]
                print(f"\n📊 NLP Analysis:")
                print(f"  Language: {nlp['detected_language']} ({nlp['language_confidence']:.2f})")
                print(f"  Intent: {nlp['intent']} ({nlp['intent_confidence']:.2f})")
                print(f"  Sentiment: {nlp['sentiment']} ({nlp['sentiment_score']:.2f})")
                print(f"  Keywords: {', '.join(nlp['keywords'])}")
                print(f"  Is Question: {nlp['is_question']}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Failed to generate response')}")
        return

    # No mode specified, show help
    parser.print_help()


if __name__ == "__main__":
    main()
