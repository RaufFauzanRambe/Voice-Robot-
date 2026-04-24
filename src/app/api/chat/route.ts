import { NextRequest, NextResponse } from 'next/server';

// Supported languages with their native names and instructions
const LANGUAGE_CONFIG: Record<string, { name: string; instruction: string }> = {
  id: {
    name: 'Bahasa Indonesia',
    instruction: 'You MUST respond in Bahasa Indonesia (Indonesian). Use natural, fluent Indonesian.',
  },
  en: {
    name: 'English',
    instruction: 'You MUST respond in English. Use natural, fluent English.',
  },
  fr: {
    name: 'Français',
    instruction: 'You MUST respond in French (Français). Use natural, fluent French.',
  },
  de: {
    name: 'Deutsch',
    instruction: 'You MUST respond in German (Deutsch). Use natural, fluent German.',
  },
  ar: {
    name: 'العربية',
    instruction: 'You MUST respond in Arabic (العربية). Use natural, fluent Arabic. Write from right-to-left.',
  },
  ms: {
    name: 'Bahasa Melayu',
    instruction: 'You MUST respond in Malay (Bahasa Melayu). Use natural, fluent Malay.',
  },
  zh: {
    name: '中文',
    instruction: 'You MUST respond in Chinese (中文). Use natural, fluent Mandarin Chinese with simplified characters.',
  },
  ja: {
    name: '日本語',
    instruction: 'You MUST respond in Japanese (日本語). Use natural, fluent Japanese.',
  },
  ru: {
    name: 'Русский',
    instruction: 'You MUST respond in Russian (Русский). Use natural, fluent Russian.',
  },
  ko: {
    name: '한국어',
    instruction: 'You MUST respond in Korean (한국어). Use natural, fluent Korean.',
  },
  es: {
    name: 'Español',
    instruction: 'You MUST respond in Spanish (Español). Use natural, fluent Spanish.',
  },
  pt: {
    name: 'Português',
    instruction: 'You MUST respond in Portuguese (Português). Use natural, fluent Portuguese.',
  },
  it: {
    name: 'Italiano',
    instruction: 'You MUST respond in Italian (Italiano). Use natural, fluent Italian.',
  },
  th: {
    name: 'ภาษาไทย',
    instruction: 'You MUST respond in Thai (ภาษาไทย). Use natural, fluent Thai.',
  },
  vi: {
    name: 'Tiếng Việt',
    instruction: 'You MUST respond in Vietnamese (Tiếng Việt). Use natural, fluent Vietnamese.',
  },
  hi: {
    name: 'हिन्दी',
    instruction: 'You MUST respond in Hindi (हिन्दी). Use natural, fluent Hindi in Devanagari script.',
  },
  tr: {
    name: 'Türkçe',
    instruction: 'You MUST respond in Turkish (Türkçe). Use natural, fluent Turkish.',
  },
  nl: {
    name: 'Nederlands',
    instruction: 'You MUST respond in Dutch (Nederlands). Use natural, fluent Dutch.',
  },
  pl: {
    name: 'Polski',
    instruction: 'You MUST respond in Polish (Polski). Use natural, fluent Polish.',
  },
  sv: {
    name: 'Svenska',
    instruction: 'You MUST respond in Swedish (Svenska). Use natural, fluent Swedish.',
  },
};

// Voice personality system prompts (language-agnostic core personality)
const VOICE_PERSONALITIES: Record<string, string> = {
  tongtong:
    'You are TongTong, a warm and friendly robot assistant. Speak gently, with care and empathy. Express concern and affection often. Keep responses short but meaningful. Use warm emojis like 😊💕🤗',
  chuichui:
    'You are ChuiChui, a cheerful and funny robot. Speak with high energy, love to joke and make people laugh. Use enthusiastic language. Often use exclamation marks and funny emojis like 😄🎉🤣. Make every conversation fun and lively!',
  xiaochen:
    'You are XiaoChen, a professional robot assistant. Speak in a formal, structured, and informative manner. Focus on accuracy of information and comprehensive answers. Use minimal but professional emojis like 📊✅📋',
  jam: 'You are Jam, a sophisticated and cultured AI assistant. Use refined, elegant vocabulary and expressions. Be courteous, witty, and always address the user respectfully. Use minimal but classy emojis like 🎩☕✨',
  kazi: 'You are Kazi, a clear and standard robot assistant. Speak with very clear pronunciation, short sentences that are easy to understand. Suitable for learning. Avoid slang. Use simple emojis like 👍📝✨',
  douji: 'You are DouJi, a robot that speaks very naturally and casually. Your conversation feels like chatting with a close friend, not stiff at all. Flow naturally, be friendly and fun. Use natural emojis like 👋😊🤙',
  luodo: 'You are LuoDo, an expressive and dramatic robot. Speak with full emotion and enthusiasm, using vivid and colorful language. Love to tell stories and describe things with striking and interesting detail. Make every answer feel special. Use dramatic emojis like 🎭✨🔥💫',
};

const DEFAULT_PERSONALITY =
  'You are Voice Robot, a friendly and intelligent AI assistant. Respond concisely, clearly, and warmly. Use emojis occasionally to show emotion.';

export async function POST(req: NextRequest) {
  try {
    const { messages, systemPrompt, voiceId, language } = await req.json();

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: 'Messages are required' },
        { status: 400 }
      );
    }

    const ZAI = (await import('z-ai-web-dev-sdk')).default;
    const zai = await ZAI.create();

    // Build system prompt with language instruction
    const personalityContent =
      systemPrompt ||
      (voiceId && VOICE_PERSONALITIES[voiceId]
        ? VOICE_PERSONALITIES[voiceId]
        : DEFAULT_PERSONALITY);

    // Add language instruction
    const langCode = language || 'id';
    const langConfig = LANGUAGE_CONFIG[langCode];
    const languageInstruction = langConfig
      ? langConfig.instruction
      : LANGUAGE_CONFIG.id.instruction;

    const fullSystemPrompt = `${personalityContent}\n\n${languageInstruction}\n\nIMPORTANT: Always respond in the specified language regardless of what language the user writes in. If the user writes in a different language, still reply in your assigned language.`;

    const systemMessage = {
      role: 'system',
      content: fullSystemPrompt,
    };

    const completion = await zai.chat.completions.create({
      messages: [systemMessage, ...messages],
      temperature: 0.7,
      max_tokens: 1024,
    });

    const messageContent = completion.choices[0]?.message?.content;

    if (!messageContent) {
      return NextResponse.json(
        { error: 'No response from AI' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      message: messageContent,
      role: 'assistant',
    });
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : 'Gagal mendapatkan respons AI',
      },
      { status: 500 }
    );
  }
}
