import { useState } from 'react';
import { apiClient } from '../api/client';
import { useStore } from '../store/useStore';

export default function TaskPanel() {
  const { activeDocument, currentMode } = useStore();
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRunTask = async () => {
    if (!activeDocument) return;
    setIsLoading(true);
    setResult(null);

    try {
      // If mode is 'summarize', call /summarize. If 'quiz', call /quiz
      const response = await apiClient.post(`/${currentMode}`, { 
        filename: activeDocument.filename 
      });
      setResult(response.data);
    } catch (error) {
      console.error(`Task failed:`, error);
      setResult({ error: "Failed to generate." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6 bg-white p-6 rounded-xl border border-gray-200 flex justify-between items-center shadow-sm">
        <div>
          <h3 className="text-lg font-medium text-gray-800">
            {currentMode === 'summarize' ? 'Executive Summary' : 'Knowledge Quiz'}
          </h3>
          <p className="text-sm text-gray-500">
            Extract insights from <span className="font-semibold text-blue-600">{activeDocument?.filename}</span>
          </p>
        </div>
        <button
          onClick={handleRunTask}
          disabled={isLoading || !activeDocument}
          className="px-6 py-2.5 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {isLoading ? 'Generating...' : `Generate ${currentMode === 'summarize' ? 'Summary' : 'Quiz'}`}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-200 p-8">
        {!result && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <span className="text-4xl mb-3">{currentMode === 'summarize' ? '📝' : '🎓'}</span>
            <p>Click generate to process the document.</p>
          </div>
        )}

        {isLoading && (
          <div className="h-full flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
            <p className="text-gray-500 animate-pulse">Analyzing document structure...</p>
          </div>
        )}

        {result && result.summary && (
          <div className="max-w-4xl">
            <h2 className="text-2xl font-bold mb-4">{result.summary.title}</h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              {result.summary.key_points.map((point, idx) => (
                <div key={idx} className="flex space-x-3">
                  <span className="text-blue-600 mt-1">•</span>
                  <p>{point}</p>
                </div>
              ))}
            </div>
            <p className="mt-8 pt-4 border-t border-gray-100 text-gray-600 italic">
              {result.summary.conclusion}
            </p>
          </div>
        )}

        {result && result.quiz && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold mb-6">Knowledge Check</h2>
            {result.quiz.questions.map((q, qIdx) => (
              <div key={qIdx} className="bg-gray-50 p-6 rounded-xl border border-gray-100">
                <p className="font-medium text-lg text-gray-800 mb-4">{qIdx + 1}. {q.question}</p>
                <div className="space-y-2">
                  {q.options.map((opt, oIdx) => (
                    <div key={oIdx} className={`p-3 rounded-lg border ${
                      opt === q.correct_answer 
                        ? 'border-green-300 bg-green-50' 
                        : 'border-gray-200 bg-white'
                    }`}>
                      <span className="text-gray-700">{opt}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-sm text-gray-500"><span className="font-semibold text-gray-700">Explanation:</span> {q.explanation}</p>
              </div>
            ))}
          </div>
        )}

        {result && result.error && (
          <div className="text-red-500">{result.error}</div>
        )}
      </div>
    </div>
  );
}
