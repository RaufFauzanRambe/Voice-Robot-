"""
NLP Engine Module
==================
Provides natural language processing capabilities including
language detection, text analysis, intent classification,
sentiment analysis, and entity extraction.

Features:
    - Automatic language detection for 20 languages
    - Intent classification (greeting, question, command, etc.)
    - Sentiment analysis (positive, negative, neutral)
    - Text preprocessing and normalization
    - Keyword extraction
    - Conversation context management

Classes:
    NLPEngine - Main NLP processing engine

Usage:
    nlp = NLPEngine()
    result = nlp.process("Halo, apa kabar?")
    print(result.language)     # 'id'
    print(result.intent)       # 'greeting'
    print(result.sentiment)    # 'positive'
"""

import re
import unicodedata
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class NLPResult:
    """
    Data class representing the result of NLP processing.

    Attributes:
        original_text: The original input text.
        cleaned_text: Preprocessed and cleaned text.
        detected_language: ISO 639-1 language code.
        language_confidence: Confidence score for language detection (0.0-1.0).
        intent: Detected intent category.
        intent_confidence: Confidence score for intent detection (0.0-1.0).
        sentiment: Sentiment category ('positive', 'negative', 'neutral').
        sentiment_score: Sentiment score (-1.0 to 1.0).
        keywords: List of extracted keywords.
        entities: Dictionary of detected entities.
        is_question: Whether the text is a question.
        word_count: Number of words in the text.
    """
    original_text: str = ""
    cleaned_text: str = ""
    detected_language: str = "id"
    language_confidence: float = 0.0
    intent: str = "unknown"
    intent_confidence: float = 0.0
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    is_question: bool = False
    word_count: int = 0


