import { useState } from 'react';

const downloadFile = (content, filename, contentType) => {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// ── Color palettes for cards ──
const CARD_COLORS = [
  { bg: 'bg-indigo-50 dark:bg-indigo-950/30', border: 'border-indigo-200 dark:border-indigo-800/50', glow: 'hover:shadow-indigo-200/50 dark:hover:shadow-indigo-500/20', accent: 'text-indigo-600 dark:text-indigo-400', ring: 'ring-indigo-400/30' },
  { bg: 'bg-violet-50 dark:bg-violet-950/30', border: 'border-violet-200 dark:border-violet-800/50', glow: 'hover:shadow-violet-200/50 dark:hover:shadow-violet-500/20', accent: 'text-violet-600 dark:text-violet-400', ring: 'ring-violet-400/30' },
  { bg: 'bg-sky-50 dark:bg-sky-950/30', border: 'border-sky-200 dark:border-sky-800/50', glow: 'hover:shadow-sky-200/50 dark:hover:shadow-sky-500/20', accent: 'text-sky-600 dark:text-sky-400', ring: 'ring-sky-400/30' },
  { bg: 'bg-amber-50 dark:bg-amber-950/30', border: 'border-amber-200 dark:border-amber-800/50', glow: 'hover:shadow-amber-200/50 dark:hover:shadow-amber-500/20', accent: 'text-amber-600 dark:text-amber-400', ring: 'ring-amber-400/30' },
  { bg: 'bg-rose-50 dark:bg-rose-950/30', border: 'border-rose-200 dark:border-rose-800/50', glow: 'hover:shadow-rose-200/50 dark:hover:shadow-rose-500/20', accent: 'text-rose-600 dark:text-rose-400', ring: 'ring-rose-400/30' },
  { bg: 'bg-emerald-50 dark:bg-emerald-950/30', border: 'border-emerald-200 dark:border-emerald-800/50', glow: 'hover:shadow-emerald-200/50 dark:hover:shadow-emerald-500/20', accent: 'text-emerald-600 dark:text-emerald-400', ring: 'ring-emerald-400/30' },
  { bg: 'bg-cyan-50 dark:bg-cyan-950/30', border: 'border-cyan-200 dark:border-cyan-800/50', glow: 'hover:shadow-cyan-200/50 dark:hover:shadow-cyan-500/20', accent: 'text-cyan-600 dark:text-cyan-400', ring: 'ring-cyan-400/30' },
  { bg: 'bg-fuchsia-50 dark:bg-fuchsia-950/30', border: 'border-fuchsia-200 dark:border-fuchsia-800/50', glow: 'hover:shadow-fuchsia-200/50 dark:hover:shadow-fuchsia-500/20', accent: 'text-fuchsia-600 dark:text-fuchsia-400', ring: 'ring-fuchsia-400/30' },
  { bg: 'bg-teal-50 dark:bg-teal-950/30', border: 'border-teal-200 dark:border-teal-800/50', glow: 'hover:shadow-teal-200/50 dark:hover:shadow-teal-500/20', accent: 'text-teal-600 dark:text-teal-400', ring: 'ring-teal-400/30' },
  { bg: 'bg-orange-50 dark:bg-orange-950/30', border: 'border-orange-200 dark:border-orange-800/50', glow: 'hover:shadow-orange-200/50 dark:hover:shadow-orange-500/20', accent: 'text-orange-600 dark:text-orange-400', ring: 'ring-orange-400/30' },
];

// ─────────────────────────────────────────────
// SUMMARY CARD
// The backend returns: { summary: "plain text" }
// We render the raw text beautifully with formatting
// ─────────────────────────────────────────────
export function SummaryCard({ data }) {
  // data is a plain text string from generate_summary
  if (!data) return null;

  // Split on newlines and render each line
  const lines = typeof data === 'string'
    ? data.split('\n').filter((l) => l.trim())
    : [];

  if (lines.length === 0) return null;

  return (
    <div className="animate-slide-up space-y-3">
      <div className="flex items-center justify-between space-x-2">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center">
            <span className="text-xs">📝</span>
          </div>
          <span className="text-xs font-bold uppercase tracking-widest text-brand-500 dark:text-brand-400">
            Summary
          </span>
        </div>
        <button
          onClick={() => downloadFile(data, 'summary.txt', 'text/plain')}
          className="text-xs font-medium px-2.5 py-1 rounded-md bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
        >
          ⬇️ Export
        </button>
      </div>

      <div className="space-y-2">
        {lines.map((line, idx) => {
          const trimmed = line.trim();

          // Detect headings (lines ending with : or starting with #)
          if (trimmed.endsWith(':') || trimmed.startsWith('#')) {
            const clean = trimmed.replace(/^#+\s*/, '').replace(/:$/, '');
            return (
              <h4 key={idx} className="text-sm font-bold text-surface-800 dark:text-surface-100 pt-2 first:pt-0">
                {clean}
              </h4>
            );
          }

          // Detect bullet points
          if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*') || /^\d+\./.test(trimmed)) {
            const clean = trimmed.replace(/^[-•*]\s*/, '').replace(/^\d+\.\s*/, '');
            // Detect bold text marked with **
            const parts = clean.split(/\*\*(.*?)\*\*/g);

            return (
              <div key={idx} className="flex space-x-2.5 pl-1">
                <span className="text-brand-400 mt-0.5 shrink-0 text-sm">›</span>
                <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed">
                  {parts.map((part, i) =>
                    i % 2 === 1
                      ? <strong key={i} className="font-semibold text-surface-800 dark:text-surface-100">{part}</strong>
                      : <span key={i}>{part}</span>
                  )}
                </p>
              </div>
            );
          }

          // Regular paragraph — also handle bold
          const parts = trimmed.split(/\*\*(.*?)\*\*/g);
          return (
            <p key={idx} className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed">
              {parts.map((part, i) =>
                i % 2 === 1
                  ? <strong key={i} className="font-semibold text-surface-800 dark:text-surface-100">{part}</strong>
                  : <span key={i}>{part}</span>
              )}
            </p>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// QUIZ CARD
// The backend returns: { quiz: [{ question, options, answer }] }
// Interactive: click any option to reveal the correct answer
// ─────────────────────────────────────────────
export function QuizCard({ data }) {
  const [selected, setSelected] = useState({});
  const [revealed, setRevealed] = useState({});

  // data is an array of { question, options, answer }
  const questions = Array.isArray(data) ? data : [];
  if (questions.length === 0) return null;

  const handleSelect = (qIdx, option) => {
    if (revealed[qIdx]) return; // Already revealed
    setSelected((p) => ({ ...p, [qIdx]: option }));
    setRevealed((p) => ({ ...p, [qIdx]: true }));
  };

  return (
    <div className="animate-slide-up space-y-4">
      <div className="flex items-center justify-between space-x-2">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center">
            <span className="text-xs">🎓</span>
          </div>
          <span className="text-xs font-bold uppercase tracking-widest text-brand-500 dark:text-brand-400">
            Quiz · {questions.length} questions
          </span>
        </div>
        <button
          onClick={() => downloadFile(JSON.stringify(questions, null, 2), 'quiz.json', 'application/json')}
          className="text-xs font-medium px-2.5 py-1 rounded-md bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
        >
          ⬇️ Export
        </button>
      </div>

      {questions.map((q, qIdx) => {
        const correct = q.answer || q.correct_answer;
        const isRevealed = revealed[qIdx];
        const userPick = selected[qIdx];

        return (
          <div
            key={qIdx}
            className="p-4 rounded-xl bg-surface-50/80 dark:bg-surface-800/40 border border-surface-100 dark:border-surface-700/40"
          >
            <p className="font-semibold text-surface-800 dark:text-surface-100 mb-3 text-[15px]">
              <span className="text-brand-500 mr-1.5">{qIdx + 1}.</span>
              {q.question}
            </p>

            <div className="space-y-1.5">
              {q.options?.map((opt, oIdx) => {
                const isCorrect = opt === correct;
                const isUserPick = opt === userPick;
                const isWrong = isRevealed && isUserPick && !isCorrect;

                let optClass = 'border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 text-surface-700 dark:text-surface-300';
                if (isRevealed && isCorrect) {
                  optClass = 'border-emerald-400 dark:border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300';
                } else if (isWrong) {
                  optClass = 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400';
                } else if (isRevealed) {
                  optClass = 'border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800 text-surface-400 dark:text-surface-500';
                }

                return (
                  <button
                    key={oIdx}
                    onClick={() => handleSelect(qIdx, opt)}
                    disabled={isRevealed}
                    className={`
                      w-full text-left p-3 rounded-lg border text-sm transition-all duration-200
                      ${optClass}
                      ${!isRevealed ? 'hover:border-brand-300 dark:hover:border-brand-600 cursor-pointer' : ''}
                    `}
                  >
                    <span className="flex items-center space-x-2">
                      {isRevealed && isCorrect && <span className="text-emerald-500 shrink-0">✓</span>}
                      {isWrong && <span className="text-red-500 shrink-0">✗</span>}
                      <span>{opt}</span>
                    </span>
                  </button>
                );
              })}
            </div>

            {isRevealed && q.explanation && (
              <p className="text-xs text-surface-500 dark:text-surface-400 mt-3 pt-2.5 border-t border-surface-100 dark:border-surface-700/40 animate-fade-in leading-relaxed">
                <span className="font-bold text-surface-600 dark:text-surface-300">Explanation: </span>
                {q.explanation}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────
// FLASHCARDS
// The backend returns: { flashcards: [{ term, definition }] }
// Fixed-size cards, 2 per row, each a different color, click to flip
// ─────────────────────────────────────────────
export function FlashcardsCard({ data }) {
  const [flipped, setFlipped] = useState({});

  const cards = Array.isArray(data) ? data : [];
  if (cards.length === 0) return null;

  return (
    <div className="animate-slide-up space-y-4">
      <div className="flex items-center justify-between space-x-2">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center">
            <span className="text-xs">🃏</span>
          </div>
          <span className="text-xs font-bold uppercase tracking-widest text-brand-500 dark:text-brand-400">
            Flashcards · {cards.length} cards
          </span>
        </div>
        <button
          onClick={() => downloadFile(JSON.stringify(cards, null, 2), 'flashcards.json', 'application/json')}
          className="text-xs font-medium px-2.5 py-1 rounded-md bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
        >
          ⬇️ Export
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {cards.map((card, idx) => {
          const color = CARD_COLORS[idx % CARD_COLORS.length];
          const isFlipped = flipped[idx];

          return (
            <button
              key={idx}
              onClick={() => setFlipped((p) => ({ ...p, [idx]: !p[idx] }))}
              className={`
                text-left rounded-xl border transition-all duration-300 cursor-pointer
                h-44 p-5 flex flex-col justify-between
                shadow-sm hover:shadow-lg
                ${color.border} ${color.glow}
                ${isFlipped
                  ? `${color.bg} ring-2 ${color.ring}`
                  : 'bg-white dark:bg-surface-800'
                }
              `}
            >
              <div className="flex-1 flex flex-col">
                <span className={`text-[10px] font-bold uppercase tracking-widest mb-2 ${color.accent}`}>
                  {isFlipped ? 'Definition' : 'Term'}
                </span>
                <p className={`text-sm leading-relaxed flex-1 ${
                  isFlipped
                    ? 'text-surface-700 dark:text-surface-300'
                    : 'text-surface-800 dark:text-surface-100 font-semibold'
                }`}>
                  {isFlipped ? card.definition : card.term}
                </p>
              </div>
              <p className={`text-[10px] mt-2 ${color.accent} opacity-60`}>
                {isFlipped ? 'Click to see term' : 'Click to reveal'}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
