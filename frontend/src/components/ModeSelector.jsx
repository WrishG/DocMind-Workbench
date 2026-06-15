import { useStore } from '../store/useStore';

export default function ModeSelector() {
  const { currentMode, setCurrentMode } = useStore();

  const modes = [
    { id: 'chat', label: 'Q&A Chat', icon: '💬' },
    { id: 'summarize', label: 'Summary', icon: '📝' },
    { id: 'quiz', label: 'Quiz', icon: '🎓' }
  ];

  return (
    <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg w-fit">
      {modes.map(mode => (
        <button
          key={mode.id}
          onClick={() => setCurrentMode(mode.id)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2
            ${currentMode === mode.id 
              ? 'bg-white text-blue-700 shadow-sm border border-gray-200' 
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200'
            }`}
        >
          <span>{mode.icon}</span>
          <span>{mode.label}</span>
        </button>
      ))}
    </div>
  );
}
