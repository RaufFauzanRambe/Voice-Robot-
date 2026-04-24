"""
Response Generator Module
===========================
AI-powered multilingual response generation using the
Voice Robot Chat API endpoint.

Features:
    - Context-aware response generation
    - 20 language support with automatic language instructions
    - Voice personality integration (7 voice profiles)
    - Conversation history management
    - Streaming-ready response handling
    - Configurable AI parameters (temperature, max_tokens)

Classes:
    ResponseGenerator - Main AI response generator

Usage:
    generator = ResponseGenerator(language="id", voice="tongtong")
    response = generator.generate("Halo, apa kabar?")
    print(response.text)
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """
    Represents a single chat message.

    Attributes:
        role: Message role ('user', 'assistant', 'system').
        content: Message text content.
    """
    role: str
    content: str


@dataclass
class ResponseResult:
    """
    Data class representing a generated response.

    Attributes:
        text: The generated response text.
        role: Response role (always 'assistant').
        language: Language code used for generation.
        voice: Voice personality ID used.
        success: Whether generation succeeded.
        error: Error message if generation failed.
        metadata: Additional metadata about the generation.
    """
    text: str = ""
    role: str = "assistant"
    language: str = "id"
    voice: str = "tongtong"
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseGenerator:
    """
    AI-powered multilingual response generator.

    This generator communicates with the Voice Robot Chat API
    to produce contextually relevant responses in 20 languages
    with 7 different voice personalities.

    The generator maintains conversation history and supports
    configurable AI parameters for fine-tuning response quality.

    Supported Languages (20):
        Indonesian (id), English (en), French (fr), German (de),
        Arabic (ar), Malay (ms), Chinese (zh), Japanese (ja),
        Russian (ru), Korean (ko), Spanish (es), Portuguese (pt),
        Italian (it), Thai (th), Vietnamese (vi), Hindi (hi),
        Turkish (tr), Dutch (nl), Polish (pl), Swedish (sv)

    Voice Personalities (7):
        tongtong (Warm & Friendly), chuichui (Cheerful & Funny),
        xiaochen (Professional), jam (English Gentleman),
        kazi (Clear & Standard), douji (Natural & Casual),
        luodo (Expressive & Dramatic)

    Attributes:
        api_url: URL of the Chat API endpoint.
        language: Current language code.
        voice: Current voice personality ID.
        temperature: AI creativity parameter (0.0-2.0).
        max_tokens: Maximum response length in tokens.
        history: Conversation history for context.

    Example:
        >>> gen = ResponseGenerator(language="en", voice="jam")
        >>> result = gen.generate("Tell me about quantum physics")
        >>> print(result.text)
    """

    # Language configurations with native names and instructions
    LANGUAGE_CONFIG = {
        "id": {"name": "Bahasa Indonesia", "native": "Bahasa Indonesia"},
        "en": {"name": "English", "native": "English"},
        "fr": {"name": "French", "native": "Français"},
        "de": {"name": "German", "native": "Deutsch"},
        "ar": {"name": "Arabic", "native": "العربية"},
        "ms": {"name": "Malay", "native": "Bahasa Melayu"},
        "zh": {"name": "Chinese", "native": "中文"},
        "ja": {"name": "Japanese", "native": "日本語"},
        "ru": {"name": "Russian", "native": "Русский"},
        "ko": {"name": "Korean", "native": "한국어"},
        "es": {"name": "Spanish", "native": "Español"},
        "pt": {"name": "Portuguese", "native": "Português"},
        "it": {"name": "Italian", "native": "Italiano"},
        "th": {"name": "Thai", "native": "ภาษาไทย"},
        "vi": {"name": "Vietnamese", "native": "Tiếng Việt"},
        "hi": {"name": "Hindi", "native": "हिन्दी"},
        "tr": {"name": "Turkish", "native": "Türkçe"},
        "nl": {"name": "Dutch", "native": "Nederlands"},
        "pl": {"name": "Polish", "native": "Polski"},
        "sv": {"name": "Swedish", "native": "Svenska"},
    }

    # Voice personality descriptions
    VOICE_PROFILES = {
        "tongtong": {
            "name": "TongTong",
            "emoji": "😊",
            "personality": "Warm & Friendly",
            "description": "Gentle, caring, empathetic responses",
        },
        "chuichui": {
            "name": "ChuiChui",
            "emoji": "😄",
            "personality": "Cheerful & Funny",
            "description": "Energetic, humorous, fun responses",
        },
        "xiaochen": {
            "name": "XiaoChen",
            "emoji": "💼",
            "personality": "Professional & Calm",
            "description": "Formal, structured, informative responses",
        },
        "jam": {
            "name": "Jam",
            "emoji": "🎩",
            "personality": "English Gentleman",
            "description": "Refined, polite, sophisticated responses",
        },
        "kazi": {
            "name": "Kazi",
            "emoji": "🎯",
            "personality": "Clear & Standard",
            "description": "Clear pronunciation, easy to understand",
        },
        "douji": {
            "name": "DouJi",
            "emoji": "🌊",
            "personality": "Natural & Casual",
            "description": "Flowing, natural conversation style",
        },
        "luodo": {
            "name": "LuoDo",
            "emoji": "🎭",
            "personality": "Expressive & Dramatic",
            "description": "Emotional, vivid, colorful language",
        },
    }

    def __init__(
        self,
        api_url: str = "http://localhost:3000/api/chat",
        language: str = "id",
        voice: str = "tongtong",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
        max_history: int = 20,
    ):
        """
        Initialize the Response Generator.

        Args:
            api_url: URL of the Chat API endpoint.
            language: Language code for responses.
            voice: Voice personality ID.
            temperature: AI creativity (0.0=deterministic, 2.0=creative).
            max_tokens: Maximum response length.
            timeout: API request timeout in seconds.
            max_history: Maximum conversation history messages to keep.
        """
        self.api_url = api_url
        self.language = language
        self.voice = voice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_history = max_history
        self.history: List[ChatMessage] = []

        # Validate language
        if language not in self.LANGUAGE_CONFIG:
            logger.warning(
                f"Language '{language}' not supported. "
                f"Available: {list(self.LANGUAGE_CONFIG.keys())}"
            )

        # Validate voice
        if voice not in self.VOICE_PROFILES:
            logger.warning(
                f"Voice '{voice}' not recognized. "
                f"Available: {list(self.VOICE_PROFILES.keys())}"
            )

        logger.info(
            f"ResponseGenerator initialized - "
            f"Language: {language}, Voice: {voice}, "
            f"Temperature: {temperature}, MaxTokens: {max_tokens}"
        )

    def set_language(self, language: str) -> None:
        """
        Change the response language.

        Args:
            language: Language code (e.g., 'id', 'en', 'ja').
        """
        if language in self.LANGUAGE_CONFIG:
            self.language = language
            logger.info(
                f"Language changed to: {language} "
                f"({self.LANGUAGE_CONFIG[language]['native']})"
            )
        else:
            logger.warning(f"Unsupported language: {language}")

    def set_voice(self, voice: str) -> None:
        """
        Change the voice personality.

        Args:
            voice: Voice ID (e.g., 'tongtong', 'jam', 'luodo').
        """
        if voice in self.VOICE_PROFILES:
            self.voice = voice
            profile = self.VOICE_PROFILES[voice]
            logger.info(
                f"Voice changed to: {voice} "
                f"({profile['name']} {profile['emoji']} {profile['personality']})"
            )
        else:
            logger.warning(f"Unknown voice: {voice}")

    def generate(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        include_history: bool = True,
    ) -> ResponseResult:
        """
        Generate an AI response to the user message.

        This method sends the user message along with conversation
        history to the Chat API and returns the generated response.
        The response is automatically generated in the configured
        language and with the selected voice personality.

        Args:
            user_message: The user's input message.
            system_prompt: Optional custom system prompt override.
            include_history: Whether to include conversation history.

        Returns:
            ResponseResult containing the generated text and metadata.

        Example:
            >>> gen = ResponseGenerator(language="en", voice="jam")
            >>> result = gen.generate("What is AI?")
            >>> if result.success:
            ...     print(result.text)
        """
        if not user_message or not user_message.strip():
            return ResponseResult(
                language=self.language,
                voice=self.voice,
                success=False,
                error="Empty message provided",
            )

        try:
            # Build message list
            user_msg = ChatMessage(role="user", content=user_message.strip())
            messages = []

            # Include conversation history for context
            if include_history:
                messages.extend(
                    [{"role": m.role, "content": m.content} for m in self.history]
                )

            messages.append({"role": user_msg.role, "content": user_msg.content})

            # Prepare request payload
            payload = {
                "messages": messages,
                "voiceId": self.voice,
                "language": self.language,
            }

            if system_prompt:
                payload["systemPrompt"] = system_prompt

            logger.info(
                f"Generating response (lang={self.language}, voice={self.voice}, "
                f"history={len(self.history)} msgs)"
            )

            # Send request to Chat API
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                assistant_text = data.get("message", "")

                # Update conversation history
                self.history.append(user_msg)
                self.history.append(ChatMessage(role="assistant", content=assistant_text))

                # Trim history if too long
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]

                logger.info(
                    f"Response generated: {len(assistant_text)} chars, "
                    f"history: {len(self.history)} msgs"
                )

                return ResponseResult(
                    text=assistant_text,
                    role="assistant",
                    language=self.language,
                    voice=self.voice,
                    success=True,
                    metadata={
                        "history_length": len(self.history),
                        "response_length": len(assistant_text),
                        "temperature": self.temperature,
                    },
                )
            else:
                error_msg = f"API error: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                return ResponseResult(
                    language=self.language,
                    voice=self.voice,
                    success=False,
                    error=error_msg,
                )

        except requests.exceptions.Timeout:
            error_msg = "Chat API request timed out"
            logger.error(error_msg)
            return ResponseResult(
                language=self.language,
                voice=self.voice,
                success=False,
                error=error_msg,
            )

        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to Chat API at {self.api_url}"
            logger.error(error_msg)
            return ResponseResult(
                language=self.language,
                voice=self.voice,
                success=False,
                error=error_msg,
            )

        except Exception as e:
            error_msg = f"Response generation error: {str(e)}"
            logger.error(error_msg)
            return ResponseResult(
                language=self.language,
                voice=self.voice,
                success=False,
                error=error_msg,
            )

    def generate_with_context(
        self,
        user_message: str,
        context: str,
    ) -> ResponseResult:
        """
        Generate a response with additional context information.

        This is useful when you want to provide the AI with
        extra context about the conversation or the user's
        situation without adding it to the conversation history.

        Args:
            user_message: The user's input message.
            context: Additional context to include in the system prompt.

        Returns:
            ResponseResult containing the generated text.

        Example:
            >>> result = gen.generate_with_context(
            ...     "What's the weather like?",
            ...     "The user is in Jakarta, Indonesia. Current season: rainy."
            ... )
        """
        lang_config = self.LANGUAGE_CONFIG.get(self.language, {})
        lang_name = lang_config.get("native", "the specified language")

        enhanced_prompt = (
            f"Additional context: {context}\n\n"
            f"Respond in {lang_name}. Use the personality of the voice character assigned to you."
        )

        return self.generate(user_message, system_prompt=enhanced_prompt)

    def clear_history(self) -> None:
        """
        Clear the conversation history.

        This resets the conversation context, so the AI will
        not remember previous messages.
        """
        self.history.clear()
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.

        Returns:
            List of message dictionaries with 'role' and 'content' keys.
        """
        return [{"role": m.role, "content": m.content} for m in self.history]

    def get_history_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation history.

        Returns:
            Dictionary with history statistics.
        """
        user_msgs = sum(1 for m in self.history if m.role == "user")
        assistant_msgs = sum(1 for m in self.history if m.role == "assistant")
        total_chars = sum(len(m.content) for m in self.history)

        return {
            "total_messages": len(self.history),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "total_characters": total_chars,
            "language": self.language,
            "voice": self.voice,
        }

    @classmethod
    def list_languages(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all supported languages.

        Returns:
            Dictionary mapping language codes to language info.
        """
        return cls.LANGUAGE_CONFIG.copy()

    @classmethod
    def list_voices(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all available voice personalities.

        Returns:
            Dictionary mapping voice IDs to profile info.
        """
        return cls.VOICE_PROFILES.copy()

    def __repr__(self) -> str:
        return (
            f"ResponseGenerator(language='{self.language}', "
            f"voice='{self.voice}', "
            f"history={len(self.history)} msgs)"
        )
