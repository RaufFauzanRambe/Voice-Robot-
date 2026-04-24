'use client'

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Settings,
  Trash2,
  Bot,
  User,
  StopCircle,
  Loader2,
  Sparkles,
  MessageCircle,
  Play,
  Pause,
  Headphones,
  Speaker,
  AudioWaveform,
  Globe,
  ChevronDown,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from '@/components/ui/sheet'

// ============ Types ============
type RobotState = 'idle' | 'thinking' | 'speaking' | 'listening'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface VoiceProfile {
  value: string
  label: string
  emoji: string
  personality: string
  description: string
  sampleText: string
  color: string
  gradientFrom: string
  gradientTo: string
}

interface LanguageOption {
  code: string
  name: string
  nativeName: string
  flag: string
  sampleText: string
  suggestions: string[]
}

// Sound effects utility using Web Audio API
function playBeepSound(type: 'thinking' | 'listening' | 'sent') {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)

    switch (type) {
      case 'thinking':
        osc.frequency.value = 800
        osc.type = 'sine'
        gain.gain.value = 0.08
        osc.start()
        osc.stop(ctx.currentTime + 0.1)
        break
      case 'listening':
        osc.frequency.value = 600
        osc.type = 'sine'
        gain.gain.value = 0.08
        osc.start()
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15)
        osc.stop(ctx.currentTime + 0.15)
        break
      case 'sent':
        osc.frequency.value = 1000
        osc.type = 'sine'
        gain.gain.value = 0.06
        osc.start()
        osc.stop(ctx.currentTime + 0.08)
        break
    }
  } catch {
    // Silently fail if audio context not available
  }
}

// ============ Language Options ============
const LANGUAGES: LanguageOption[] = [
  {
    code: 'id',
    name: 'Indonesian',
    nativeName: 'Bahasa Indonesia',
    flag: '🇮🇩',
    sampleText: 'Halo! Saya Voice Robot, asisten AI Anda. Senang bertemu dengan Anda!',
    suggestions: ['Halo Robot! 👋', 'Ceritakan lelucon dong 😄', 'Apa yang bisa kamu lakukan? 🤔'],
  },
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇬🇧',
    sampleText: 'Hello! I am Voice Robot, your AI assistant. Nice to meet you!',
    suggestions: ['Hello Robot! 👋', 'Tell me a joke 😄', 'What can you do? 🤔'],
  },
  {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    sampleText: 'Bonjour! Je suis Voice Robot, votre assistant IA. Enchanté!',
    suggestions: ['Bonjour Robot! 👋', 'Raconte-moi une blague 😄', 'Que peux-tu faire? 🤔'],
  },
  {
    code: 'de',
    name: 'German',
    nativeName: 'Deutsch',
    flag: '🇩🇪',
    sampleText: 'Hallo! Ich bin Voice Robot, Ihr KI-Assistent. Schön, Sie kennenzulernen!',
    suggestions: ['Hallo Robot! 👋', 'Erzähl mir einen Witz 😄', 'Was kannst du tun? 🤔'],
  },
  {
    code: 'ar',
    name: 'Arabic',
    nativeName: 'العربية',
    flag: '🇸🇦',
    sampleText: 'مرحبا! أنا روبوت الصوت، مساعدك الذكي. سعيد بلقائك!',
    suggestions: ['مرحبا روبوت! 👋', 'احكِ لي نكتة 😄', 'ماذا يمكنك أن تفعل؟ 🤔'],
  },
  {
    code: 'ms',
    name: 'Malay',
    nativeName: 'Bahasa Melayu',
    flag: '🇲🇾',
    sampleText: 'Helo! Saya Voice Robot, pembantu AI anda. Gembira berjumpa anda!',
    suggestions: ['Helo Robot! 👋', 'Ceritakan lawak 😄', 'Apa yang kamu boleh buat? 🤔'],
  },
  {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    flag: '🇨🇳',
    sampleText: '你好！我是语音机器人，你的AI助手。很高兴见到你！',
    suggestions: ['你好机器人！ 👋', '给我讲个笑话 😄', '你能做什么？ 🤔'],
  },
  {
    code: 'ja',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵',
    sampleText: 'こんにちは！私はボイスロボット、あなたのAIアシスタントです。お会いできて嬉しいです！',
    suggestions: ['こんにちはロボット！ 👋', '冗談を言って 😄', '何ができるの？ 🤔'],
  },
  {
    code: 'ru',
    name: 'Russian',
    nativeName: 'Русский',
    flag: '🇷🇺',
    sampleText: 'Привет! Я Голосовой Робот, ваш ИИ-помощник. Рад встрече!',
    suggestions: ['Привет Робот! 👋', 'Расскажи шутку 😄', 'Что ты умеешь? 🤔'],
  },
  {
    code: 'ko',
    name: 'Korean',
    nativeName: '한국어',
    flag: '🇰🇷',
    sampleText: '안녕하세요! 저는 음성 로봇, 당신의 AI 어시스턴트입니다. 만나서 반갑습니다!',
    suggestions: ['안녕 로봇! 👋', '농담 해줘 😄', '뭘 할 수 있어? 🤔'],
  },
  {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    sampleText: '¡Hola! Soy Voice Robot, tu asistente de IA. ¡Encantado de conocerte!',
    suggestions: ['¡Hola Robot! 👋', 'Cuéntame un chiste 😄', '¿Qué puedes hacer? 🤔'],
  },
  {
    code: 'pt',
    name: 'Portuguese',
    nativeName: 'Português',
    flag: '🇧🇷',
    sampleText: 'Olá! Eu sou o Voice Robot, seu assistente de IA. Prazer em conhecê-lo!',
    suggestions: ['Olá Robô! 👋', 'Conte-me uma piada 😄', 'O que você pode fazer? 🤔'],
  },
  {
    code: 'it',
    name: 'Italian',
    nativeName: 'Italiano',
    flag: '🇮🇹',
    sampleText: 'Ciao! Sono Voice Robot, il tuo assistente IA. Piacere di conoscerti!',
    suggestions: ['Ciao Robot! 👋', 'Raccontami una barzelletta 😄', 'Cosa sai fare? 🤔'],
  },
  {
    code: 'th',
    name: 'Thai',
    nativeName: 'ภาษาไทย',
    flag: '🇹🇭',
    sampleText: 'สวัสดี! ฉันคือ Voice Robot ผู้ช่วย AI ของคุณ ยินดีที่ได้พบคุณ!',
    suggestions: ['สวัสดีหุ่นยนต์! 👋', 'เล่าเรื่องตลกหน่อย 😄', 'คุณทำอะไรได้บ้าง? 🤔'],
  },
  {
    code: 'vi',
    name: 'Vietnamese',
    nativeName: 'Tiếng Việt',
    flag: '🇻🇳',
    sampleText: 'Xin chào! Tôi là Voice Robot, trợ lý AI của bạn. Rất vui được gặp bạn!',
    suggestions: ['Xin chào Robot! 👋', 'Kể tôi nghe một câu đùa 😄', 'Bạn có thể làm gì? 🤔'],
  },
  {
    code: 'hi',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    flag: '🇮🇳',
    sampleText: 'नमस्ते! मैं वॉइस रोबोट हूँ, आपका AI सहायक। आपसे मिलकर खुशी हुई!',
    suggestions: ['नमस्ते रोबोट! 👋', 'एक चुटकुला सुनाओ 😄', 'आप क्या कर सकते हैं? 🤔'],
  },
  {
    code: 'tr',
    name: 'Turkish',
    nativeName: 'Türkçe',
    flag: '🇹🇷',
    sampleText: 'Merhaba! Ben Voice Robot, yapay zeka asistanınız. Tanıştığıma memnun oldum!',
    suggestions: ['Merhaba Robot! 👋', 'Bir şaka anlat 😄', 'Neler yapabilirsin? 🤔'],
  },
  {
    code: 'nl',
    name: 'Dutch',
    nativeName: 'Nederlands',
    flag: '🇳🇱',
    sampleText: 'Hallo! Ik ben Voice Robot, uw AI-assistent. Aangenaam kennis te maken!',
    suggestions: ['Hallo Robot! 👋', 'Vertel een grap 😄', 'Wat kun je doen? 🤔'],
  },
  {
    code: 'pl',
    name: 'Polish',
    nativeName: 'Polski',
    flag: '🇵🇱',
    sampleText: 'Cześć! Jestem Voice Robot, Twój asystent AI. Miło Cię poznać!',
    suggestions: ['Cześć Robocie! 👋', 'Opowiedz żart 😄', 'Co potrafisz zrobić? 🤔'],
  },
  {
    code: 'sv',
    name: 'Swedish',
    nativeName: 'Svenska',
    flag: '🇸🇪',
    sampleText: 'Hej! Jag är Voice Robot, din AI-assistent. Trevligt att träffas!',
    suggestions: ['Hej Robot! 👋', 'Berätta ett skämt 😄', 'Vad kan du göra? 🤔'],
  },
]