class NLPEngine:
    """
    Natural Language Processing engine for multilingual text analysis.

    This engine provides comprehensive text analysis including language
    detection, intent classification, sentiment analysis, keyword
    extraction, and entity detection. It supports 20 languages and
    uses heuristic-based approaches for fast local processing
    without requiring external API calls.

    Attributes:
        supported_languages: Dictionary of supported language codes and names.
        language_keywords: Language-specific keyword patterns for detection.
        intent_patterns: Patterns for intent classification.
        sentiment_words: Language-specific sentiment word lists.

    Example:
        >>> nlp = NLPEngine()
        >>> result = nlp.process("Bonjour, comment allez-vous?")
        >>> print(result.detected_language)  # 'fr'
        >>> print(result.intent)             # 'greeting'
    """

    # Supported languages with their characteristics
    SUPPORTED_LANGUAGES = {
        "id": {"name": "Bahasa Indonesia", "script": "Latin"},
        "en": {"name": "English", "script": "Latin"},
        "fr": {"name": "Français", "script": "Latin"},
        "de": {"name": "Deutsch", "script": "Latin"},
        "ar": {"name": "العربية", "script": "Arabic"},
        "ms": {"name": "Bahasa Melayu", "script": "Latin"},
        "zh": {"name": "中文", "script": "CJK"},
        "ja": {"name": "日本語", "script": "CJK"},
        "ru": {"name": "Русский", "script": "Cyrillic"},
        "ko": {"name": "한국어", "script": "Hangul"},
        "es": {"name": "Español", "script": "Latin"},
        "pt": {"name": "Português", "script": "Latin"},
        "it": {"name": "Italiano", "script": "Latin"},
        "th": {"name": "ภาษาไทย", "script": "Thai"},
        "vi": {"name": "Tiếng Việt", "script": "Latin"},
        "hi": {"name": "हिन्दी", "script": "Devanagari"},
        "tr": {"name": "Türkçe", "script": "Latin"},
        "nl": {"name": "Nederlands", "script": "Latin"},
        "pl": {"name": "Polski", "script": "Latin"},
        "sv": {"name": "Svenska", "script": "Latin"},
    }

    # Language detection patterns based on unique characters/scripts
    SCRIPT_PATTERNS = {
        "ar": re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"),
        "zh": re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]"),
        "ja": re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"),
        "ko": re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]"),
        "th": re.compile(r"[\u0E00-\u0E7F]"),
        "hi": re.compile(r"[\u0900-\u097F]"),
        "ru": re.compile(r"[\u0400-\u04FF]"),
    }

    # Language-specific common words for detection
    LANGUAGE_MARKER_WORDS = {
        "id": {
            "saya", "aku", "kamu", "anda", "ini", "itu", "yang", "dengan",
            "untuk", "pada", "dari", "ke", "di", "adalah", "akan", "tidak",
            "bisa", "apa", "bagaimana", "kapan", "dimana", "kenapa", "siapa",
            "terima", "kasih", "halo", "selamat", "pagi", "siang", "sore",
            "malam", "tolong", "bantuan", "maaf", "iya", "ya", "tidak",
        },
        "en": {
            "the", "is", "are", "was", "were", "have", "has", "had", "will",
            "would", "could", "should", "can", "may", "might", "hello", "hi",
            "please", "thank", "sorry", "what", "where", "when", "how", "why",
            "who", "which", "this", "that", "with", "from", "for", "about",
            "you", "your", "they", "their", "them", "she", "her", "him",
        },
        "fr": {
            "le", "la", "les", "un", "une", "des", "de", "du", "et", "est",
            "sont", "avoir", "etre", "je", "tu", "il", "elle", "nous", "vous",
            "bonjour", "merci", "s'il", "plaît", "comment", "pourquoi", "oui",
            "non", "avec", "pour", "dans", "sur", "pas", "plus", "très",
        },
        "de": {
            "der", "die", "das", "ein", "eine", "und", "ist", "sind", "haben",
            "ich", "du", "er", "sie", "wir", "ihr", "Sie", "mit", "für",
            "auf", "nicht", "ja", "nein", "bitte", "danke", "hallo", "wie",
            "was", "wo", "wann", "warum", "wer", "kann", "werden", "auch",
        },
        "ms": {
            "saya", "awak", "kita", "dia", "mereka", "ini", "itu", "yang",
            "dengan", "untuk", "pada", "dari", "ke", "di", "adalah", "akan",
            "tidak", "boleh", "apa", "bagaimana", "bila", "mana", "kenapa",
            "terima", "kasih", "halo", "selamat", "pagi", "petang", "malam",
        },
        "es": {
            "el", "la", "los", "las", "un", "una", "y", "es", "son", "estar",
            "hola", "gracias", "por", "para", "con", "sin", "no", "sí",
            "qué", "cómo", "dónde", "cuándo", "por qué", "quién", "mucho",
            "poco", "bien", "mal", "también", "pero", "más", "muy",
        },
        "pt": {
            "o", "a", "os", "as", "um", "uma", "e", "é", "são", "estar",
            "olá", "obrigado", "obrigada", "por", "para", "com", "sem",
            "não", "sim", "que", "como", "onde", "quando", "porque", "quem",
            "muito", "pouco", "bem", "mal", "também", "mas", "mais",
        },
        "it": {
            "il", "lo", "la", "i", "gli", "le", "un", "una", "e", "è",
            "ciao", "grazie", "per", "con", "senza", "non", "sì", "che",
            "come", "dove", "quando", "perché", "chi", "molto", "poco",
            "bene", "male", "anche", "ma", "più", "questo", "quello",
        },
        "nl": {
            "de", "het", "een", "en", "is", "zijn", "heb", "heeft", "ik",
            "jij", "hij", "zij", "wij", "met", "voor", "op", "aan", "niet",
            "ja", "nee", "alstublieft", "dank", "hallo", "hoe", "wat", "waar",
            "wanneer", "waarom", "wie", "kan", "ook", "maar", "meer", "zeer",
        },
        "pl": {
            "i", "w", "na", "z", "do", "nie", "tak", "jest", "są", "być",
            "cześć", "dziękuję", "proszę", "przepraszam", "co", "jak", "gdzie",
            "kiedy", "dlaczego", "kto", "może", "ale", "też", "bardzo",
        },
        "sv": {
            "och", "att", "det", "den", "en", "ett", "är", "var", "har",
            "hej", "tack", "snälla", "ursäkta", "vad", "hur", "var", "när",
            "varför", "vem", "kan", "inte", "också", "men", "mycket", "bra",
        },
        "tr": {
            "ve", "bir", "bu", "şu", "da", "de", "ile", "için", "mi", "mı",
            "merhaba", "teşekkür", "lütfen", "affedersiniz", "ne", "nasıl",
            "nerede", "ne zaman", "neden", "kim", "olabilir", "ama", "çok",
        },
        "vi": {
            "và", "là", "có", "không", "được", "này", "đó", "với", "cho",
            "xin", "chào", "cảm", "ơn", "làm", "gì", "như", "thế", "nào",
            "ở", "đâu", "khi", "nào", "tại", "sao", "ai", "nhưng", "rất",
        },
        "ru": {
            "и", "в", "на", "с", "не", "это", "как", "но", "он", "она",
            "привет", "спасибо", "пожалуйста", "извините", "что", "где",
            "когда", "почему", "кто", "может", "очень", "тоже", "но",
        },
    }

    # Intent classification patterns (multilingual)
    INTENT_PATTERNS = {
        "greeting": {
            "id": [r"\b(halo|hallo|hai|hi|selamat|assalamualaikum|salam)\b"],
            "en": [r"\b(hello|hi|hey|greetings|good\s*(morning|afternoon|evening))\b"],
            "fr": [r"\b(bonjour|salut|bonsoir|coucou)\b"],
            "de": [r"\b(hallo|guten\s*(morgen|tag|abend)|grüß\s*gott)\b"],
            "ar": [r"مرحبا|السلام\s*عليكم|أهلا"],
            "ms": [r"\b(helo|halo|selamat|apa\s*khabar)\b"],
            "zh": [r"你好|您好|早上好|晚上好"],
            "ja": [r"こんにちは|おはよう|こんばんは|やあ"],
            "ru": [r"привет|здравствуйте|добр"],
            "ko": [r"안녕|반갑"],
            "es": [r"\b(hola|buenos\s*días|buenas)\b"],
            "pt": [r"\b(olá|oi|bom\s*dia|boa\s*tarde|boa\s*noite)\b"],
            "it": [r"\b(ciao|buongiorno|buonasera|salve)\b"],
        },
        "farewell": {
            "id": [r"\b(sampai\s*jumpa|dadah|bye|selamat\s*tidur|pamit)\b"],
            "en": [r"\b(bye|goodbye|farewell|good\s*night|see\s*you)\b"],
            "fr": [r"\b(au\s*revoir|adieu|bonne\s*nuit|à\s*bientôt)\b"],
            "de": [r"\b(auf\s*wiedersehen|tschüss|gute\s*nacht|bis\s*bald)\b"],
            "ar": [r"مع\s*السلامة|وداعا"],
            "ms": [r"\b(selamat\s*tinggal|jumpa\s*lagi|bye)\b"],
            "zh": [r"再见|拜拜|晚安"],
            "ja": [r"さようなら|おやすみ|またね"],
            "ru": [r"до\s*свидания|пока|спокойной"],
            "ko": [r"안녕히|잘\s*가"],
            "es": [r"\b(adiós|hasta\s*luego|buenas\s*noches)\b"],
            "pt": [r"\b(tchau|adeus|até|boa\s*noite)\b"],
            "it": [r"\b(arrivederci|ciao|buonanotte|a\s*presto)\b"],
        },
        "question": {
            "id": [r"\b(apa|bagaimana|mengapa|kenapa|kapan|dimana|siapa|berapa)\b", r"\?"],
            "en": [r"\b(what|how|why|when|where|who|which|how\s*much|how\s*many)\b", r"\?"],
            "fr": [r"\b(quoi|comment|pourquoi|quand|où|qui|combien)\b", r"\?"],
            "de": [r"\b(was|wie|warum|wann|wo|wer|welche|wie\s*viel)\b", r"\?"],
            "ar": [r"ماذا|كيف|لماذا|متى|أين|من|كم", r"؟"],
            "ms": [r"\b(apa|bagaimana|mengapa|bila|mana|siapa|berapa)\b", r"\?"],
            "zh": [r"什么|怎么|为什么|何时|哪里|谁|多少", r"？"],
            "ja": [r"何|どう|なぜ|いつ|どこ|誰|いくら", r"？"],
            "ru": [r"что|как|почему|когда|где|кто|сколько", r"\?"],
            "ko": [r"무엇|어떻게|왜|언제|어디|누구|얼마", r"\?"],
        },
        "command": {
            "id": [r"\b(tolong|bantu|buat|cari|ceritakan|jelaskan|berikan|tunjukkan)\b"],
            "en": [r"\b(please|help|make|find|tell|explain|give|show|do|create)\b"],
            "fr": [r"\b(s'il\s*vous\s*plaît|aidez|faites|cherchez|racontez|expliquez)\b"],
            "de": [r"\b(bitte|hilfe|mach|finde|erzähl|erklär|zeig)\b"],
            "ar": [r"من\s*فضلك|ساعد|افعل|ابحث|احك|اشرح"],
            "ms": [r"\b(tolong|bantu|buat|cari|ceritakan|jelaskan)\b"],
            "zh": [r"请|帮|做|找|告诉|解释|给|显示"],
            "ja": [r"ください|して|探して|教えて|説明して"],
            "ru": [r"пожалуйста|помоги|сделай|найди|расскажи|объясни"],
            "ko": [r"주세요|도와|만들|찾아|알려|설명"],
        },
        "thanks": {
            "id": [r"\b(terima\s*kasih|maksih|makasih|thanks|thank\s*you)\b"],
            "en": [r"\b(thanks?|thank\s*you|appreciate|grateful)\b"],
            "fr": [r"\b(merci|remercie|gratitude)\b"],
            "de": [r"\b(danke|dankeschön|vielen\s*dank)\b"],
            "ar": [r"شكرا|مشكور"],
            "ms": [r"\b(terima\s*kasih|thanks|thank\s*you)\b"],
            "zh": [r"谢谢|感谢|多谢"],
            "ja": [r"ありがとう|感謝"],
            "ru": [r"спасибо|благодар"],
            "ko": [r"감사|고마워"],
        },
        "joke_request": {
            "id": [r"\b(lelucon|lucu|humor|joke|ketawa|bercanda|lawak)\b"],
            "en": [r"\b(joke|funny|humor|laugh|make\s*me\s*laugh)\b"],
            "fr": [r"\b(blague|drôle|humour|rire|plaisanterie)\b"],
            "de": [r"\b(witz|lustig|humor|lachen)\b"],
            "ar": [r"نكتة|مضحك|فكاهة"],
            "ms": [r"\b(lawak|lucu|jenaka|kelakar)\b"],
            "zh": [r"笑话|搞笑|幽默"],
            "ja": [r"冗談|面白い|笑わせ"],
            "ru": [r"шутк|смешн|юмор|анекдот"],
            "ko": [r"농담|웃기|유머"],
        },
    }

    # Sentiment words (multilingual)
    SENTIMENT_WORDS = {
        "positive": {
            "id": {"senang", "gembira", "bahagia", "bagus", "baik", "hebat", "luar biasa",
                   "indah", "cantik", "keren", "mantap", "suka", "cinta", "sayang",
                   "terima kasih", "puas", "menyenangkan", "menakjubkan", "sempurna"},
            "en": {"happy", "glad", "great", "good", "wonderful", "amazing", "love",
                   "excellent", "fantastic", "beautiful", "awesome", "perfect", "like",
                   "enjoy", "thank", "appreciate", "best", "brilliant", "nice"},
            "fr": {"heureux", "content", "bien", "bon", "merveilleux", "super", "amour",
                   "excellent", "beau", "magnifique", "parfait", "merci", "bravo"},
            "de": {"glücklich", "froh", "gut", "wunderbar", "toll", "liebe", "schön",
                   "perfekt", "danke", "ausgezeichnet", "großartig", "prima"},
        },
        "negative": {
            "id": {"sedih", "marah", "kecewa", "buruk", "jelek", "benci", "takut",
                   "khawatir", "cemas", "bosan", "lelah", "sakit", "susah", "sulit",
                   "gagal", "salah", "parah", "mengerikan", "menyedihkan"},
            "en": {"sad", "angry", "disappointed", "bad", "ugly", "hate", "fear",
                   "worried", "anxious", "bored", "tired", "pain", "difficult", "fail",
                   "wrong", "terrible", "awful", "horrible", "worse", "worst"},
            "fr": {"triste", "en colère", "déçu", "mauvais", "laid", "haine", "peur",
                   "inquiet", "ennuyé", "fatigué", "douleur", "difficile", "échouer"},
            "de": {"traurig", "wütend", "enttäuscht", "schlecht", "hässlich", "hass",
                   "angst", "besorgt", "gelangweilt", "müde", "schmerz", "schwierig"},
        },
    }

    # Stop words for keyword extraction (multilingual)
    STOP_WORDS = {
        "id": {"yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
               "pada", "adalah", "akan", "tidak", "saya", "kamu", "dia", "mereka",
               "kita", "atau", "juga", "sudah", "belum", "lagi", "hanya", "seperti"},
        "en": {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
               "have", "has", "had", "do", "does", "did", "will", "would", "could",
               "should", "may", "might", "shall", "can", "it", "its", "this", "that",
               "these", "those", "i", "you", "he", "she", "we", "they", "me", "him",
               "her", "us", "them", "my", "your", "his", "our", "their", "and", "or",
               "but", "in", "on", "at", "to", "for", "with", "from", "by", "of"},
    }

    def __init__(self, default_language: str = "id"):
        """
        Initialize the NLP Engine.

        Args:
            default_language: Default language code when detection is uncertain.
        """
        self.default_language = default_language
        logger.info(f"NLPEngine initialized (default language: {default_language})")

    def process(self, text: str, language_hint: Optional[str] = None) -> NLPResult:
        """
        Process text through the full NLP pipeline.

        This method runs the text through all processing stages:
        1. Text preprocessing and cleaning
        2. Language detection
        3. Intent classification
        4. Sentiment analysis
        5. Keyword extraction
        6. Question detection
        7. Entity extraction

        Args:
            text: Input text to process.
            language_hint: Optional language hint to improve detection.

        Returns:
            NLPResult object with all analysis results.

        Example:
            >>> nlp = NLPEngine()
            >>> result = nlp.process("Bonjour, comment allez-vous?")
            >>> print(result.detected_language)  # 'fr'
            >>> print(result.intent)             # 'greeting'
        """
        if not text or not text.strip():
            return NLPResult()

        # Step 1: Preprocess text
        cleaned_text = self.preprocess_text(text)

        # Step 2: Detect language
        detected_lang, lang_confidence = self.detect_language(cleaned_text, language_hint)

        # Step 3: Classify intent
        intent, intent_conf = self.classify_intent(cleaned_text, detected_lang)

        # Step 4: Analyze sentiment
        sentiment, sentiment_score = self.analyze_sentiment(cleaned_text, detected_lang)

        # Step 5: Extract keywords
        keywords = self.extract_keywords(cleaned_text, detected_lang)

        # Step 6: Detect question
        is_question = self.is_question(cleaned_text, detected_lang)

        # Step 7: Extract entities
        entities = self.extract_entities(cleaned_text)

        # Count words
        word_count = len(cleaned_text.split())

        result = NLPResult(
            original_text=text,
            cleaned_text=cleaned_text,
            detected_language=detected_lang,
            language_confidence=lang_confidence,
            intent=intent,
            intent_confidence=intent_conf,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            keywords=keywords,
            entities=entities,
            is_question=is_question,
            word_count=word_count,
        )

        logger.debug(
            f"NLP Result: lang={detected_lang}({lang_confidence:.2f}), "
            f"intent={intent}({intent_conf:.2f}), "
            f"sentiment={sentiment}({sentiment_score:.2f})"
        )

        return result

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess and clean text for analysis.

        Performs the following cleaning steps:
        1. Unicode normalization (NFC)
        2. Remove control characters
        3. Normalize whitespace
        4. Strip leading/trailing whitespace

        Args:
            text: Raw input text.

        Returns:
            Cleaned text string.

        Example:
            >>> nlp.preprocess_text("  Halo   apa   kabar?  ")
            'Halo apa kabar?'
        """
        # Normalize unicode
        text = unicodedata.normalize("NFC", text)

        # Remove control characters but keep newlines
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip
        text = text.strip()

        return text

    def detect_language(
        self, text: str, hint: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Detect the language of the input text.

        Uses a multi-strategy approach:
        1. Script-based detection (Arabic, CJK, Cyrillic, etc.)
        2. Marker word frequency analysis
        3. Language hint if provided

        Args:
            text: Text to analyze.
            hint: Optional language hint code.

        Returns:
            Tuple of (language_code, confidence_score).

        Example:
            >>> nlp.detect_language("Hello, how are you?")
            ('en', 0.85)
        """
        if not text:
            return (hint or self.default_language, 0.0)

        scores: Dict[str, float] = {}

        # Strategy 1: Script-based detection
        for lang_code, pattern in self.SCRIPT_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                ratio = len("".join(matches)) / max(len(text), 1)
                scores[lang_code] = ratio * 0.9  # High confidence for script

        # Strategy 2: Marker word frequency
        text_lower = text.lower()
        words = set(re.findall(r"\b\w+\b", text_lower))

        for lang_code, marker_words in self.LANGUAGE_MARKER_WORDS.items():
            overlap = len(words & marker_words)
            if overlap > 0:
                ratio = overlap / max(len(words), 1)
                current_score = scores.get(lang_code, 0.0)
                scores[lang_code] = current_score + ratio * 0.7

        # Apply hint with moderate confidence
        if hint and hint in self.SUPPORTED_LANGUAGES:
            scores[hint] = scores.get(hint, 0.0) + 0.3

        if not scores:
            return (hint or self.default_language, 0.1)

        # Get top language
        best_lang = max(scores, key=scores.get)
        confidence = min(scores[best_lang], 1.0)

        # If confidence is very low, use hint or default
        if confidence < 0.1 and hint:
            return (hint, 0.2)

        return (best_lang, confidence)

    def classify_intent(self, text: str, language: str) -> Tuple[str, float]:
        """
        Classify the intent of the input text.

        Detects intents such as greeting, farewell, question,
        command, thanks, and joke_request using language-specific
        pattern matching.

        Args:
            text: Text to classify.
            language: Language code for pattern selection.

        Returns:
            Tuple of (intent_name, confidence_score).

        Example:
            >>> nlp.classify_intent("Hello there!", "en")
            ('greeting', 0.9)
        """
        if not text:
            return ("unknown", 0.0)

        text_lower = text.lower()
        intent_scores: Dict[str, float] = {}

        for intent_name, lang_patterns in self.INTENT_PATTERNS.items():
            # Get patterns for the detected language, fallback to English
            patterns = lang_patterns.get(language, lang_patterns.get("en", []))

            for pattern in patterns:
                try:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        intent_scores[intent_name] = max(
                            intent_scores.get(intent_name, 0.0),
                            min(0.5 + len(matches) * 0.2, 1.0),
                        )
                except re.error:
                    continue

        if not intent_scores:
            # Check if it's a question by punctuation
            if "?" in text or "？" in text or "؟" in text:
                return ("question", 0.4)
            return ("general", 0.3)

        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]

        return (best_intent, confidence)

    def analyze_sentiment(self, text: str, language: str) -> Tuple[str, float]:
        """
        Analyze the sentiment of the input text.

        Uses language-specific positive/negative word lists
        to determine the overall sentiment.

        Args:
            text: Text to analyze.
            language: Language code for word list selection.

        Returns:
            Tuple of (sentiment_category, sentiment_score).
            sentiment_category: 'positive', 'negative', or 'neutral'.
            sentiment_score: Float from -1.0 (negative) to 1.0 (positive).

        Example:
            >>> nlp.analyze_sentiment("I am very happy today!", "en")
            ('positive', 0.6)
        """
        if not text:
            return ("neutral", 0.0)

        text_lower = text.lower()
        words = set(re.findall(r"\b\w+\b", text_lower))

        positive_count = 0
        negative_count = 0

        for sentiment_type in ("positive", "negative"):
            word_set = self.SENTIMENT_WORDS.get(sentiment_type, {})
            # Check language-specific words, fallback to English
            sentiment_words = word_set.get(language, word_set.get("en", set()))

            overlap = len(words & sentiment_words)
            if sentiment_type == "positive":
                positive_count = overlap
            else:
                negative_count = overlap

        total = positive_count + negative_count

        if total == 0:
            return ("neutral", 0.0)

        # Calculate score: positive = +1, negative = -1
        score = (positive_count - negative_count) / total

        if score > 0.1:
            return ("positive", score)
        elif score < -0.1:
            return ("negative", score)
        else:
            return ("neutral", score)

    def extract_keywords(self, text: str, language: str, top_n: int = 5) -> List[str]:
        """
        Extract the most important keywords from text.

        Removes stop words and returns the most frequent
        meaningful terms in the text.

        Args:
            text: Text to extract keywords from.
            language: Language code for stop word filtering.
            top_n: Maximum number of keywords to return.

        Returns:
            List of keyword strings, ordered by frequency.

        Example:
            >>> nlp.extract_keywords("Saya suka makan nasi goreng pedas", "id")
            ['makan', 'nasi', 'goreng', 'pedas']
        """
        if not text:
            return []

        # Get stop words for the language
        stop_words = self.STOP_WORDS.get(language, self.STOP_WORDS.get("en", set()))

        # Tokenize and filter
        words = re.findall(r"\b\w{2,}\b", text.lower())
        filtered_words = [w for w in words if w not in stop_words]

        # Count and return top N
        word_counts = Counter(filtered_words)
        return [word for word, _ in word_counts.most_common(top_n)]

    def is_question(self, text: str, language: str) -> bool:
        """
        Detect whether the text is a question.

        Uses question mark detection and language-specific
        question word patterns.

        Args:
            text: Text to analyze.
            language: Language code.

        Returns:
            True if the text appears to be a question.

        Example:
            >>> nlp.is_question("How are you?", "en")
            True
        """
        # Check for question marks
        if "?" in text or "？" in text or "؟" in text:
            return True

        # Check for question words
        question_patterns = self.INTENT_PATTERNS.get("question", {})
        patterns = question_patterns.get(language, question_patterns.get("en", []))

        for pattern in patterns:
            if pattern == r"\?":
                continue
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                continue

        return False

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text using pattern matching.

        Detects common entity types:
        - URLs
        - Email addresses
        - Numbers (including currencies)
        - Dates (simple patterns)
        - Mentions (@username)

        Args:
            text: Text to extract entities from.

        Returns:
            Dictionary of entity types and their values.

        Example:
            >>> nlp.extract_entities("Visit https://example.com or email test@test.com")
            {'urls': ['https://example.com'], 'emails': ['test@test.com']}
        """
        entities: Dict[str, Any] = {}

        # URLs
        urls = re.findall(
            r"https?://[^\s<>\"]+|www\.[^\s<>\"]+",
            text,
        )
        if urls:
            entities["urls"] = urls

        # Email addresses
        emails = re.findall(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", text)
        if emails:
            entities["emails"] = emails

        # Numbers (including decimals and negatives)
        numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
        if numbers:
            entities["numbers"] = numbers

        # Currency patterns
        currencies = re.findall(
            r"(?:\$|€|¥|£|Rp|RM)\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*(?:dollar|euro|yen|pound|rupiah|ringgit)",
            text,
            re.IGNORECASE,
        )
        if currencies:
            entities["currencies"] = currencies

        # Mentions
        mentions = re.findall(r"@\w+", text)
        if mentions:
            entities["mentions"] = mentions

        # Hashtags
        hashtags = re.findall(r"#\w+", text)
        if hashtags:
            entities["hashtags"] = hashtags

        return entities

    @classmethod
    def list_supported_languages(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all supported languages with their details.

        Returns:
            Dictionary mapping language codes to language info.
        """
        return cls.SUPPORTED_LANGUAGES.copy()

    def __repr__(self) -> str:
        return f"NLPEngine(default_language='{self.default_language}')"
