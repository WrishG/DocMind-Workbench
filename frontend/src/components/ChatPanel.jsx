import { useState, useRef, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useStore } from '../store/useStore';
import { SummaryCard, QuizCard, FlashcardsCard } from './ResultCards';

const MODES = [
  { id: 'chat',       label: 'Chat',       icon: '💬', description: 'Ask questions' },
  { id: 'summarize',  label: 'Summarize',  icon: '📝', description: 'Key insights' },
  { id: 'quiz',       label: 'Quiz',       icon: '🎓', description: 'Test knowledge' },
  { id: 'flashcards', label: 'Flashcards', icon: '🃏', description: 'Study cards' },
];

export default function ChatPanel() {
  const { activeDocument, getMessages, addMessage } = useStore();
  const [input, setInput] = useState('');
  const [activeMode, setActiveMode] = useState('chat');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const messages = getMessages();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeDocument]);

  // Handle sending a message or triggering a task
  const handleSend = async () => {
    if (!activeDocument) return;
    const filename = activeDocument.filename;

    if (activeMode === 'chat') {
      // Chat mode: requires user input
      if (!input.trim()) return;
      const question = input.trim();

      addMessage({ role: 'user', content: question });
      setInput('');
      setIsLoading(true);

      try {
        const res = await apiClient.post('/ask', { question });
        addMessage({
          role: 'assistant',
          type: 'chat',
          content: res.data.Answer,
          sources: res.data.Sources,
        });
      } catch (err) {
        addMessage({
          role: 'assistant',
          type: 'error',
          content: 'Failed to get a response. Is the backend running?',
        });
      } finally {
        setIsLoading(false);
      }
    } else {
      // Task mode: no user input needed, just trigger the AI
      const modeLabel = MODES.find((m) => m.id === activeMode)?.label || activeMode;
      addMessage({ role: 'user', content: `Generate ${modeLabel} for ${filename}` });
      setIsLoading(true);

      try {
        const res = await apiClient.post(`/${activeMode}`, { 
          filename: filename,
          document_id: activeDocument._id 
        });
        addMessage({
          role: 'assistant',
          type: activeMode,
          data: res.data,
        });
      } catch (err) {
        const is503 = err?.response?.status === 503;
        addMessage({
          role: 'assistant',
          type: 'error',
          content: is503
            ? 'The AI model is temporarily overloaded. Please try again in a moment.'
            : `Failed to generate ${modeLabel}. Check the backend logs.`,
          retryMode: activeMode,
        });
      } finally {
        setIsLoading(false);
        setActiveMode('chat'); // Reset back to chat after running a task
      }
    }
  };

  // Retry a failed task
  const handleRetry = (mode) => {
    setActiveMode(mode);
    setTimeout(() => handleSend(), 50);
  };

  // Render a single message bubble
  const renderMessage = (msg, idx) => {
    // User message
    if (msg.role === 'user') {
      return (
        <div key={idx} className="flex justify-end animate-slide-up">
          <div className="max-w-[75%] rounded-2xl rounded-br-md px-5 py-3 bg-brand-600 text-white shadow-md shadow-brand-600/10">
            <p className="text-[15px] leading-relaxed">{msg.content}</p>
          </div>
        </div>
      );
    }

    // AI message
    return (
      <div key={idx} className="flex justify-start animate-slide-up">
        <div className={`rounded-2xl rounded-bl-md px-5 py-4 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700/50 shadow-sm ${
          msg.type === 'chat' || msg.type === 'error' ? 'max-w-[80%]' : 'max-w-[95%] w-full'
        }`}>
          {/* Regular chat response */}
          {msg.type === 'chat' && (
            <>
              <p className="text-[15px] leading-relaxed text-surface-800 dark:text-surface-200 whitespace-pre-wrap">
                {msg.content}
              </p>
              {msg.sources?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-surface-100 dark:border-surface-700/50">
                  <p className="text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-widest mb-1.5">
                    Sources
                  </p>
                  {msg.sources.map((src, i) => (
                    <p key={i} className="text-xs text-surface-500 dark:text-surface-400 leading-relaxed">
                      <span className="text-brand-400 mr-1">›</span>{src}
                    </p>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Summary result */}
          {msg.type === 'summarize' && <SummaryCard data={msg.data?.summary} />}

          {/* Quiz result */}
          {msg.type === 'quiz' && <QuizCard data={msg.data?.quiz} />}

          {/* Flashcards result */}
          {msg.type === 'flashcards' && <FlashcardsCard data={msg.data?.flashcards} />}

          {/* Raw text fallback */}
          {msg.type === 'summarize' && !msg.data?.summary && msg.data?.raw_text && (
            <pre className="text-sm text-surface-700 dark:text-surface-300 whitespace-pre-wrap">{msg.data.raw_text}</pre>
          )}
          {(msg.type === 'quiz' || msg.type === 'flashcards') && !msg.data?.quiz && !msg.data?.flashcards && msg.data?.raw_text && (
            <pre className="text-sm text-surface-700 dark:text-surface-300 whitespace-pre-wrap">{msg.data.raw_text}</pre>
          )}

          {/* Error with retry */}
          {msg.type === 'error' && (
            <div className="flex items-start space-x-3">
              <span className="text-lg mt-0.5">⚠️</span>
              <div>
                <p className="text-sm text-red-600 dark:text-red-400">{msg.content}</p>
                {msg.retryMode && (
                  <button
                    onClick={() => handleRetry(msg.retryMode)}
                    className="mt-2 text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline"
                  >
                    ↻ Try again
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-100 to-brand-200 dark:from-brand-950/50 dark:to-brand-900/30 flex items-center justify-center mb-5">
              <span className="text-3xl">✨</span>
            </div>
            <h3 className="text-lg font-semibold text-surface-700 dark:text-surface-200">
              What would you like to do?
            </h3>
            <p className="text-sm text-surface-400 dark:text-surface-500 mt-1 max-w-md text-center leading-relaxed">
              Ask a question, generate a summary, take a quiz, or create flashcards.
              Select a mode below and press Enter.
            </p>
          </div>
        )}

        {messages.map(renderMessage)}

        {isLoading && (
          <div className="flex justify-start animate-slide-up">
            <div className="bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700/50 rounded-2xl rounded-bl-md px-5 py-3.5 shadow-sm">
              <div className="flex items-center space-x-2.5">
                <div className="flex space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-thinking" style={{ animationDelay: '0s' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-thinking" style={{ animationDelay: '0.2s' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-thinking" style={{ animationDelay: '0.4s' }} />
                </div>
                <span className="text-sm text-surface-400 dark:text-surface-500">
                  {activeMode === 'chat' ? 'Thinking…' : 'Analyzing document…'}
                </span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="px-6 pb-5 pt-2">
        {/* Mode Pills */}
        <div className="flex items-center space-x-1.5 mb-3">
          {MODES.map((mode) => (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              className={`
                flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                ${activeMode === mode.id
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/20'
                  : 'bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700 hover:text-surface-700 dark:hover:text-surface-200'
                }
              `}
            >
              <span>{mode.icon}</span>
              <span>{mode.label}</span>
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="flex items-center space-x-3 p-2 rounded-2xl bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 focus-within:border-brand-400 dark:focus-within:border-brand-500 transition-colors shadow-sm">
          {activeMode === 'chat' ? (
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask anything about this document…"
              disabled={isLoading}
              className="flex-1 px-3 py-2 bg-transparent text-surface-800 dark:text-surface-100 placeholder-surface-400 dark:placeholder-surface-500 focus:outline-none text-[15px] disabled:opacity-50"
            />
          ) : (
            <div className="flex-1 px-3 py-2 text-[15px] text-surface-400 dark:text-surface-500">
              Press <kbd className="px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300 text-xs font-mono border border-surface-200 dark:border-surface-600">Enter</kbd> to generate {MODES.find(m => m.id === activeMode)?.label.toLowerCase()} for <span className="text-brand-500 dark:text-brand-400 font-medium">{activeDocument?.filename}</span>
            </div>
          )}

          <button
            onClick={handleSend}
            disabled={isLoading || (activeMode === 'chat' && !input.trim())}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md shrink-0"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