// ============ Constants ============
const VOICE_PROFILES: VoiceProfile[] = [
  {
    value: 'tongtong',
    label: 'TongTong',
    emoji: '😊',
    personality: 'Hangat & Ramah',
    description: 'Suara lembut dan menyenangkan, cocok untuk percakapan santai dan teman curhat',
    sampleText: 'Halo! Namaku TongTong. Aku senang bisa membantumu hari ini!',
    color: '#10b981',
    gradientFrom: 'from-emerald-500',
    gradientTo: 'to-green-400',
  },
  {
    value: 'chuichui',
    label: 'ChuiChui',
    emoji: '😄',
    personality: 'Ceria & Lucu',
    description: 'Suara ceria dan penuh semangat, selalu siap membuat suasana jadi lebih menyenangkan',
    sampleText: 'Hehe! Aku ChuiChui, siap buat kamu tertawa dan senang terus!',
    color: '#f59e0b',
    gradientFrom: 'from-amber-500',
    gradientTo: 'to-yellow-400',
  },
  {
    value: 'xiaochen',
    label: 'XiaoChen',
    emoji: '💼',
    personality: 'Profesional & Tenang',
    description: 'Suara stabil dan berwibawa, ideal untuk urusan bisnis dan informasi penting',
    sampleText: 'Selamat datang. Saya XiaoChen, siap memberikan informasi yang Anda butuhkan.',
    color: '#6366f1',
    gradientFrom: 'from-indigo-500',
    gradientTo: 'to-blue-400',
  },
  {
    value: 'jam',
    label: 'Jam',
    emoji: '🎩',
    personality: 'English Gentleman',
    description: 'Suara gentleman Inggris yang elegan dan sopan, sempurna untuk percakapan berbahasa Inggris',
    sampleText: 'Good day! I am Jam, your refined English companion. How may I assist you?',
    color: '#8b5cf6',
    gradientFrom: 'from-violet-500',
    gradientTo: 'to-purple-400',
  },
  {
    value: 'kazi',
    label: 'Kazi',
    emoji: '🎯',
    personality: 'Jernih & Standar',
    description: 'Suara yang jelas dan mudah dipahami, cocok untuk pembelajaran dan pengucapan yang tepat',
    sampleText: 'Halo, saya Kazi. Saya akan berbicara dengan jelas agar Anda mudah memahami.',
    color: '#06b6d4',
    gradientFrom: 'from-cyan-500',
    gradientTo: 'to-teal-400',
  },
  {
    value: 'douji',
    label: 'DouJi',
    emoji: '🌊',
    personality: 'Alami & Lancar',
    description: 'Suara natural yang mengalir seperti percakapan sungguhan, terasa sangat manusiawi',
    sampleText: 'Hai! Aku DouJi. Yuk ngobrol santai, aku suka bicara dengan natural aja.',
    color: '#ec4899',
    gradientFrom: 'from-pink-500',
    gradientTo: 'to-rose-400',
  },
  {
    value: 'luodo',
    label: 'LuoDo',
    emoji: '🎭',
    personality: 'Ekspresif & Dramatis',
    description: 'Suara penuh ekspresi dan emosi, bisa membawakan cerita dengan luar biasa',
    sampleText: 'Salam! Aku LuoDo, suaramu yang penuh semangat dan ekspresi. Dengarkan ceritaku!',
    color: '#ef4444',
    gradientFrom: 'from-red-500',
    gradientTo: 'to-orange-400',
  },
]

const STATUS_MAP: Record<RobotState, string> = {
  idle: 'SIAP',
  thinking: 'BERPIKIR...',
  speaking: 'BERBICARA...',
  listening: 'MENDENGARKAN...',
}

// ============ Audio Waveform Visualizer ============
function AudioWaveformViz({
  isPlaying,
  audioLevel,
  color = '#10b981',
}: {
  isPlaying: boolean
  audioLevel: number
  color?: string
}) {
  const barCount = 24

  return (
    <div className="flex items-end justify-center gap-[2px] h-8">
      {Array.from({ length: barCount }).map((_, i) => {
        const centerDistance = Math.abs(i - barCount / 2) / (barCount / 2)
        const baseHeight = isPlaying
          ? (1 - centerDistance * 0.6) * audioLevel * 28 + 4
          : 3
        return (
          <motion.div
            key={i}
            className="rounded-full"
            style={{
              width: 3,
              backgroundColor: isPlaying ? color : 'rgba(255,255,255,0.15)',
              transition: 'background-color 0.3s',
            }}
            animate={{
              height: isPlaying
                ? baseHeight + Math.random() * 8
                : 3,
            }}
            transition={{
              duration: 0.08,
              ease: 'easeOut',
            }}
          />
        )
      })}
    </div>
  )
}

