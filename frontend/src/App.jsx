import { useEffect } from 'react';
import { useStore } from './store/useStore';
import { apiClient } from './api/client';

function App() {
  const { documents, setDocuments, activeDocument } = useStore();

  // On page load, fetch the documents from FastAPI
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const response = await apiClient.get('/documents');
        setDocuments(response.data);
      } catch (error) {
        console.error("Failed to fetch documents", error);
      }
    };
    fetchDocs();
  }, []);

  return (
    <div className="flex h-screen bg-gray-100 font-sans text-gray-800">

      {/* LEFT SIDEBAR: Document Library */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
            DocMind OS
          </h1>
          <p className="text-sm text-gray-500 mt-1">Workspace</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Your Documents
          </h2>
          {documents.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li key={doc._id} className="p-3 bg-gray-50 rounded-lg text-sm truncate hover:bg-blue-50 cursor-pointer border border-gray-100">
                  📄 {doc.filename}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Upload Button Placeholder */}
        <div className="p-4 border-t border-gray-100">
          <button className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            + Upload PDF
          </button>
        </div>
      </aside>

      {/* RIGHT MAIN AREA: AI Workspace */}
      <main className="flex-1 flex flex-col">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-8">
          <h2 className="text-lg font-medium">
            {activeDocument ? `Analyzing: ${activeDocument.filename}` : "Select or upload a document to begin"}
          </h2>
        </header>

        <div className="flex-1 p-8 overflow-y-auto flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-4">🧠</div>
            <h3 className="text-xl font-medium text-gray-700">AI Intelligence Core</h3>
            <p className="text-gray-500 mt-2">Upload a document on the left to trigger the workflow engine, generate summaries, and ask questions.</p>
          </div>
        </div>
      </main>

    </div>
  )
}

export default App;
