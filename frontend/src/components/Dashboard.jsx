import React from 'react';
import { useStore } from '../store/useStore';

const Dashboard = () => {
  const { documents, setActiveDocument } = useStore();

  // Metrics calculation
  const totalDocs = documents.length;
  const memorySaved = totalDocs * 350; // 350MB per doc context using Serverless

  return (
    <div className="flex-1 overflow-y-auto bg-surface-50 dark:bg-surface-950 p-8 h-full">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-surface-900 dark:text-white tracking-tight">
              Welcome back to DocMind
            </h1>
            <p className="text-surface-500 dark:text-surface-400 mt-2">
              Your serverless document intelligence platform.
            </p>
          </div>
          <div className="flex gap-4">
            <div className="bg-white dark:bg-surface-900 px-5 py-3 rounded-2xl border border-surface-200 dark:border-surface-800 shadow-sm">
              <p className="text-[11px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-widest">Docs Processed</p>
              <p className="text-2xl font-bold text-brand-500">{totalDocs}</p>
            </div>
            <div className="bg-white dark:bg-surface-900 px-5 py-3 rounded-2xl border border-surface-200 dark:border-surface-800 shadow-sm">
              <p className="text-[11px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-widest">Server RAM Saved</p>
              <p className="text-2xl font-bold text-emerald-500">{memorySaved} MB</p>
            </div>
          </div>
        </div>

        {/* Recent Documents Grid */}
        <div>
          <h2 className="text-lg font-semibold text-surface-800 dark:text-surface-200 mb-4">
            Recent Documents
          </h2>
          
          {documents.length === 0 ? (
            <div className="bg-white dark:bg-surface-900 border border-dashed border-surface-300 dark:border-surface-700 rounded-3xl p-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-surface-400 dark:text-surface-500">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" strokeLinecap="round" strokeLinejoin="round"/>
                  <polyline points="14 2 14 8 20 8" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <p className="text-surface-600 dark:text-surface-300 font-medium">Your library is empty</p>
              <p className="text-sm text-surface-400 dark:text-surface-500 mt-1 max-w-sm mx-auto">
                Upload a PDF using the sidebar to extract intelligence, generate summaries, and build interactive flashcards.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {documents.map(doc => (
                <div 
                  key={doc._id}
                  onClick={() => setActiveDocument(doc)}
                  className="group bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-3xl p-5 hover:border-brand-500/50 hover:shadow-md hover:shadow-brand-500/5 transition-all cursor-pointer flex flex-col h-48"
                >
                  <div className="flex items-start justify-between mb-auto">
                    <div className="p-2.5 bg-brand-50 dark:bg-brand-500/10 rounded-xl text-brand-600 dark:text-brand-400">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                        <polyline points="10 9 9 9 8 9"/>
                      </svg>
                    </div>
                    <span className="text-xs font-medium px-2.5 py-1 bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 rounded-full">
                      {doc.total_chunks || 0} chunks
                    </span>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-surface-800 dark:text-surface-200 truncate" title={doc.filename}>
                      {doc.filename}
                    </h3>
                    
                    {/* Quick Badges for available cached tasks */}
                    <div className="flex gap-2 mt-3">
                      {doc.tasks?.summary && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 rounded-md">
                          Summary
                        </span>
                      )}
                      {doc.tasks?.quiz && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400 rounded-md">
                          Quiz
                        </span>
                      )}
                      {doc.tasks?.flashcards && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400 rounded-md">
                          Flashcards
                        </span>
                      )}
                      {!doc.tasks && (
                        <span className="text-[10px] font-medium text-surface-400 dark:text-surface-500">
                          Click to analyze
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
