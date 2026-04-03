import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function ScoreCard({ score, credibility }) {
  let colorClass = "text-green-500";
  let bgClass = "bg-green-500/10";
  let Icon = ShieldCheck;

  if (credibility === "Biased") {
    colorClass = "text-orange-500";
    bgClass = "bg-orange-500/10";
    Icon = ShieldAlert;
  } else if (credibility === "Highly Manipulative") {
    colorClass = "text-red-500";
    bgClass = "bg-red-500/10";
    Icon = Shield;
  }

  // Calculate SVG circle dasharray and offset
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="glass-panel p-8 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-50"></div>
      
      <h3 className="text-sm font-semibold text-gray-400 mb-6 uppercase tracking-wider">Manipulation Score</h3>
      
      <div className="relative flex items-center justify-center w-32 h-32 mb-4">
        {/* Background Circle */}
        <svg className="absolute w-full h-full transform -rotate-90">
          <circle 
            cx="64" cy="64" r={radius} 
            stroke="currentColor" strokeWidth="8" fill="transparent" 
            className="text-gray-800"
          />
          {/* Progress Circle */}
          <circle 
            cx="64" cy="64" r={radius} 
            stroke="currentColor" strokeWidth="8" fill="transparent" 
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={`transition-all duration-1000 ease-out ${colorClass}`}
          />
        </svg>
        <div className="flex flex-col items-center">
          <span className="text-4xl font-bold text-white tracking-tighter">{score}</span>
        </div>
      </div>

      <div className={`flex items-center gap-3 px-6 py-3 rounded-full shadow-lg border border-white/10 ${bgClass}`}>
        <Icon className={`w-6 h-6 ${colorClass} drop-shadow-[0_0_10px_currentColor]`} />
        <span className={`font-bold text-lg tracking-wide ${colorClass} drop-shadow-[0_0_5px_currentColor]`}>{credibility}</span>
      </div>
    </div>
  );
}
