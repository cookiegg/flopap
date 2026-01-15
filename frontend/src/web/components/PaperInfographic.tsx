import React from 'react';
import { Paper } from '../../types';
import { ArrowDown, Shield, Radio, Lock, Activity, Wifi, Eye, EyeOff, Signal, ShieldCheck, Dices } from 'lucide-react';

interface PaperInfographicProps {
  paper: Paper;
  isDark: boolean;
}

const PaperInfographic: React.FC<PaperInfographicProps> = ({ paper, isDark }) => {
  const bgClass = isDark ? 'bg-slate-900' : 'bg-slate-50';
  const textClass = isDark ? 'text-slate-100' : 'text-slate-900';
  const borderClass = isDark ? 'border-slate-700' : 'border-slate-300';

  return (
    <div className={`${bgClass} ${textClass} p-6 rounded-xl overflow-y-auto max-h-[600px]`}>
      {/* Header */}
      <div className="text-center mb-8">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${isDark ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-emerald-500 bg-emerald-50 text-emerald-700'} text-xs font-bold uppercase tracking-widest mb-4`}>
          <Shield size={14} /> Paper Infographic
        </div>
        <h2 className="text-2xl font-bold mb-2">{paper.title}</h2>
        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          {paper.authors.slice(0, 3).join(', ')}
          {paper.authors.length > 3 && ' et al.'}
        </p>
      </div>

      {/* Problem Section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg ${isDark ? 'bg-red-500/10 border border-red-500/20' : 'bg-red-50 border border-red-300'}`}>
            <Radio className={`w-5 h-5 ${isDark ? 'text-red-400' : 'text-red-600'}`} />
          </div>
          <h3 className="text-lg font-bold">The Challenge</h3>
        </div>
        
        <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-800/50 border border-red-500/20' : 'bg-white border border-red-200'}`}>
          <div className="h-24 relative flex flex-col justify-center gap-3">
            <div className={`w-full h-10 ${isDark ? 'bg-slate-900/50' : 'bg-slate-100'} rounded-lg overflow-hidden flex items-center px-2`}>
              {Array.from({ length: 15 }).map((_, i) => (
                <div key={i} className={`flex-1 h-6 ${isDark ? 'bg-red-500/40' : 'bg-red-300'} mx-[1px] rounded-sm`} />
              ))}
            </div>
            <div className={`flex justify-center items-center gap-2 text-sm ${isDark ? 'text-red-300' : 'text-red-700'}`}>
              <Eye size={16} />
              <span>Traditional approach: Continuous communication</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connector */}
      <div className="flex justify-center my-4">
        <ArrowDown className={`${isDark ? 'text-slate-600' : 'text-slate-400'}`} />
      </div>

      {/* Solution Section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg ${isDark ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-emerald-50 border border-emerald-300'}`}>
            <Lock className={`w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
          </div>
          <h3 className="text-lg font-bold">The Solution</h3>
        </div>

        <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-800/50 border border-emerald-500/20' : 'bg-white border border-emerald-200'}`}>
          <div className="h-24 relative flex flex-col justify-center gap-3">
            <div className={`w-full h-10 ${isDark ? 'bg-slate-900/50' : 'bg-slate-100'} rounded-lg overflow-hidden flex items-center px-2`}>
              {Array.from({ length: 15 }).map((_, i) => {
                const isActive = [2, 6, 11, 14].includes(i);
                return (
                  <div key={i} className={`flex-1 h-6 mx-[1px] rounded-sm ${isActive ? (isDark ? 'bg-emerald-500' : 'bg-emerald-400') : 'bg-transparent'}`} />
                );
              })}
            </div>
            <div className={`flex justify-center items-center gap-2 text-sm ${isDark ? 'text-emerald-300' : 'text-emerald-700'}`}>
              <EyeOff size={16} />
              <span>Sparse & randomized communication</span>
            </div>
          </div>
        </div>
      </div>

      {/* Mechanism */}
      <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-800/30 border border-slate-700' : 'bg-white border border-slate-200'} mb-6`}>
        <h4 className={`text-center text-xs uppercase tracking-widest font-semibold mb-6 ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
          Core Mechanism
        </h4>
        
        <div className="flex justify-around items-center">
          <div className="flex flex-col items-center text-center">
            <div className={`w-16 h-16 rounded-full border-2 flex flex-col items-center justify-center mb-2 ${isDark ? 'bg-indigo-900/30 border-indigo-500/50' : 'bg-indigo-50 border-indigo-300'}`}>
              <Signal className={`w-6 h-6 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
              <span className={`text-[10px] ${isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>Rate ↓</span>
            </div>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Lower frequency</p>
          </div>

          <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700 border border-slate-600' : 'bg-slate-100 border border-slate-300'}`}>
            <Dices className={`w-5 h-5 ${isDark ? 'text-white' : 'text-slate-700'}`} />
          </div>

          <div className="flex flex-col items-center text-center">
            <div className={`w-16 h-16 rounded-full border-2 flex flex-col items-center justify-center mb-2 ${isDark ? 'bg-emerald-900/30 border-emerald-500/50' : 'bg-emerald-50 border-emerald-300'}`}>
              <ShieldCheck className={`w-6 h-6 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
              <span className={`text-[10px] ${isDark ? 'text-emerald-300' : 'text-emerald-700'}`}>Privacy ↑</span>
            </div>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Better protection</p>
          </div>
        </div>
      </div>

      {/* Key Insight */}
      <div className={`p-4 rounded-lg text-center ${isDark ? 'bg-emerald-900/20 border border-emerald-500/30' : 'bg-emerald-50 border border-emerald-300'}`}>
        <p className={`text-sm font-medium ${isDark ? 'text-emerald-200' : 'text-emerald-800'}`}>
          Key Insight: Less communication can provide stronger privacy guarantees
        </p>
      </div>

      {/* Abstract Preview */}
      <div className="mt-6">
        <h4 className={`text-sm font-bold mb-2 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Abstract</h4>
        <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          {paper.abstract.slice(0, 300)}...
        </p>
      </div>
    </div>
  );
};

export default PaperInfographic;
