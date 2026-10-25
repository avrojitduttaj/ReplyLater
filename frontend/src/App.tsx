import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { KanbanBoard } from './components/KanbanBoard';
import { SeedBanner } from './components/SeedBanner';
import {
  CheckCircle2,
  AlertCircle,
  Database,
  Cpu,
  GitBranch,
  Activity,
  Heart,
  Moon,
} from 'lucide-react';

interface ThreadData {
  id: string;
  sender: string;
  subject: string;
  raw_body: string;
  received_at: string;
  status: string;
}

interface DraftData {
  id: string;
  thread_id: string;
  status: string;
  suggested_weekday: string;
  detected_deadline?: string;
  commitments_found: string[];
  missing_info_question?: string;
  user_clarification?: string;
  proposed_reply: string;
  created_at: string;
  thread?: ThreadData;
}

interface BoardData {
  needs_input: DraftData[];
  week_queue: {
    Monday: DraftData[];
    Tuesday: DraftData[];
    Wednesday: DraftData[];
    Thursday: DraftData[];
    Friday: DraftData[];
  };
  archived: ThreadData[];
}

export function App() {
  const [board, setBoard] = useState<BoardData>({
    needs_input: [],
    week_queue: {
      Monday: [],
      Tuesday: [],
      Wednesday: [],
      Thursday: [],
      Friday: [],
    },
    archived: [],
  });

  const [isLoadingSeed, setIsLoadingSeed] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  const fetchBoard = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch('/api/board');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data: BoardData = await res.json();
      setBoard(data);
    } catch (err) {
      console.error('Failed to fetch board:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchBoard();
  }, [fetchBoard]);

  const handleLoadSeed = async () => {
    setIsLoadingSeed(true);
    try {
      const res = await fetch('/api/trigger-seed-batch', { method: 'POST' });
      if (!res.ok) throw new Error(`Failed to load seed batch: ${res.statusText}`);
      const data = await res.json();
      await fetchBoard();
      showToast(
        data.message || 'Successfully ingested 5 scenarios through overnight pipeline!',
        'success'
      );
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Error triggering seed batch', 'error');
    } finally {
      setIsLoadingSeed(false);
    }
  };

  const handleResolveInput = async (draftId: string, clarification: string) => {
    try {
      const res = await fetch('/api/resolve-input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft_id: draftId, clarification }),
      });
      if (!res.ok) throw new Error('Failed to resolve input');
      await fetchBoard();
      showToast('Gemma finalized your draft and moved it to the Week-Ahead queue!', 'success');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to complete draft', 'error');
      throw err;
    }
  };

  const handleApproveDraft = async (draftId: string) => {
    try {
      const res = await fetch(`/api/approve-draft/${draftId}`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to approve draft');
      await fetchBoard();
      showToast('Draft approved and scheduled for automated delivery!', 'success');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to approve draft', 'error');
      throw err;
    }
  };

  const handleUpdateDraft = async (draftId: string, text: string) => {
    try {
      const res = await fetch(`/api/drafts/${draftId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proposed_reply: text }),
      });
      if (!res.ok) throw new Error('Failed to update draft');
      await fetchBoard();
      showToast('Draft text updated successfully', 'success');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to update draft', 'error');
    }
  };

  const totalThreads =
    board.needs_input.length +
    Object.values(board.week_queue).reduce((sum, list) => sum + list.length, 0) +
    board.archived.length;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation & Metrics Header */}
      <Header
        onLoadSeed={handleLoadSeed}
        onRefresh={fetchBoard}
        isLoadingSeed={isLoadingSeed}
        isRefreshing={isRefreshing}
      />

      {/* Main Board Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        {/* Toast Alert */}
        {toastMessage && (
          <div
            className={`mb-6 p-4 rounded-xl border flex items-center justify-between gap-3 shadow-xl animate-fade-in ${
              toastMessage.type === 'success'
                ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200'
                : 'bg-rose-950/80 border-rose-500/40 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-2.5">
              {toastMessage.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              )}
              <span className="text-xs font-medium">{toastMessage.text}</span>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-xs text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Hero Banner for Empty / Quick Exploration */}
        <SeedBanner
          onLoadSeed={handleLoadSeed}
          isLoading={isLoadingSeed}
          totalThreads={totalThreads}
        />

        {/* The 3-Bucket Review Board */}
        <KanbanBoard
          board={board}
          onResolveInput={handleResolveInput}
          onApproveDraft={handleApproveDraft}
          onUpdateDraft={handleUpdateDraft}
        />
      </main>

      {/* Footer & Partner Targets */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-8 px-4 lg:px-8 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="text-xl">🦥</span>
            <div>
              <p className="font-semibold text-slate-300">
                ReplyLater • Slow and Steady: Channel Your Inner Sloth
              </p>
              <p className="text-slate-400">
                Zero Cloud Egress Email Co-Pilot for Hacktoberfest DEV Challenge.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              <span>Gemma 2B</span>
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <GitBranch className="w-3.5 h-3.5 text-amber-400" />
              <span>Temporal Workflows</span>
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <Activity className="w-3.5 h-3.5 text-purple-400" />
              <span>Sentry Agent Tracing</span>
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>Tiger Data &amp; pgvector</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
