import { FileDown, Loader2 } from 'lucide-react';
import { useState } from 'react';

export default function ExportButton({ analysisId }) {
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    if (!analysisId) return;
    setLoading(true);
    
    const baseUrl = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}/export/pdf/${analysisId}`, {
        method: 'GET',
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      // Handle the blob response for download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PropagandaLens_Report_${analysisId.substring(0,8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      console.error(err);
      alert('Failed to export PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={handleExport}
      disabled={loading || !analysisId}
      className="w-full mt-4 glass-panel hover:bg-white/10 text-white py-4 px-4 rounded-xl font-bold tracking-wide flex justify-center items-center gap-2 transition-all shadow-lg active:scale-95 border border-white/20"
    >
      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileDown className="w-5 h-5" />}
      Download PDF Report
    </button>
  );
}
