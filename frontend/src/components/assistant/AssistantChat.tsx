'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { api } from '@/lib/api';
import { Mic, MicOff, Send, Volume2, VolumeX, RotateCcw, Loader2 } from 'lucide-react';

type MicState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'RESPONDING' | 'ERROR';
type Msg = { role: 'user' | 'assistant'; text: string; language?: string; navigate_to?: string };

const QUICK_ACTIONS = [
  'Why is my score low?',
  'Show missing documents',
  'Show high-risk alerts',
  'What do I need to prepare?',
  'Upcoming deadlines',
  'Explain my tax position',
  'What if I invest ₹50,000?',
  'Summarize my finances',
];

const langLabel: Record<string, string> = {
  en: 'English', ta: 'தமிழ்', hi: 'हिन्दी', 'ta-mix': 'Tamil + English', 'hi-mix': 'Hindi + English',
};

function langToVoice(lang?: string): string {
  if (lang?.startsWith('ta')) return 'ta-IN';
  if (lang?.startsWith('hi')) return 'hi-IN';
  return 'en-IN';
}

export function AssistantChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'assistant', text: 'Hi! I can help you understand your tax readiness, documents, risks, deadlines and scenarios.' },
  ]);
  const [input, setInput] = useState('');
  const [mic, setMic] = useState<MicState>('IDLE');
  const [micError, setMicError] = useState('');
  const [muted, setMuted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [heard, setHeard] = useState('');
  const recRef = useRef<any>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, busy]);

  useEffect(() => {
    api.chatHistory(20).then((h: any) => {
      const items: Msg[] = (h?.messages || []).map((m: any) => ({ role: m.role, text: m.text, language: m.language }));
      if (items.length) setMessages(items.slice(-20));
    }).catch(() => {});
    return () => { try { recRef.current?.abort(); } catch {} try { window.speechSynthesis?.cancel(); } catch {} };
  }, []);

  const speak = useCallback((text: string, lang?: string) => {
    if (muted || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.slice(0, 500));
      u.lang = langToVoice(lang);
      setMic('RESPONDING');
      u.onend = () => setMic((s) => (s === 'RESPONDING' ? 'IDLE' : s));
      u.onerror = () => setMic('IDLE');
      window.speechSynthesis.speak(u);
    } catch { setMic('IDLE'); }
  }, [muted]);

  const send = useCallback(async (raw: string, viaVoice = false) => {
    const text = raw.trim();
    if (!text || busy) return;
    setBusy(true);
    if (viaVoice) setMic('PROCESSING');
    setMessages((m) => [...m, { role: 'user', text }]);
    setInput('');
    try {
      const out = await api.chatMessage(text);
      setMessages((m) => [...m, { role: 'assistant', text: out.response, language: out.language, navigate_to: out.navigate_to }]);
      if (viaVoice || mic === 'PROCESSING') speak(out.response, out.language);
      else setMic('IDLE');
    } catch (e: any) {
      const msg = e?.response?.status === 429
        ? 'Too many requests. Please try again shortly.'
        : "I'm unable to access your TaxShield data right now. Please try again shortly.";
      setMessages((m) => [...m, { role: 'assistant', text: msg }]);
      setMic('ERROR');
      setMicError(msg);
    } finally {
      setBusy(false);
      if (!viaVoice) setMic((s) => (s === 'PROCESSING' ? 'IDLE' : s));
    }
  }, [busy, mic, speak]);

  const toggleMic = useCallback(() => {
    const SR: any = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setMic('ERROR');
      setMicError('Voice input is not supported in this browser. Please type instead.');
      return;
    }
    if (mic === 'LISTENING') {
      try { recRef.current?.stop(); } catch {}
      setMic('IDLE');
      return;
    }
    try {
      const rec = new SR();
      recRef.current = rec;
      rec.lang = 'ta-IN';
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      // Cycle ta-IN -> hi-IN -> en-IN is handled by auto-detection server-side;
      // start with Tamil since it covers code-mix well, fallback on error below.
      setMic('LISTENING');
      setMicError('');
      setHeard('');
      rec.onresult = async (ev: any) => {
        const transcript = ev.results?.[0]?.[0]?.transcript || '';
        setHeard(transcript);
        try { await api.voiceTranscribe(transcript); } catch {}
        await send(transcript, true);
      };
      rec.onerror = () => {
        setMic('ERROR');
        setMicError("Sorry, I couldn't understand the voice input. Please try again.");
      };
      rec.onend = () => setMic((s) => (s === 'LISTENING' ? 'IDLE' : s));
      rec.start();
    } catch {
      setMic('ERROR');
      setMicError("Sorry, I couldn't start voice input. Please try again.");
    }
  }, [mic, send]);

  const micHint = mic === 'LISTENING' ? 'Listening...' : mic === 'PROCESSING' ? 'Understanding...' : mic === 'RESPONDING' ? 'Speaking...' : mic === 'ERROR' ? (micError || 'Error — try again') : 'Tap to speak (தமிழ் / हिन्दी / English)';

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <h1 className="text-lg font-semibold text-gray-900">TaxShield AI Assistant</h1>
        <p className="text-sm text-gray-500">Your tax-readiness companion</p>
      </div>

      <div className="px-4 pt-3 flex flex-wrap gap-2" aria-label="Quick actions">
        {QUICK_ACTIONS.map((q) => (
          <button key={q} onClick={() => send(q)} disabled={busy}
            className="text-xs px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700">
            {q}
          </button>
        ))}
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3" role="log" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              m.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-900'}`}>
              {m.language && m.role === 'assistant' && (
                <div className="text-[11px] opacity-70 mb-1">{langLabel[m.language] || m.language}</div>
              )}
              <div className="whitespace-pre-wrap">{m.text}</div>
              {m.role === 'assistant' && m.navigate_to && (
                <button onClick={() => router.push(m.navigate_to!)}
                  className="mt-2 text-xs font-medium underline underline-offset-2">View Details</button>
              )}
              {m.role === 'assistant' && (
                <button
                  onClick={() => speak(m.text, m.language)}
                  className="mt-1.5 flex items-center gap-1 text-xs opacity-70 hover:opacity-100"
                  aria-label="Replay response">
                  <RotateCcw className="h-3 w-3" /> Replay
                </button>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl px-4 py-2.5 text-sm text-gray-500 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Thinking...
            </div>
          </div>
        )}
        {heard && <p className="text-xs text-gray-400 px-1">Heard: “{heard}”</p>}
      </div>

      <div className="px-4 pb-1">
        <p className="text-xs text-gray-500 text-center" role="status">
          {mic === 'LISTENING' && <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />{micHint}</span>}
          {mic !== 'LISTENING' && micHint}
        </p>
      </div>
      <form
        className="p-3 border-t border-gray-100 flex items-center gap-2"
        onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <button type="button" onClick={toggleMic} aria-label="Microphone"
          className={`p-2.5 rounded-full border ${mic === 'LISTENING' ? 'bg-red-50 border-red-300 text-red-600' : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'}`}>
          {mic === 'LISTENING' ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type in English / தமிழ் / हिन्दी..."
          className="flex-1 rounded-full border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="Type message"
        />
        <button type="button" onClick={() => { setMuted((v) => !v); try { window.speechSynthesis?.cancel(); } catch {} }}
          className="p-2.5 rounded-full bg-gray-50 border border-gray-200 text-gray-700 hover:bg-gray-100" aria-label="Mute voice response">
          {muted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
        </button>
        <button type="submit" disabled={busy || !input.trim()} aria-label="Send"
          className="p-2.5 rounded-full bg-primary-600 text-white disabled:opacity-50 hover:bg-primary-700">
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}

