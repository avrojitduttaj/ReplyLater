import React from 'react';
import { Cpu, ShieldCheck, GitBranch, Activity, RefreshCw, Sparkles } from 'lucide-react';

interface HeaderProps {
  onLoadSeed: () => void;
  onRefresh: () => void;
  isLoadingSeed: boolean;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onLoadSeed,
  onRefresh,
  isLoadingSeed,
  isRefreshing,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Theme */}
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-amber-500/20 via-emerald-500/20 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center text-2xl shadow-inner">
            🦥
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-xl text-white tracking-tight">ReplyLater</h1>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                Local-First
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Slow &amp; Steady: Channel Your Inner Sloth • Overnight Email Co-Pilot
            </p>
          </div>
        </div>

        {/* 4 Partner / Architecture Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {/* Badge 1: Gemma */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 shadow-sm"
            title="Local Gemma 2B running via Ollama with 0 cloud egress"
          >
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-medium text-slate-200">Gemma 2B</span>
            <span className="text-[10px] text-slate-400 font-mono">Ollama</span>
          </div>

          {/* Badge 2: Privacy / 0 KB Egress */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-xs text-emerald-300 shadow-sm"
            title="Zero external cloud egress for email bodies"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-medium">Cloud Egress:</span>
            <span className="font-semibold text-emerald-200 font-mono">0 KB</span>
          </div>

          {/* Badge 3: Temporal */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 shadow-sm"
            title="Temporal Durable Orchestration Engine managing overnight sequential triage"
          >
            <GitBranch className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-medium text-slate-200">Temporal</span>
            <span className="text-[10px] text-slate-400 font-mono">Durable</span>
          </div>

          {/* Badge 4: Sentry */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 shadow-sm"
            title="Sentry AI Agent Telemetry tracking prompt tokens and latency"
          >
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-medium text-slate-200">Sentry</span>
            <span className="text-[10px] text-slate-400 font-mono">Agent Traces</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center justify-center disabled:opacity-50"
            title="Refresh board"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          <button
            onClick={onLoadSeed}
            disabled={isLoadingSeed}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-xs shadow-md hover:shadow-emerald-500/20 transition disabled:opacity-60"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isLoadingSeed ? 'animate-spin' : ''}`} />
            {isLoadingSeed ? 'Triaging 5 Emails...' : 'Load Demo Backlog (5 Emails)'}
          </button>
        </div>
      </div>
    </header>
  );
};
