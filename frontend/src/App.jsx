import { useState } from 'react';
import TextInput from './components/TextInput';
import HighlightedText from './components/HighlightedText';
import ScoreCard from './components/ScoreCard';
import TechniqueChart from './components/TechniqueChart';
import Timeline from './components/Timeline';
import ChatBot from './components/ChatBot';
import ExportButton from './components/ExportButton';
import { ShieldAlert, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  return (
    <>
      {/* Animated Mesh Background */}
      <div className="mesh-bg">
        <div className="mesh-blob mesh-blob-1 rounded-full"></div>
        <div className="mesh-blob mesh-blob-2 rounded-full"></div>
        <div className="mesh-blob mesh-blob-3 rounded-full"></div>
      </div>

      <div className="min-h-screen flex flex-col items-center p-4 lg:p-8 relative z-10">
        <motion.header 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="w-full max-w-6xl flex justify-between items-center mb-10 glass-panel px-8 py-4 rounded-2xl"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl backdrop-blur-md border border-white/20 shadow-[0_0_15px_rgba(99,102,241,0.5)]">
              <ShieldAlert className="w-8 h-8 text-indigo-400" />
            </div>
            <h1 className="text-3xl font-extrabold bg-gradient-to-r from-indigo-300 via-purple-300 to-indigo-400 bg-clip-text text-transparent tracking-tight">
              PropagandaLens
            </h1>
          </div>
          <div className="flex gap-2 p-1.5 bg-black/20 rounded-xl backdrop-blur-md border border-white/5">
            <button
              onClick={() => setActiveTab('analyze')}
              className={`px-5 py-2.5 rounded-lg font-semibold transition-all ${
                activeTab === 'analyze' ? 'bg-indigo-500/80 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              Analyze
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-5 py-2.5 rounded-lg font-semibold transition-all ${
                activeTab === 'timeline' ? 'bg-indigo-500/80 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              Timeline
            </button>
          </div>
        </motion.header>

        <main className="w-full max-w-6xl flex-grow gap-8 grid grid-cols-1 lg:grid-cols-12 relative">
          <AnimatePresence mode="wait">
            {activeTab === 'analyze' && (
              <motion.div 
                key="analyze"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.4 }}
                className="lg:col-span-12 grid grid-cols-1 lg:grid-cols-12 gap-8"
              >
                <div className="lg:col-span-8 flex flex-col gap-8">
                  <TextInput onAnalyzeStart={() => setIsAnalyzing(true)} onAnalyzeComplete={(res) => { setIsAnalyzing(false); setAnalysisResult(res); }} />
                  
                  <AnimatePresence>
                    {(analysisResult || isAnalyzing) && (
                      <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass-panel p-8 rounded-2xl min-h-[350px] relative overflow-hidden"
                      >
                        {isAnalyzing ? (
                          <div className="flex flex-col items-center justify-center h-full text-indigo-200">
                            <Activity className="w-12 h-12 animate-bounce text-indigo-400 mb-6" />
                            <p className="animate-pulse text-lg font-medium tracking-wide">Processing through PropagandaLens Core...</p>
                          </div>
                        ) : (
                          <HighlightedText spans={analysisResult.spans} originalText={analysisResult.original_text} />
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <div className="lg:col-span-4 flex flex-col gap-6">
                  {analysisResult ? (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ staggerChildren: 0.1 }}
                      className="flex flex-col gap-6"
                    >
                      <ScoreCard score={analysisResult.overall_score} credibility={analysisResult.credibility} />
                      <TechniqueChart breakdown={analysisResult.technique_breakdown} />
                      <ExportButton analysisId={analysisResult.analysis_id} />
                    </motion.div>
                  ) : (
                    <div className="glass-panel p-8 rounded-2xl h-[400px] flex flex-col items-center justify-center text-center px-8 text-gray-400 border-dashed border-2 border-white/20">
                      <ShieldAlert className="w-16 h-16 mb-6 opacity-30" />
                      <p className="text-lg">Run an analysis to decrypt manipulation patterns and score credibility.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'timeline' && (
              <motion.div 
                key="timeline"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.4 }}
                className="lg:col-span-12"
              >
                <Timeline />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <AnimatePresence>
          {analysisResult && (
            <motion.div 
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className="fixed bottom-8 right-8 z-50"
            >
              <ChatBot analysisContext={analysisResult} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}

export default App;
