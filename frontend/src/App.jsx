import { useEffect } from 'react';
import { useStore } from './store/useStore';
import { apiClient } from './api/client';
import UploadZone from './components/UploadZone';
import ModeSelector from './components/ModeSelector';
import ChatPanel from './components/ChatPanel';
import TaskPanel from './components/TaskPanel';

function App() {
  const { documents, setDocuments, activeDocument, setActiveDocument, currentMode } = useStore();

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const response = await apiClient.get('/documents');
        setDocuments(response.data);
        if (response.data.length > 0) {
          setActiveDocument(response.data[0]);
        }
      } catch (error) {
        console.error("Failed to fetch documents", error);
      }
    };
    fetchDocs();
  }, []);

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-800">
      
      {/* LEFT SIDEBAR: Document Library */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm z-10">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
            DocMind OS
          </h1>
          <p className="text-xs font-medium text-gray-400 mt-1 tracking-wide uppercase">Intelligence Workspace</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
            Your Documents
          </h2>
          {documents.length === 0 ? (
            <p className="text-sm text-gray-400 italic px-2">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-1">
              {documents.map((doc) => (
                <li 
                  key={doc._id} 
                  onClick={() => setActiveDocument(doc)}
                  className={`p-3 rounded-lg text-sm truncate cursor-pointer border transition-colors ${
                    activeDocument?._id === doc._id 
                      ? 'bg-blue-50 border-blue-200 text-blue-700 font-medium' 
                      : 'bg-white border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-200'
                  }`}
                >
                  📄 {doc.filename}
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* Upload Component */}
        <UploadZone />
      </aside>

      {/* RIGHT MAIN AREA: AI Workspace */}
      <main className="flex-1 flex flex-col bg-gray-50">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 shadow-sm z-0">
          <h2 className="text-lg font-medium text-gray-700">
            {activeDocument ? (
              <span className="flex items-center space-x-2">
                <span>Analyzing:</span>
                <span className="text-blue-600 font-semibold">{activeDocument.filename}</span>
              </span>
            ) : "Select or upload a document to begin"}
          </h2>
          {activeDocument && <ModeSelector />}
        </header>
        
        <div className="flex-1 p-8 overflow-hidden">
          {!activeDocument ? (
             <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
               <div className="text-6xl mb-4 opacity-80">🧠</div>
               <h3 className="text-xl font-medium text-gray-700">AI Intelligence Core</h3>
               <p className="text-gray-500 mt-2 leading-relaxed">Upload a document on the left to trigger the workflow engine, generate summaries, and ask questions.</p>
             </div>
          ) : (
             currentMode === 'chat' ? <ChatPanel /> : <TaskPanel />
          )}
        </div>
      </main>

    </div>
  )
}

export default App;
