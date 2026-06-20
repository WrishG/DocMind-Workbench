import { useState, useRef } from 'react';
import { apiClient } from '../api/client';
import { useStore } from '../store/useStore';

export default function UploadZone() {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const { setDocuments, setActiveDocument } = useStore();

  const refreshDocuments = async () => {
    try {
      const response = await apiClient.get('/documents');
      setDocuments(response.data);
      if (response.data.length > 0) {
        setActiveDocument(response.data[0]);
      }
    } catch (error) {
      console.error("Failed to refresh documents", error);
    }
  };

  const processFile = async (file) => {
    if (!file || file.type !== "application/pdf") {
      alert("Please upload a PDF file!");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data.error) {
        throw new Error(res.data.error);
      }
      
      await refreshDocuments();
    } catch (error) {
      console.error("Upload failed:", error);
      alert(error.message || "Failed to upload document.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileChange = (event) => {
    processFile(event.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    processFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="p-3">
      <input
        type="file"
        accept=".pdf"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileChange}
      />

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current.click()}
        className={`
          relative overflow-hidden cursor-pointer rounded-xl p-4 text-center transition-all duration-200
          border-2 border-dashed
          ${isDragOver
            ? 'border-brand-400 bg-brand-50 dark:bg-brand-950/30 scale-[1.02]'
            : 'border-surface-200 dark:border-surface-700 hover:border-brand-300 dark:hover:border-brand-600'
          }
          ${isUploading ? 'pointer-events-none opacity-70' : ''}
        `}
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <svg className="animate-spin h-4 w-4 text-brand-500" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25"/>
              <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" className="opacity-75"/>
            </svg>
            <span className="text-sm font-medium text-surface-600 dark:text-surface-300">Processing…</span>
          </div>
        ) : (
          <>
            <div className="mb-1">
              <svg className="mx-auto h-6 w-6 text-surface-400 dark:text-surface-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"/>
              </svg>
            </div>
            <p className="text-sm font-medium text-surface-600 dark:text-surface-300">
              Upload PDF
            </p>
            <p className="text-xs text-surface-400 dark:text-surface-500 mt-0.5">
              Click or drag & drop
            </p>
          </>
        )}
      </div>
    </div>
  );
}
