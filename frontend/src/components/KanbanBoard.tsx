import React, { useState } from 'react';
import { NeedsInputCard } from './NeedsInputCard';
import { DraftCard } from './DraftCard';
import {
  AlertTriangle,
  CalendarDays,
  Archive,
  CheckCircle,
  Inbox,
  Clock,
  Sparkles,
  Mail,
  ChevronDown,
  ChevronUp,
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

interface KanbanBoardProps {
  board: BoardData;
  onResolveInput: (draftId: string, clarification: string) => Promise<void>;
  onApproveDraft: (draftId: string) => Promise<void>;
  onUpdateDraft?: (draftId: string, text: string) => Promise<void>;
}

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  board,
  onResolveInput,
  onApproveDraft,
  onUpdateDraft,
}) => {
  const [selectedDay, setSelectedDay] = useState<string>('All');
  const [expandedArchivedId, setExpandedArchivedId] = useState<string | null>(null);

  // Flatten week queue items based on day filter
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const allWeekDrafts: DraftData[] = [];
  days.forEach((day) => {
    const list = board.week_queue[day as keyof typeof board.week_queue] || [];
    if (selectedDay === 'All' || selectedDay === day) {
      allWeekDrafts.push(...list);
    }
  });

  const totalWeekCount = days.reduce(
    (acc, day) => acc + (board.week_queue[day as keyof typeof board.week_queue]?.length || 0),
    0
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      {/* ======================================================== */}
      {/* COLUMN 1: Needs Your Call (Amber)                        */}
      {/* ======================================================== */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col min-h-[500px]">
        {/* Column Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-100">Needs Your Call</h3>
              <p className="text-[11px] text-slate-400">Gemma refused to hallucinate</p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold font-mono">
            {board.needs_input.length}
          </span>
        </div>

        {/* Content */}
        <div className="space-y-4 flex-1">
          {board.needs_input.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-6 border border-dashed border-slate-800 rounded-xl text-slate-500">
              <div className="w-12 h-12 rounded-full bg-slate-800/60 flex items-center justify-center mb-3">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
              <p className="text-sm font-medium text-slate-300">All Decisions Clear</p>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                Zero emails currently waiting for rate or availability confirmation.
              </p>
            </div>
          ) : (
            board.needs_input.map((draft) => (
              <NeedsInputCard
                key={draft.id}
                draft={draft}
                onResolve={onResolveInput}
              />
            ))
          )}
        </div>
      </div>

      {/* ======================================================== */}
      {/* COLUMN 2: Week-Ahead Queue (Emerald)                     */}
      {/* ======================================================== */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col min-h-[500px]">
        {/* Column Header */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CalendarDays className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-100">Week-Ahead Queue</h3>
              <p className="text-[11px] text-slate-400">Scheduled &amp; approved drafts</p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold font-mono">
            {totalWeekCount}
          </span>
        </div>

        {/* Day Selector Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-2 mb-3 scrollbar-none text-[11px]">
          <button
            onClick={() => setSelectedDay('All')}
            className={`px-2.5 py-1 rounded-md transition font-medium whitespace-nowrap ${
              selectedDay === 'All'
                ? 'bg-emerald-500 text-slate-950 font-bold'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({totalWeekCount})
          </button>
          {days.map((day) => {
            const count = board.week_queue[day as keyof typeof board.week_queue]?.length || 0;
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-2.5 py-1 rounded-md transition font-medium whitespace-nowrap ${
                  selectedDay === day
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
                }`}
              >
                {day.slice(0, 3)} {count > 0 && `(${count})`}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="space-y-4 flex-1">
          {allWeekDrafts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-6 border border-dashed border-slate-800 rounded-xl text-slate-500">
              <div className="w-12 h-12 rounded-full bg-slate-800/60 flex items-center justify-center mb-3">
                <Clock className="w-6 h-6 text-slate-400" />
              </div>
              <p className="text-sm font-medium text-slate-300">Queue is Clear</p>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                {selectedDay === 'All'
                  ? 'No drafts queued. Click "Load Demo Backlog" to see overnight triage.'
                  : `No drafts currently scheduled for ${selectedDay}.`}
              </p>
            </div>
          ) : (
            allWeekDrafts.map((draft) => (
              <DraftCard
                key={draft.id}
                draft={draft}
                onApprove={onApproveDraft}
                onUpdateDraft={onUpdateDraft}
              />
            ))
          )}
        </div>
      </div>

      {/* ======================================================== */}
      {/* COLUMN 3: Info / Closed (Slate)                          */}
      {/* ======================================================== */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col min-h-[500px]">
        {/* Column Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-800 text-slate-400">
              <Archive className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-100">Info / Closed</h3>
              <p className="text-[11px] text-slate-400">Newsletters, receipts, FYIs</p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-bold font-mono">
            {board.archived.length}
          </span>
        </div>

        {/* Content */}
        <div className="space-y-3 flex-1">
          {board.archived.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-6 border border-dashed border-slate-800 rounded-xl text-slate-500">
              <div className="w-12 h-12 rounded-full bg-slate-800/60 flex items-center justify-center mb-3">
                <Inbox className="w-6 h-6 text-slate-400" />
              </div>
              <p className="text-sm font-medium text-slate-300">No Archived Items</p>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                Automated receipts, invoices, and newsletters auto-route here.
              </p>
            </div>
          ) : (
            board.archived.map((thread) => {
              const isExpanded = expandedArchivedId === thread.id;
              return (
                <div
                  key={thread.id}
                  className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3.5 shadow-sm hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 text-[10px] font-semibold uppercase tracking-wider">
                      <Sparkles className="w-3 h-3 text-slate-400" />
                      Zero-Effort Auto-Archived
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {thread.received_at ? new Date(thread.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                    </span>
                  </div>

                  <h4 className="font-medium text-xs text-slate-200 line-clamp-1 mb-1">
                    {thread.subject}
                  </h4>
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-2">
                    <Mail className="w-3 h-3 text-slate-500 shrink-0" />
                    <span className="truncate">{thread.sender}</span>
                  </div>

                  <button
                    onClick={() => setExpandedArchivedId(isExpanded ? null : thread.id)}
                    className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-300 transition"
                  >
                    <span>{isExpanded ? 'Hide content' : 'Preview content'}</span>
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>

                  {isExpanded && (
                    <div className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 whitespace-pre-wrap max-h-36 overflow-y-auto font-mono">
                      {thread.raw_body}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
