"""
Voice Engine - Multilingual AI Voice Robot Engine
====================================================
A Python engine for multilingual speech-to-text, NLP processing,
AI response generation, and text-to-speech synthesis.

Supports 20 languages:
    Indonesian, English, French, German, Arabic, Malay, Chinese,
    Japanese, Russian, Korean, Spanish, Portuguese, Italian, Thai,
    Vietnamese, Hindi, Turkish, Dutch, Polish, Swedish

Modules:
    speech_to_text  - Audio recording and transcription (ASR)
    nlp_engine      - Language detection, text processing, and intent analysis
    response_generator - AI-powered multilingual response generation
    text_to_speech  - Text-to-speech synthesis with multiple voices
    main            - Orchestrator that ties everything together

Usage:
    from voice_engine import VoiceEngine

    engine = VoiceEngine(language="id", voice="tongtong")
    engine.run()
"""

__version__ = "1.0.0"
__author__ = "Voice Robot Team"
