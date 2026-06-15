import { useState, useRef } from 'react';
import { apiClient } from '../api/client';
import { useStore } from '../store/useStore';

export default function UploadZone() {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const { setDocuments, setActiveDocument } = useStore();

  const refreshDocuments = async () => {
    try {
      const response = await apiClient.get('/documents');
      setDocuments(response.data);
      // Auto-select the newest document
      if (response.data.length > 0) {
        setActiveDocument(response.data[0]);
      }
    } catch (error) {
      console.error("Failed to refresh documents", error);
    }
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file!");
      return;
    }

    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await refreshDocuments();
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload document.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="p-4 border-t border-gray-100 bg-gray-50">
      <input
        type="file"
        accept=".pdf"
        className="hidden"
        ref={fileInputRef}
        onChange={handleFileChange}
      />
      
      <button 
        onClick={() => fileInputRef.current.click()}
        disabled={isUploading}
        className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
          isUploading 
            ? "bg-gray-300 cursor-not-allowed text-gray-700" 
            : "bg-blue-600 hover:bg-blue-700 hover:shadow-md text-white"
        }`}
      >
        {isUploading ? "⏳ Uploading & Indexing..." : "+ Upload PDF"}
      </button>
    </div>
  );
}
