import React from 'react';
import { Moon, Sparkles, SlidersHorizontal, Lock } from 'lucide-react';

interface SeedBannerProps {
  onLoadSeed: () => void;
  isLoading: boolean;
  totalThreads: number;
}

export const SeedBanner: React.FC<SeedBannerProps> = ({ onLoadSeed, isLoading, totalThreads }) => {
  if (totalThreads > 0) return null;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 p-6 md:p-8 mb-8 shadow-xl">
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            <Moon className="w-3.5 h-3.5" />
            <span>Hacktoberfest DEV Challenge • The Slow &amp; Steady Ethos</span>
          </div>
          <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
            Go to sleep with an inbox full of obligations. Wake up with next week’s replies ready.
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            ReplyLater is a private, local-first email orchestrator. Powered by local <strong className="text-white">Gemma 2B</strong>, <strong className="text-white">Temporal</strong> durable workflows, and <strong className="text-white">pgvector</strong> memory, it triages overnight with <strong>zero cloud egress</strong>. When an email asks for private rates or availability, Gemma refuses to hallucinate and asks for your call.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>0 KB cloud egress (Ollama local)</span>
            </div>
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Anti-hallucination guardrails</span>
            </div>
            <div className="flex items-center gap-2">
              <Moon className="w-4 h-4 text-purple-400 shrink-0" />
              <span>Overnight rate-limited triage</span>
            </div>
          </div>
        </div>

        <button
          onClick={onLoadSeed}
          disabled={isLoading}
          className="shrink-0 flex items-center gap-2.5 px-5 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-950/50 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60"
        >
          <Sparkles className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Triaging Demo Emails...' : 'Load Demo Backlog (5 Scenarios)'}
        </button>
      </div>
    </div>
  );
};
