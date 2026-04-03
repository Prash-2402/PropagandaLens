import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, X, Send, Bot, User, Loader2 } from 'lucide-react';

export default function ChatBot({ analysisContext }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Suggested Prompts
  const suggestedPrompts = [
    "Why is this propaganda?",
    "Which sentence is most manipulating?",
    "Rewrite this neutrally."
  ];

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || !analysisContext?.analysis_id) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Build history (excluding system prompt which is handled by backend)
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      
      const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/chat`, {
        message: text,
        analysis_id: analysisContext.analysis_id,
        history: history
      });

      const aiMsg = { role: 'assistant', content: res.data.response };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error or analysis missing.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="bg-primary hover:bg-indigo-600 text-white p-4 rounded-full shadow-[0_0_20px_rgba(99,102,241,0.5)] transition-transform hover:scale-110 flexitems-center justify-center animate-bounce"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      {isOpen && (
        <div className="w-[400px] h-[600px] glass-panel rounded-3xl shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden animate-in slide-in-from-bottom-8">
          <div className="bg-white/10 backdrop-blur-md p-5 border-b border-white/10 flex justify-between items-center shadow-lg">
            <div className="flex items-center gap-3">
              <Bot className="w-6 h-6 text-primary" />
              <h3 className="font-bold text-white">PropagandaLens AI</h3>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white transition">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-grow overflow-y-auto p-4 flex flex-col gap-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 my-auto text-sm">
                <Bot className="w-10 h-10 mx-auto mb-3 opacity-20" />
                Ask me about the analysis! I can explain the techniques or rewrite the text.
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
                <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-blue-900/50 text-blue-400' : 'bg-primary/20 text-primary'}`}>
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className={`p-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-gray-800 text-gray-200 border border-gray-700 rounded-tl-sm'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3 max-w-[85%]">
                <div className="shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-4 rounded-2xl bg-gray-800 text-gray-400 border border-gray-700 rounded-tl-sm flex gap-1">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-75"></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-150"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-black/30 border-t border-white/10 backdrop-blur-md">
            {messages.length < 2 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {suggestedPrompts.map(prompt => (
                  <button 
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-full border border-gray-700 transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask a question..."
                className="flex-grow glass-input rounded-xl px-4 py-3"
              />
              <button 
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="bg-primary hover:bg-indigo-600 disabled:opacity-50 disabled:hover:bg-primary text-white p-3 rounded-lg transition"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