// ============ Voice Character Card ============
function VoiceCard({
  profile,
  isSelected,
  isPreviewing,
  onSelect,
  onPreview,
}: {
  profile: VoiceProfile
  isSelected: boolean
  isPreviewing: boolean
  onSelect: () => void
  onPreview: () => void
}) {
  return (
    <motion.button
      onClick={onSelect}
      className={`relative w-full text-left rounded-xl p-3 transition-all border ${
        isSelected
          ? `bg-gradient-to-br ${profile.gradientFrom}/10 ${profile.gradientTo}/5 border-white/20`
          : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06] hover:border-white/10'
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      {isSelected && (
        <motion.div
          layoutId="voice-selected-ring"
          className="absolute inset-0 rounded-xl"
          style={{
            boxShadow: `0 0 12px ${profile.color}30, inset 0 0 12px ${profile.color}10`,
          }}
          transition={{ type: 'spring', bounce: 0.2, duration: 0.5 }}
        />
      )}

      <div className="relative flex items-start gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-lg"
          style={{
            background: isSelected ? `${profile.color}25` : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isSelected ? profile.color + '50' : 'rgba(255,255,255,0.08)'}`,
          }}
        >
          {profile.emoji}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-200">{profile.label}</span>
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
              style={{
                background: `${profile.color}15`,
                color: profile.color,
                border: `1px solid ${profile.color}30`,
              }}
            >
              {profile.personality}
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">
            {profile.description}
          </p>
        </div>

        <motion.button
          onClick={(e) => {
            e.stopPropagation()
            onPreview()
          }}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all"
          style={{
            background: isPreviewing ? `${profile.color}25` : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isPreviewing ? profile.color + '40' : 'rgba(255,255,255,0.08)'}`,
            color: isPreviewing ? profile.color : 'rgba(255,255,255,0.4)',
          }}
          whileTap={{ scale: 0.85 }}
          aria-label={`Preview suara ${profile.label}`}
        >
          {isPreviewing ? (
            <Pause className="h-3.5 w-3.5" />
          ) : (
            <Play className="h-3.5 w-3.5 ml-0.5" />
          )}
        </motion.button>
      </div>
    </motion.button>
  )
}

// ============ Language Selector ============
function LanguageSelector({
  selectedLang,
  onLangChange,
  isOpen,
  onToggle,
}: {
  selectedLang: string
  onLangChange: (code: string) => void
  isOpen: boolean
  onToggle: () => void
}) {
  const [searchQuery, setSearchQuery] = useState('')
  const currentLang = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0]

  const filteredLangs = LANGUAGES.filter((lang) => {
    const q = searchQuery.toLowerCase()
    return (
      lang.name.toLowerCase().includes(q) ||
      lang.nativeName.toLowerCase().includes(q) ||
      lang.code.toLowerCase().includes(q)
    )
  })

  // Popular languages shown first
  const popularCodes = ['id', 'en', 'zh', 'ja', 'ko', 'ar', 'fr', 'de', 'ru', 'ms']
  const popularLangs = filteredLangs.filter((l) => popularCodes.includes(l.code))
  const otherLangs = filteredLangs.filter((l) => !popularCodes.includes(l.code))

  return (
    <div className="relative">
      {/* Trigger button */}
      <motion.button
        onClick={onToggle}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border transition-all"
        style={{
          background: 'rgba(255,255,255,0.05)',
          borderColor: isOpen ? 'rgba(34,211,238,0.4)' : 'rgba(255,255,255,0.1)',
        }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <Globe className="h-3.5 w-3.5 text-cyan-400" />
        <span className="text-lg leading-none">{currentLang.flag}</span>
        <span className="text-[11px] font-medium text-gray-300 max-w-[70px] truncate">
          {currentLang.nativeName}
        </span>
        <ChevronDown
          className={`h-3 w-3 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </motion.button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 z-40"
              onClick={onToggle}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            <motion.div
              className="absolute top-full left-0 mt-2 z-50 w-72 rounded-xl border border-white/10 bg-gray-900/95 backdrop-blur-xl shadow-2xl overflow-hidden"
              style={{
                maxHeight: '420px',
              }}
              initial={{ opacity: 0, y: -8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.95 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
            >
              {/* Search */}
              <div className="p-2 border-b border-white/5">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search language..."
                    className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50"
                    autoFocus
                  />
                </div>
              </div>

              {/* Language list */}
              <div className="overflow-y-auto max-h-[350px] custom-scrollbar">
                {popularLangs.length > 0 && (
                  <>
                    <div className="px-3 py-1.5 text-[9px] font-semibold text-gray-600 uppercase tracking-widest">
                      Popular
                    </div>
                    {popularLangs.map((lang) => (
                      <LanguageItem
                        key={lang.code}
                        lang={lang}
                        isSelected={selectedLang === lang.code}
                        onSelect={() => {
                          onLangChange(lang.code)
                          onToggle()
                        }}
                      />
                    ))}
                  </>
                )}

                {otherLangs.length > 0 && (
                  <>
                    <div className="px-3 py-1.5 mt-1 text-[9px] font-semibold text-gray-600 uppercase tracking-widest border-t border-white/5 pt-2">
                      More Languages
                    </div>
                    {otherLangs.map((lang) => (
                      <LanguageItem
                        key={lang.code}
                        lang={lang}
                        isSelected={selectedLang === lang.code}
                        onSelect={() => {
                          onLangChange(lang.code)
                          onToggle()
                        }}
                      />
                    ))}
                  </>
                )}

                {filteredLangs.length === 0 && (
                  <div className="px-3 py-4 text-center text-xs text-gray-600">
                    No languages found
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function LanguageItem({
  lang,
  isSelected,
  onSelect,
}: {
  lang: LanguageOption
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <motion.button
      onClick={onSelect}
      className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all ${
        isSelected
          ? 'bg-cyan-500/10 border-l-2 border-cyan-400'
          : 'hover:bg-white/5 border-l-2 border-transparent'
      }`}
      whileTap={{ scale: 0.98 }}
    >
      <span className="text-lg">{lang.flag}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className={`text-xs font-medium ${isSelected ? 'text-cyan-300' : 'text-gray-200'}`}>
            {lang.nativeName}
          </span>
          {isSelected && (
            <span className="text-[8px] px-1 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              ACTIVE
            </span>
          )}
        </div>
        <span className="text-[10px] text-gray-500">{lang.name}</span>
      </div>
    </motion.button>
  )
}

// ============ Robot Avatar Component ============
function RobotAvatar({
  state,
  audioLevel,
  currentVoice,
}: {
  state: RobotState
  audioLevel: number
  currentVoice: VoiceProfile
}) {
  const eyeVariants = {
    idle: { scaleY: 1, scaleX: 1 },
    thinking: { scaleY: 0.15, scaleX: 1.1 },
    speaking: { scaleY: 1.2, scaleX: 0.9 },
    listening: { scaleY: 1.3, scaleX: 1.3 },
  }

  const mouthVariants = {
    idle: { scaleY: 0.3, scaleX: 1 },
    thinking: { scaleY: 0.2, scaleX: 0.8 },
    speaking: { scaleY: 0.6 + audioLevel * 0.8, scaleX: 1 + audioLevel * 0.3 },
    listening: { scaleY: 0.15, scaleX: 1.2 },
  }

  const showPulse = state === 'speaking' || state === 'listening'
  const voiceColor = currentVoice.color

  return (
    <div className="relative flex items-center justify-center">
      <AnimatePresence>
        {showPulse && (
          <>
            <motion.div
              className="absolute rounded-full border-2"
              style={{
                width: 140,
                height: 140,
                borderColor:
                  state === 'speaking'
                    ? `${voiceColor}66`
                    : 'rgba(34, 211, 238, 0.4)',
              }}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.5, opacity: 0 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
            />
            <motion.div
              className="absolute rounded-full border-2"
              style={{
                width: 140,
                height: 140,
                borderColor:
                  state === 'speaking'
                    ? `${voiceColor}44`
                    : 'rgba(34, 211, 238, 0.3)',
              }}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.8, opacity: 0 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'easeOut',
                delay: 0.4,
              }}
            />
          </>
        )}
      </AnimatePresence>

      {state === 'listening' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <svg width="160" height="160" viewBox="0 0 160 160">
            {[0, 60, 120, 180, 240, 300].map((rotation, i) => (
              <motion.circle
                key={i}
                cx="80"
                cy="80"
                r={55 + i * 3}
                fill="none"
                stroke={`rgba(34, 211, 238, ${0.2 + audioLevel * 0.3})`}
                strokeWidth="2"
                strokeDasharray="8 12"
                style={{ rotate: rotation }}
                animate={{ rotate: rotation + 360 }}
                transition={{
                  duration: 4 + i,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            ))}
          </svg>
        </div>
      )}

      <motion.div
        className="relative flex items-center justify-center rounded-full"
        style={{
          width: 120,
          height: 120,
          background: `linear-gradient(135deg, ${voiceColor}33, ${voiceColor}15)`,
          border: `2px solid ${voiceColor}44`,
          boxShadow: `0 0 ${20 + audioLevel * 30}px ${voiceColor}${Math.round(15 + audioLevel * 20).toString(16).padStart(2, '0')}`,
        }}
        animate={{
          scale: state === 'speaking' ? 1 + audioLevel * 0.05 : 1,
        }}
        transition={{ duration: 0.1 }}
      >
        <div className="flex flex-col items-center gap-2">
          <div className="flex gap-4">
            <motion.div
              className="rounded-full"
              style={{
                width: 18,
                height: 18,
                background:
                  state === 'listening'
                    ? 'radial-gradient(circle, #22d3ee, #06b6d4)'
                    : `radial-gradient(circle, ${voiceColor}, ${voiceColor}cc)`,
                boxShadow:
                  state === 'listening'
                    ? '0 0 10px rgba(34,211,238,0.6)'
                    : `0 0 10px ${voiceColor}99`,
              }}
              variants={eyeVariants}
              animate={state}
              transition={{ duration: 0.3 }}
            />
            <motion.div
              className="rounded-full"
              style={{
                width: 18,
                height: 18,
                background:
                  state === 'listening'
                    ? 'radial-gradient(circle, #22d3ee, #06b6d4)'
                    : `radial-gradient(circle, ${voiceColor}, ${voiceColor}cc)`,
                boxShadow:
                  state === 'listening'
                    ? '0 0 10px rgba(34,211,238,0.6)'
                    : `0 0 10px ${voiceColor}99`,
              }}
              variants={eyeVariants}
              animate={state}
              transition={{ duration: 0.3 }}
            />
          </div>

          <motion.div
            className="rounded-full"
            style={{
              width: 24,
              height: 10,
              background:
                state === 'speaking'
                  ? `radial-gradient(circle, ${voiceColor}, ${voiceColor}cc)`
                  : `${voiceColor}66`,
            }}
            variants={mouthVariants}
            animate={state}
            transition={{ duration: 0.08 }}
          />
        </div>

        <div
          className="absolute -bottom-6 text-[9px] font-mono tracking-wider"
          style={{ color: `${voiceColor}88` }}
        >
          {currentVoice.label.toUpperCase()}
        </div>
      </motion.div>
    </div>
  )
}

// ============ Typing Indicator ============
function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-start gap-3"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-500/30">
        <Bot className="h-4 w-4 text-emerald-400" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-white/5 border border-white/10 px-4 py-3">
        <motion.div
          className="h-2 w-2 rounded-full bg-emerald-400"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
        />
        <motion.div
          className="h-2 w-2 rounded-full bg-emerald-400"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
        />
        <motion.div
          className="h-2 w-2 rounded-full bg-emerald-400"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
        />
      </div>
    </motion.div>
  )
}

// ============ Chat Message Bubble ============
function ChatBubble({
  message,
  onSpeak,
  isSpeaking,
  isMuted,
  voiceColor,
}: {
  message: ChatMessage
  onSpeak: (text: string) => void
  isSpeaking: boolean
  isMuted: boolean
  voiceColor: string
}) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
          isUser
            ? 'bg-cyan-500/20 border-cyan-500/30'
            : ''
        }`}
        style={
          !isUser
            ? {
                background: `${voiceColor}20`,
                borderColor: `${voiceColor}30`,
              }
            : undefined
        }
      >
        {isUser ? (
          <User className="h-4 w-4 text-cyan-400" />
        ) : (
          <Bot className="h-4 w-4" style={{ color: voiceColor }} />
        )}
      </div>

      <div className={`flex flex-col gap-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-gradient-to-br from-emerald-600 to-cyan-600 text-white rounded-tr-sm'
              : 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-sm'
          }`}
        >
          {message.content}
        </div>

        {!isUser && !isMuted && (
          <button
            onClick={() => onSpeak(message.content)}
            className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-emerald-400 transition-colors px-1 py-0.5 rounded-md hover:bg-white/5"
            aria-label="Putar suara"
          >
            {isSpeaking ? (
              <StopCircle className="h-3 w-3" />
            ) : (
              <Volume2 className="h-3 w-3" />
            )}
            {isSpeaking ? 'Berhenti' : 'Putar'}
          </button>
        )}
      </div>
    </motion.div>
  )
}

// ============ Settings Panel Content ============
function SettingsContent({
  voice,
  onVoiceChange,
  speed,
  onSpeedChange,
  volume,
  onVolumeChange,
  autoSpeak,
  onAutoSpeakChange,
  isMuted,
  onMuteChange,
  onPreviewVoice,
  previewingVoice,
  soundEffects,
  onSoundEffectsChange,
  language,
  onLanguageChange,
}: {
  voice: string
  onVoiceChange: (v: string) => void
  speed: number
  onSpeedChange: (s: number) => void
  volume: number
  onVolumeChange: (v: number) => void
  autoSpeak: boolean
  onAutoSpeakChange: (v: boolean) => void
  isMuted: boolean
  onMuteChange: (v: boolean) => void
  onPreviewVoice: (voiceId: string) => void
  previewingVoice: string | null
  soundEffects: boolean
  onSoundEffectsChange: (v: boolean) => void
  language: string
  onLanguageChange: (code: string) => void
}) {
  const currentProfile = VOICE_PROFILES.find((v) => v.value === voice) || VOICE_PROFILES[0]
  const currentLang = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]

  return (
    <div className="flex flex-col gap-5 p-1">
      {/* Language Selection */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Globe className="h-3.5 w-3.5 text-gray-500" />
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Bahasa / Language
          </label>
        </div>
        <div className="grid grid-cols-2 gap-1.5 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
          {LANGUAGES.map((lang) => (
            <motion.button
              key={lang.code}
              onClick={() => onLanguageChange(lang.code)}
              className={`flex items-center gap-1.5 px-2 py-1.5 rounded-lg border text-left transition-all ${
                language === lang.code
                  ? 'bg-cyan-500/10 border-cyan-500/30'
                  : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06] hover:border-white/10'
              }`}
              whileTap={{ scale: 0.97 }}
            >
              <span className="text-sm">{lang.flag}</span>
              <span className={`text-[10px] truncate ${language === lang.code ? 'text-cyan-300 font-medium' : 'text-gray-400'}`}>
                {lang.nativeName}
              </span>
            </motion.button>
          ))}
        </div>
        <div className="flex items-center gap-1.5 px-1 py-1 rounded-lg bg-cyan-500/5 border border-cyan-500/10">
          <span className="text-sm">{currentLang.flag}</span>
          <span className="text-[10px] text-cyan-400 font-medium">
            {currentLang.nativeName} — {currentLang.name}
          </span>
        </div>
      </div>

      {/* Voice Character Cards */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Headphones className="h-3.5 w-3.5 text-gray-500" />
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Pilih Suara Robot
          </label>
        </div>
        <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1 custom-scrollbar">
          {VOICE_PROFILES.map((profile) => (
            <VoiceCard
              key={profile.value}
              profile={profile}
              isSelected={voice === profile.value}
              isPreviewing={previewingVoice === profile.value}
              onSelect={() => onVoiceChange(profile.value)}
              onPreview={() => onPreviewVoice(profile.value)}
            />
          ))}
        </div>
      </div>

      {/* Speed Slider */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AudioWaveform className="h-3.5 w-3.5 text-gray-500" />
            <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              Kecepatan
            </label>
          </div>
          <span className="text-xs font-mono" style={{ color: currentProfile.color }}>
            {speed.toFixed(1)}x
          </span>
        </div>
        <Slider
          value={[speed]}
          onValueChange={([v]) => onSpeedChange(v)}
          min={0.5}
          max={2.0}
          step={0.1}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-600">
          <span>0.5x Lambat</span>
          <span>1.0x Normal</span>
          <span>2.0x Cepat</span>
        </div>
      </div>

      {/* Volume Slider */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Speaker className="h-3.5 w-3.5 text-gray-500" />
            <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              Volume
            </label>
          </div>
          <span className="text-xs font-mono" style={{ color: currentProfile.color }}>
            {Math.round(volume * 100)}%
          </span>
        </div>
        <Slider
          value={[volume]}
          onValueChange={([v]) => onVolumeChange(v)}
          min={0.1}
          max={1.0}
          step={0.05}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-600">
          <span>Pelan</span>
          <span>Sedang</span>
          <span>Keras</span>
        </div>
      </div>

      {/* Toggles */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Auto Bicara
          </label>
          <Switch
            checked={autoSpeak}
            onCheckedChange={onAutoSpeakChange}
            className="data-[state=checked]:bg-emerald-500"
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Bisukan
          </label>
          <Switch
            checked={isMuted}
            onCheckedChange={onMuteChange}
            className="data-[state=checked]:bg-red-500"
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Efek Suara
          </label>
          <Switch
            checked={soundEffects}
            onCheckedChange={onSoundEffectsChange}
            className="data-[state=checked]:bg-cyan-500"
          />
        </div>
      </div>

      {/* Info card */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-emerald-400" />
          <h4 className="text-sm font-medium text-emerald-300">Voice Robot</h4>
        </div>
        <p className="text-xs text-gray-500 leading-relaxed">
          Tekan tombol <Play className="inline h-3 w-3" /> di setiap suara untuk mendengar preview.
          Pilih suara yang paling cocok untuk percakapan Anda!
        </p>
        <div className="flex items-center gap-1.5 mt-2 px-2 py-1.5 rounded-lg bg-cyan-500/5 border border-cyan-500/10">
          <Globe className="h-3 w-3 text-cyan-400" />
          <span className="text-[10px] text-cyan-400">
            20 bahasa tersedia — Indonesian, English, French, German, Arabic, Malay, Chinese, Japanese, Russian, Korean, Spanish, Portuguese, Italian, Thai, Vietnamese, Hindi, Turkish, Dutch, Polish, Swedish
          </span>
        </div>
      </div>
    </div>
  )
}

// ============ Main Page Component ============
export default function VoiceRobotPage() {
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Robot state
  const [robotState, setRobotState] = useState<RobotState>('idle')
  const [audioLevel, setAudioLevel] = useState(0)

  // Language state
  const [language, setLanguage] = useState('id')
  const [langSelectorOpen, setLangSelectorOpen] = useState(false)

  // Voice settings
  const [voice, setVoice] = useState('tongtong')
  const [speed, setSpeed] = useState(1.0)
  const [volume, setVolume] = useState(0.8)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [isMuted, setIsMuted] = useState(false)
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null)

  // Recording state
  const [isRecording, setIsRecording] = useState(false)

  // Speaking state
  const [currentlySpeakingId, setCurrentlySpeakingId] = useState<string | null>(null)
  const [isPaused, setIsPaused] = useState(false)

  // Settings sheet state
  const [settingsOpen, setSettingsOpen] = useState(false)

  // Sound effects toggle
  const [soundEffects, setSoundEffects] = useState(true)

  // Refs
  const scrollRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const previewAudioRef = useRef<HTMLAudioElement | null>(null)
  const speakAudioLevelRef = useRef(0)

  // Get current voice profile & language
  const currentVoiceProfile = VOICE_PROFILES.find((v) => v.value === voice) || VOICE_PROFILES[0]
  const currentLanguage = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      const viewport = scrollRef.current.querySelector('[data-slot="scroll-area-viewport"]')
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight
      }
    }
  }, [messages, isLoading])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      if (audioContextRef.current) audioContextRef.current.close()
      if (audioRef.current) {
        audioRef.current.pause()
        URL.revokeObjectURL(audioRef.current.src)
      }
      if (previewAudioRef.current) {
        previewAudioRef.current.pause()
        URL.revokeObjectURL(previewAudioRef.current.src)
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  // Generate unique ID
  const genId = () => Math.random().toString(36).substring(2, 9)

  // ======== TTS API Call ========
  const callTTS = useCallback(
    async (text: string, voiceId?: string, speedVal?: number, volumeVal?: number) => {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.substring(0, 1024),
          voice: voiceId || voice,
          speed: speedVal ?? speed,
          volume: volumeVal ?? volume,
        }),
      })

      if (!res.ok) throw new Error('TTS gagal')

      const audioBlob = await res.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      return { audioUrl, blob: audioBlob }
    },
    [voice, speed, volume]
  )

  // ======== Speak Text ========
  const speakText = useCallback(
    async (text: string, msgId?: string) => {
      if (isMuted) return

      if (audioRef.current) {
        audioRef.current.pause()
        URL.revokeObjectURL(audioRef.current.src)
        audioRef.current = null
      }

      setRobotState('speaking')
      setIsPaused(false)
      if (msgId) setCurrentlySpeakingId(msgId)

      try {
        const { audioUrl } = await callTTS(text)
        const audio = new Audio(audioUrl)
        audio.volume = volume
        audioRef.current = audio

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
          audioRef.current = null
          setRobotState('idle')
          setCurrentlySpeakingId(null)
          setIsPaused(false)
          speakAudioLevelRef.current = 0
        }

        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl)
          audioRef.current = null
          setRobotState('idle')
          setCurrentlySpeakingId(null)
          setIsPaused(false)
          speakAudioLevelRef.current = 0
        }

        await audio.play()

        const animateSpeaking = () => {
          if (audioRef.current && !audioRef.current.paused) {
            speakAudioLevelRef.current = 0.3 + Math.random() * 0.5
            setAudioLevel(speakAudioLevelRef.current)
            requestAnimationFrame(animateSpeaking)
          }
        }
        animateSpeaking()
      } catch (err) {
        console.error('TTS error:', err)
        setRobotState('idle')
        setCurrentlySpeakingId(null)
        speakAudioLevelRef.current = 0
      }
    },
    [callTTS, isMuted, volume]
  )

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      URL.revokeObjectURL(audioRef.current.src)
      audioRef.current = null
    }
    setRobotState('idle')
    setCurrentlySpeakingId(null)
    setAudioLevel(0)
    setIsPaused(false)
    speakAudioLevelRef.current = 0
  }, [])

  // ======== Pause / Resume TTS ========
  const togglePause = useCallback(() => {
    if (!audioRef.current) return
    if (isPaused) {
      audioRef.current.play()
      setIsPaused(false)
      setRobotState('speaking')
    } else {
      audioRef.current.pause()
      setIsPaused(true)
      setRobotState('idle')
    }
  }, [isPaused])

  // ======== Preview Voice ========
  const previewVoice = useCallback(
    async (voiceId: string) => {
      if (previewAudioRef.current) {
        previewAudioRef.current.pause()
        URL.revokeObjectURL(previewAudioRef.current.src)
        previewAudioRef.current = null
      }

      if (previewingVoice === voiceId) {
        setPreviewingVoice(null)
        return
      }

      const profile = VOICE_PROFILES.find((v) => v.value === voiceId)
      if (!profile) return

      setPreviewingVoice(voiceId)

      try {
        // Use language-specific sample text for preview
        const langSample = currentLanguage.sampleText
        const previewText = voiceId === voice ? langSample : profile.sampleText

        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: previewText,
            voice: voiceId,
            speed: 1.0,
            volume: volume,
          }),
        })

        if (!res.ok) throw new Error('TTS gagal')

        const audioBlob = await res.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.volume = volume
        previewAudioRef.current = audio

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
          previewAudioRef.current = null
          setPreviewingVoice(null)
        }

        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl)
          previewAudioRef.current = null
          setPreviewingVoice(null)
        }

        await audio.play()
      } catch (err) {
        console.error('Preview voice error:', err)
        setPreviewingVoice(null)
      }
    },
    [previewingVoice, volume, currentLanguage, voice]
  )

  // ======== Send Message ========
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return

      if (previewAudioRef.current) {
        previewAudioRef.current.pause()
        URL.revokeObjectURL(previewAudioRef.current.src)
        previewAudioRef.current = null
        setPreviewingVoice(null)
      }

      const userMsg: ChatMessage = { id: genId(), role: 'user', content: text.trim() }
      setMessages((prev) => [...prev, userMsg])
      setInputText('')
      setIsLoading(true)
      setRobotState('thinking')
      if (soundEffects) playBeepSound('sent')

      try {
        const chatHistory = [...messages, userMsg].map((m) => ({
          role: m.role,
          content: m.content,
        }))

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: chatHistory,
            voiceId: voice,
            language: language,
          }),
        })

        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.error || 'Gagal mendapatkan respons')
        }

        const data = await res.json()
        const assistantMsg: ChatMessage = {
          id: genId(),
          role: 'assistant',
          content: data.message,
        }

        setMessages((prev) => [...prev, assistantMsg])
        setIsLoading(false)
        setRobotState('idle')

        if (autoSpeak && !isMuted) {
          speakText(data.message, assistantMsg.id)
        }
      } catch (err) {
        console.error('Chat error:', err)
        setIsLoading(false)
        setRobotState('idle')
        const errorMsg: ChatMessage = {
          id: genId(),
          role: 'assistant',
          content: `Maaf, terjadi kesalahan: ${err instanceof Error ? err.message : 'Koneksi gagal'}. Coba lagi ya!`,
        }
        setMessages((prev) => [...prev, errorMsg])
      }
    },
    [messages, autoSpeak, isMuted, speakText, voice, language]
  )

  // ======== Voice Recording ========
  const monitorAudioLevel = useCallback((stream: MediaStream) => {
    const audioContext = new AudioContext()
    audioContextRef.current = audioContext
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    analyserRef.current = analyser

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const updateLevel = () => {
      if (!analyserRef.current) return
      analyserRef.current.getByteFrequencyData(dataArray)
      const average = dataArray.reduce((sum, v) => sum + v, 0) / dataArray.length
      const normalizedLevel = Math.min(average / 128, 1)
      setAudioLevel(normalizedLevel)
      animFrameRef.current = requestAnimationFrame(updateLevel)
    }

    updateLevel()
  }, [])

  const startRecording = useCallback(async () => {
    if (previewAudioRef.current) {
      previewAudioRef.current.pause()
      URL.revokeObjectURL(previewAudioRef.current.src)
      previewAudioRef.current = null
      setPreviewingVoice(null)
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      })

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      })

      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop())

        if (animFrameRef.current) {
          cancelAnimationFrame(animFrameRef.current)
          animFrameRef.current = null
        }
        if (audioContextRef.current) {
          audioContextRef.current.close()
          audioContextRef.current = null
        }
        analyserRef.current = null
        setAudioLevel(0)

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        chunksRef.current = []

        if (blob.size < 1000) {
          setIsRecording(false)
          setRobotState('idle')
          return
        }

        setRobotState('thinking')
        setIsRecording(false)

        try {
          const formData = new FormData()
          formData.append('audio', blob, 'recording.webm')
          formData.append('language', language)

          const asrRes = await fetch('/api/asr', {
            method: 'POST',
            body: formData,
          })

          if (!asrRes.ok) {
            throw new Error('ASR gagal')
          }

          const asrData = await asrRes.json()

          if (asrData.transcription && asrData.transcription.trim()) {
            await sendMessage(asrData.transcription.trim())
          } else {
            setRobotState('idle')
            const errorMsg: ChatMessage = {
              id: genId(),
              role: 'assistant',
              content: 'Maaf, saya tidak bisa mendengar suara Anda. Coba lagi ya!',
            }
            setMessages((prev) => [...prev, errorMsg])
          }
        } catch (err) {
          console.error('ASR error:', err)
          setRobotState('idle')
          const errorMsg: ChatMessage = {
            id: genId(),
            role: 'assistant',
            content: 'Maaf, terjadi kesalahan saat mengenali suara. Coba lagi ya!',
          }
          setMessages((prev) => [...prev, errorMsg])
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(250)
      setIsRecording(true)
      setRobotState('listening')
      if (soundEffects) playBeepSound('listening')
      monitorAudioLevel(stream)
    } catch (err) {
      console.error('Mic error:', err)
      const errorMsg: ChatMessage = {
        id: genId(),
        role: 'assistant',
        content: 'Tidak bisa mengakses mikrofon. Pastikan izin mikrofon diaktifkan!',
      }
      setMessages((prev) => [...prev, errorMsg])
    }
  }, [monitorAudioLevel, sendMessage, language])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
  }, [])

  // Handle Speak from message
  const handleSpeakMessage = useCallback(
    (text: string) => {
      if (currentlySpeakingId) {
        stopSpeaking()
      } else {
        speakText(text, genId())
      }
    },
    [currentlySpeakingId, stopSpeaking, speakText]
  )

  // Clear Chat
  const clearChat = useCallback(() => {
    stopSpeaking()
    setMessages([])
    setRobotState('idle')
  }, [stopSpeaking])

  // Handle language change
  const handleLanguageChange = useCallback((code: string) => {
    setLanguage(code)
    setLangSelectorOpen(false)
  }, [])

  // ======== Render ========
  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      {/* Background gradient */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse at 20% 20%, ${currentVoiceProfile.color}12 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(34,211,238,0.06) 0%, transparent 50%), linear-gradient(180deg, #030712 0%, #0f172a 100%)`,
        }}
      />

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-full shadow-lg"
              style={{
                background: `linear-gradient(135deg, ${currentVoiceProfile.color}, ${currentVoiceProfile.color}aa)`,
                boxShadow: `0 4px 12px ${currentVoiceProfile.color}33`,
              }}
            >
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1
                className="text-base font-bold bg-clip-text text-transparent"
                style={{
                  backgroundImage: `linear-gradient(to right, ${currentVoiceProfile.color}, #22d3ee)`,
                }}
              >
                Voice Robot
              </h1>
              <div className="flex items-center gap-1.5">
                <p className="text-[10px] text-gray-500">{currentVoiceProfile.label}</p>
                <span className="text-[10px]">{currentVoiceProfile.emoji}</span>
                <span className="text-[10px] text-gray-700">|</span>
                <span className="text-[10px]">{currentLanguage.flag}</span>
                <p className="text-[10px] text-cyan-500/60">{currentLanguage.nativeName}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <LanguageSelector
              selectedLang={language}
              onLangChange={handleLanguageChange}
              isOpen={langSelectorOpen}
              onToggle={() => setLangSelectorOpen(!langSelectorOpen)}
            />

            {/* Mute toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMuted(!isMuted)}
              className={`h-9 w-9 rounded-full ${
                isMuted
                  ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                  : 'text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10'
              }`}
              aria-label={isMuted ? 'Aktifkan suara' : 'Bisukan'}
            >
              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </Button>

            {/* Clear chat */}
            <Button
              variant="ghost"
              size="icon"
              onClick={clearChat}
              className="h-9 w-9 rounded-full text-gray-400 hover:text-red-400 hover:bg-red-500/10"
              aria-label="Hapus chat"
            >
              <Trash2 className="h-4 w-4" />
            </Button>

            {/* Settings - mobile */}
            <Sheet open={settingsOpen} onOpenChange={setSettingsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 rounded-full text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 lg:hidden"
                  aria-label="Pengaturan"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent
                side="bottom"
                className="bg-gray-950/95 backdrop-blur-xl border-white/10 text-white rounded-t-2xl max-h-[85vh]"
              >
                <SheetHeader>
                  <SheetTitle className="text-white">Pengaturan Suara</SheetTitle>
                  <SheetDescription className="text-gray-500">
                    Pilih bahasa, suara, atur kecepatan & volume robot
                  </SheetDescription>
                </SheetHeader>
                <SettingsContent
                  voice={voice}
                  onVoiceChange={(v) => {
                    setVoice(v)
                  }}
                  speed={speed}
                  onSpeedChange={setSpeed}
                  volume={volume}
                  onVolumeChange={setVolume}
                  autoSpeak={autoSpeak}
                  onAutoSpeakChange={setAutoSpeak}
                  isMuted={isMuted}
                  onMuteChange={setIsMuted}
                  onPreviewVoice={previewVoice}
                  previewingVoice={previewingVoice}
                  soundEffects={soundEffects}
                  onSoundEffectsChange={setSoundEffects}
                  language={language}
                  onLanguageChange={handleLanguageChange}
                />
              </SheetContent>
            </Sheet>
          </div>
        </header>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Chat area */}
          <main className="flex flex-col flex-1 min-w-0">
            {/* Robot avatar area */}
            <div className="flex flex-col items-center justify-center py-4 px-4 border-b border-white/5">
              <RobotAvatar
                state={robotState}
                audioLevel={audioLevel}
                currentVoice={currentVoiceProfile}
              />

              {/* Waveform visualizer */}
              <div className="mt-5 w-48">
                <AudioWaveformViz
                  isPlaying={robotState === 'speaking'}
                  audioLevel={audioLevel}
                  color={currentVoiceProfile.color}
                />
              </div>

              <motion.div
                className="mt-2 text-xs font-mono tracking-widest"
                animate={{
                  color:
                    robotState === 'idle'
                      ? '#6b7280'
                      : robotState === 'thinking'
                        ? '#f59e0b'
                        : robotState === 'speaking'
                          ? currentVoiceProfile.color
                          : '#22d3ee',
                }}
                transition={{ duration: 0.3 }}
              >
                {STATUS_MAP[robotState]}
              </motion.div>

              {/* Quick Voice Switcher */}
              <div className="mt-3 flex items-center gap-1.5 overflow-x-auto px-2 pb-1 scrollbar-none">
                {VOICE_PROFILES.map((profile) => (
                  <motion.button
                    key={profile.value}
                    onClick={() => {
                      if (voice !== profile.value) {
                        setVoice(profile.value)
                        previewVoice(profile.value)
                      }
                    }}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full whitespace-nowrap transition-all border text-[11px] font-medium"
                    style={{
                      background:
                        voice === profile.value
                          ? `${profile.color}20`
                          : 'rgba(255,255,255,0.03)',
                      borderColor:
                        voice === profile.value
                          ? `${profile.color}50`
                          : 'rgba(255,255,255,0.06)',
                      color:
                        voice === profile.value
                          ? profile.color
                          : 'rgba(255,255,255,0.4)',
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <span className="text-sm">{profile.emoji}</span>
                    <span>{profile.label}</span>
                  </motion.button>
                ))}
              </div>

              {/* Quick Language Switcher */}
              <div className="mt-2 flex items-center gap-1 overflow-x-auto px-2 pb-1 scrollbar-none">
                <Globe className="h-3 w-3 text-cyan-500/40 shrink-0 mr-0.5" />
                {LANGUAGES.slice(0, 10).map((lang) => (
                  <motion.button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className="flex items-center gap-1 px-2 py-1 rounded-full whitespace-nowrap transition-all border text-[10px] font-medium"
                    style={{
                      background:
                        language === lang.code
                          ? 'rgba(34,211,238,0.1)'
                          : 'rgba(255,255,255,0.02)',
                      borderColor:
                        language === lang.code
                          ? 'rgba(34,211,238,0.3)'
                          : 'rgba(255,255,255,0.05)',
                      color:
                        language === lang.code
                          ? '#22d3ee'
                          : 'rgba(255,255,255,0.35)',
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    title={lang.nativeName}
                  >
                    <span className="text-xs">{lang.flag}</span>
                    <span>{lang.nativeName}</span>
                  </motion.button>
                ))}
                {/* More languages button */}
                <motion.button
                  onClick={() => setSettingsOpen(true)}
                  className="flex items-center gap-1 px-2 py-1 rounded-full whitespace-nowrap border text-[10px] text-cyan-400/60 border-cyan-500/10 hover:bg-cyan-500/5"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  +{LANGUAGES.length - 10} more
                </motion.button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-hidden">
              <ScrollArea ref={scrollRef} className="h-full">
                <div className="p-4 space-y-4 min-h-full">
                  {messages.length === 0 && !isLoading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex flex-col items-center justify-center py-12 gap-6"
                    >
                      <div className="text-center space-y-2">
                        <MessageCircle className="h-10 w-10 text-gray-700 mx-auto" />
                        <p className="text-sm text-gray-600">
                          Mulai percakapan dengan Voice Robot
                        </p>
                        <div className="flex items-center justify-center gap-1.5 mt-1">
                          <span className="text-xs">{currentLanguage.flag}</span>
                          <span className="text-[10px] text-cyan-500/50">{currentLanguage.nativeName}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap justify-center gap-2">
                        {currentLanguage.suggestions.map((suggestion) => (
                          <motion.button
                            key={suggestion}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => sendMessage(suggestion)}
                            className="px-4 py-2 rounded-full text-xs font-medium bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/20 transition-all"
                          >
                            {suggestion}
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  <AnimatePresence mode="popLayout">
                    {messages.map((msg) => (
                      <ChatBubble
                        key={msg.id}
                        message={msg}
                        onSpeak={handleSpeakMessage}
                        isSpeaking={currentlySpeakingId === msg.id}
                        isMuted={isMuted}
                        voiceColor={currentVoiceProfile.color}
                      />
                    ))}
                  </AnimatePresence>

                  {isLoading && <TypingIndicator />}
                </div>
              </ScrollArea>
            </div>

            {/* Input area */}
            <div className="border-t border-white/10 bg-white/5 backdrop-blur-xl p-3">
              <div className="flex items-center gap-2">
                {/* Mic button */}
                <motion.div whileTap={{ scale: 0.9 }}>
                  <Button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`h-10 w-10 rounded-full shrink-0 ${
                      isRecording
                        ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/30'
                        : 'bg-white/10 border border-white/10 hover:bg-white/15 text-gray-400 hover:text-white'
                    }`}
                    size="icon"
                    aria-label={isRecording ? 'Berhenti merekam' : 'Mulai merekam'}
                  >
                    {isRecording ? (
                      <MicOff className="h-4 w-4" />
                    ) : (
                      <Mic className="h-4 w-4" />
                    )}
                  </Button>
                </motion.div>

                {/* Text input */}
                <div className="flex-1 relative">
                  <Input
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey && inputText.trim()) {
                        e.preventDefault()
                        sendMessage(inputText)
                      }
                    }}
                    placeholder={`Ketik pesan... (${currentLanguage.nativeName})`}
                    className="bg-white/5 border-white/10 text-gray-200 placeholder:text-gray-600 focus-visible:border-emerald-500/50 focus-visible:ring-emerald-500/20 h-10 rounded-xl pr-12"
                    disabled={isLoading}
                  />
                  {/* Language badge in input */}
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 pointer-events-none">
                    <span className="text-xs">{currentLanguage.flag}</span>
                  </div>
                </div>

                {/* Send button */}
                <motion.div whileTap={{ scale: 0.9 }}>
                  <Button
                    onClick={() => {
                      if (inputText.trim()) sendMessage(inputText)
                    }}
                    disabled={!inputText.trim() || isLoading}
                    className="h-10 w-10 rounded-full shrink-0 text-white shadow-lg disabled:opacity-40"
                    style={{
                      background: `linear-gradient(135deg, ${currentVoiceProfile.color}, ${currentVoiceProfile.color}cc)`,
                      boxShadow: `0 4px 12px ${currentVoiceProfile.color}33`,
                    }}
                    size="icon"
                    aria-label="Kirim pesan"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </motion.div>

                {/* Playback controls */}
                {(robotState === 'speaking' || isPaused) && (
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    className="flex items-center gap-1.5"
                  >
                    <Button
                      onClick={togglePause}
                      className="h-10 w-10 rounded-full shrink-0 border"
                      size="icon"
                      aria-label={isPaused ? 'Lanjutkan' : 'Jeda'}
                      style={{
                        background: `${currentVoiceProfile.color}20`,
                        borderColor: `${currentVoiceProfile.color}40`,
                        color: currentVoiceProfile.color,
                      }}
                    >
                      {isPaused ? (
                        <Play className="h-4 w-4 ml-0.5" />
                      ) : (
                        <Pause className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      onClick={stopSpeaking}
                      className="h-10 w-10 rounded-full shrink-0 bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30"
                      size="icon"
                      aria-label="Berhenti bicara"
                    >
                      <StopCircle className="h-4 w-4" />
                    </Button>
                  </motion.div>
                )}
              </div>
            </div>
          </main>

          {/* Desktop settings sidebar */}
          <aside className="hidden lg:flex w-80 border-l border-white/10 bg-white/5 backdrop-blur-xl flex-col">
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Settings className="h-4 w-4" style={{ color: currentVoiceProfile.color }} />
                <h2 className="text-sm font-semibold text-gray-300">Pengaturan Suara</h2>
              </div>
              <p className="text-[11px] text-gray-600 mt-1">Pilih bahasa & suara, atur preferensi robot</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <SettingsContent
                voice={voice}
                onVoiceChange={setVoice}
                speed={speed}
                onSpeedChange={setSpeed}
                volume={volume}
                onVolumeChange={setVolume}
                autoSpeak={autoSpeak}
                onAutoSpeakChange={setAutoSpeak}
                isMuted={isMuted}
                onMuteChange={setIsMuted}
                onPreviewVoice={previewVoice}
                previewingVoice={previewingVoice}
                soundEffects={soundEffects}
                onSoundEffectsChange={setSoundEffects}
                language={language}
                onLanguageChange={handleLanguageChange}
              />
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
