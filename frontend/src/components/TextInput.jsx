import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Play, Loader2 } from 'lucide-react';

export default function TextInput({ onAnalyzeStart, onAnalyzeComplete }) {
  const [text, setText] = useState('');
  const [fileLoading, setFileLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleAnalyze = async () => {
    if (!text.trim() || text.length < 10) return alert('Please enter at least 10 characters.');
    
    onAnalyzeStart();
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/analyze`, { text });
      onAnalyzeComplete(res.data);
    } catch (err) {
      console.error(err);
      alert('Analysis failed. Please check the backend connection and try again.');
      onAnalyzeComplete(null);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setText(res.data.text);
    } catch (err) {
      console.error(err);
      alert('File upload failed.');
    } finally {
      setFileLoading(false);
    }
  };

  return (
    <div className="glass-panel p-8 rounded-2xl flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-white">Input Text</h2>
        <input 
          type="file" 
          accept=".txt,.pdf"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden" 
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={fileLoading}
          className="text-sm flex items-center gap-2 text-gray-400 hover:text-white transition"
        >
          {fileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          Upload .txt / .pdf
        </button>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste a speech, article, or social media post here (English or Hindi)..."
        className="w-full h-40 glass-input rounded-xl p-5 text-lg resize-y"
      />

      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500">{text.length} characters</span>
        <button 
          onClick={handleAnalyze}
          className="bg-primary hover:bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-primary/20 transition-all active:scale-95"
        >
          <Play className="w-4 h-4" /> Analyze
        </button>
      </div>
    </div>
  );
}
