import { useEffect } from 'react';
import { useStore } from './store/useStore';
import { apiClient } from './api/client';
import UploadZone from './components/UploadZone';
import ChatPanel from './components/ChatPanel';
import ThemeToggle from './components/ThemeToggle';
import Dashboard from './components/Dashboard';

function App() {
  const { documents, setDocuments, activeDocument, setActiveDocument, theme } = useStore();

  // Apply dark class to <html>
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  // Fetch documents on load
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await apiClient.get('/documents');
        setDocuments(res.data);
        if (res.data.length > 0 && !activeDocument) {
          // Do not auto-select, allow the user to see the Dashboard
        }
      } catch (err) {
        console.error("Failed to fetch documents", err);
      }
    };
    fetchDocs();
  }, []);

  // Delete a document from the sidebar
  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/documents/${docId}`);
      const res = await apiClient.get('/documents');
      setDocuments(res.data);
      if (activeDocument?._id === docId) {
        setActiveDocument(res.data.length > 0 ? res.data[0] : null);
      }
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  return (
    <div className="flex h-screen bg-surface-50 dark:bg-surface-950 text-surface-800 dark:text-surface-200 transition-colors duration-300">

      {/* ─── SIDEBAR ─── */}
      <aside className="w-[280px] flex flex-col border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 shrink-0">

        {/* Brand */}
        <div className="px-5 pt-5 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-sm shadow-brand-500/20">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <div>
                <h1 className="text-[15px] font-bold text-surface-900 dark:text-white tracking-tight">DocMind</h1>
                <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-surface-400 dark:text-surface-500">Workbench</p>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </div>

        <div className="mx-4 h-px bg-surface-100 dark:bg-surface-800" />

        {/* Document List */}
        <div className="flex-1 overflow-y-auto p-3">
          <p className="text-[11px] font-semibold text-surface-400 dark:text-surface-500 uppercase tracking-wider px-2 mb-2">
            Documents
          </p>

          {documents.length === 0 ? (
            <div className="px-2 py-10 text-center">
              <div className="w-12 h-12 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-surface-400 dark:text-surface-500">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" strokeLinecap="round" strokeLinejoin="round"/>
                  <polyline points="14 2 14 8 20 8" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <p className="text-sm text-surface-400 dark:text-surface-500 font-medium">No documents yet</p>
              <p className="text-xs text-surface-300 dark:text-surface-600 mt-0.5">Upload a PDF to get started</p>
            </div>
          ) : (
            <ul className="space-y-0.5">
              {documents.map((doc) => (
                <li
                  key={doc._id}
                  onClick={() => setActiveDocument(doc)}
                  className={`
                    group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer
                    transition-all duration-150 text-sm
                    ${activeDocument?._id === doc._id
                      ? 'bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300'
                      : 'text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800'
                    }
                  `}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <svg
                      width="14" height="14" viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                      className={`shrink-0 ${
                        activeDocument?._id === doc._id
                          ? 'stroke-brand-500'
                          : 'stroke-surface-400 dark:stroke-surface-500'
                      }`}
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <span className="truncate font-medium">{doc.filename}</span>
                  </div>

                  {/* Delete button on hover */}
                  <button
                    onClick={(e) => handleDelete(e, doc._id)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-red-100 dark:hover:bg-red-950/40 text-surface-400 hover:text-red-500 dark:hover:text-red-400 transition-all shrink-0"
                    title="Delete document"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Upload */}
        <UploadZone />
      </aside>

      {/* ─── MAIN ─── */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Minimal Top Bar */}
        <header className="h-12 flex items-center px-6 border-b border-surface-200 dark:border-surface-800 bg-white/60 dark:bg-surface-900/60 backdrop-blur-md shrink-0">
          {activeDocument ? (
            <div className="flex items-center space-x-2.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-sm font-medium text-surface-700 dark:text-surface-200 truncate">
                {activeDocument.filename}
              </span>
              <span className="text-xs text-surface-400 dark:text-surface-500">
                · {activeDocument.total_chunks} chunks
              </span>
            </div>
          ) : (
            <span className="text-sm text-surface-400 dark:text-surface-500">
              Select a document to begin
            </span>
          )}
        </header>

        {/* Chat / Workspace */}
        <div className="flex-1 overflow-hidden">
          {!activeDocument ? (
            <Dashboard />
          ) : (
            <ChatPanel />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
