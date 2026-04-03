import { useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2, Plus, Play } from 'lucide-react';

export default function Timeline() {
  const [documents, setDocuments] = useState([
    { date: '2024-01-01', text: '' },
    { date: '2024-02-01', text: '' },
  ]);
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpdateDoc = (index, field, value) => {
    const newDocs = [...documents];
    newDocs[index][field] = value;
    setDocuments(newDocs);
  };

  const handleAddDoc = () => {
    setDocuments([...documents, { date: `2024-0${Math.min(documents.length + 1, 9)}-01`, text: '' }]);
  };

  const handleAnalyze = async () => {
    const validDocs = documents.filter(d => d.text.trim().length > 10);
    if (validDocs.length < 2) return alert('Need at least 2 valid documents for timeline.');

    setLoading(true);
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/timeline`, { documents: validDocs });
      setTimelineData(res.data);
    } catch (err) {
      console.error(err);
      alert('Timeline analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900 border border-gray-700 p-4 rounded-lg shadow-xl text-sm">
          <p className="font-bold text-white mb-2">{label}</p>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-3 h-3 rounded-full bg-primary"></span>
            <span className="text-gray-300">Score: <span className="font-bold text-white">{payload[0].value}</span></span>
          </div>
          {payload[0].payload.dominant_technique && (
            <p className="text-gray-400 mt-2 text-xs">Dominant: {payload[0].payload.dominant_technique}</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="glass-panel p-8 rounded-2xl">
        <h2 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400 mb-4 tracking-tight">Temporal Analysis (Longitudinal)</h2>
        <p className="text-gray-400 text-sm mb-6 max-w-2xl">
          Track the evolution of propaganda techniques over time across multiple documents, speeches, or posts.
        </p>

        <div className="flex flex-col gap-4 mb-6">
          {documents.map((doc, idx) => (
            <div key={idx} className="flex gap-4 items-start">
              <input
                type="date"
                value={doc.date}
                onChange={(e) => handleUpdateDoc(idx, 'date', e.target.value)}
                className="glass-input rounded-xl p-3 w-40"
              />
              <textarea
                value={doc.text}
                onChange={(e) => handleUpdateDoc(idx, 'text', e.target.value)}
                placeholder="Document text..."
                className="flex-grow glass-input rounded-xl p-3 h-12 min-h-[48px] max-h-32 resize-y"
              />
            </div>
          ))}
        </div>

        <div className="flex gap-4">
          <button onClick={handleAddDoc} className="px-4 py-2 border border-gray-700 text-gray-300 rounded-lg flex items-center gap-2 hover:bg-gray-800 transition">
            <Plus className="w-4 h-4" /> Add Document
          </button>
          <button onClick={handleAnalyze} disabled={loading} className="bg-primary hover:bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 transition">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Analyze Timeline
          </button>
        </div>
      </div>

      {timelineData && (
        <div className="glass-panel p-8 rounded-2xl h-96 flex flex-col">
          <h3 className="text-lg font-bold text-white mb-6">Manipulation Score Over Time</h3>
          <div className="flex-grow">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData.data_points} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                <YAxis domain={[0, 100]} stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="overall_score"
                  stroke="#6366F1"
                  strokeWidth={3}
                  activeDot={{ r: 6, fill: '#6366F1', stroke: '#1E293B', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
