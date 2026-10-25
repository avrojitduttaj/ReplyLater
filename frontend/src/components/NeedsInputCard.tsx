import React, { useState } from 'react';
import { AlertCircle, ArrowRight, User, HelpCircle, Sparkles } from 'lucide-react';

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
  thread?: {
    id: string;
    sender: string;
    subject: string;
    raw_body: string;
    received_at: string;
    status: string;
  };
}

interface NeedsInputCardProps {
  draft: DraftData;
  onResolve: (draftId: string, clarification: string) => Promise<void>;
}

export const NeedsInputCard: React.FC<NeedsInputCardProps> = ({ draft, onResolve }) => {
  const [clarification, setClarification] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBody, setShowBody] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarification.trim()) return;
    setIsSubmitting(true);
    try {
      await onResolve(draft.id, clarification.trim());
      setClarification('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const sender = draft.thread?.sender || 'Unknown Sender';
  const subject = draft.thread?.subject || '(No Subject)';
  const body = draft.thread?.raw_body || '';

  return (
    <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-4 shadow-lg hover:border-amber-500/50 transition-all group">
      {/* Top Tag & Sender */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px] font-semibold uppercase tracking-wider">
          <AlertCircle className="w-3 h-3 text-amber-400" />
          Anti-Hallucination Guardrail
        </span>
        <span className="text-[11px] text-slate-500 font-medium">
          Suggested: {draft.suggested_weekday}
        </span>
      </div>

      {/* Subject & Sender info */}
      <div className="space-y-1 mb-3">
        <h4 className="font-semibold text-sm text-slate-100 line-clamp-1">{subject}</h4>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <User className="w-3.5 h-3.5 text-slate-500" />
          <span className="truncate">{sender}</span>
        </div>
      </div>

      {/* AI Question Prompt */}
      <div className="bg-amber-950/20 border border-amber-500/20 rounded-lg p-3 mb-3">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-amber-300 uppercase tracking-wider mb-0.5">
              Decision Needed:
            </p>
            <p className="text-xs text-amber-100 leading-snug">
              {draft.missing_info_question || 'Gemma requires your input before composing this draft.'}
            </p>
          </div>
        </div>
      </div>

      {/* Accordion to view original incoming email snippet */}
      <div className="mb-3">
        <button
          type="button"
          onClick={() => setShowBody(!showBody)}
          className="text-[11px] text-slate-400 hover:text-slate-300 underline underline-offset-2 decoration-slate-700"
        >
          {showBody ? 'Hide incoming message preview' : 'View incoming message preview'}
        </button>
        {showBody && (
          <div className="mt-2 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap max-h-36 overflow-y-auto font-mono">
            {body}
          </div>
        )}
      </div>

      {/* Inline Clarification Input & Complete Draft Button */}
      <form onSubmit={handleSubmit} className="space-y-2.5">
        <div>
          <label className="block text-[11px] font-medium text-slate-300 mb-1">
            Your decision / rate / schedule:
          </label>
          <input
            type="text"
            value={clarification}
            onChange={(e) => setClarification(e.target.value)}
            placeholder="e.g., Rate is $125/hr and available starting next Monday"
            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 focus:border-amber-400 focus:ring-1 focus:ring-amber-400 text-xs text-white placeholder-slate-500 outline-none transition"
            disabled={isSubmitting}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !clarification.trim()}
          className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <Sparkles className="w-3.5 h-3.5 animate-spin" />
              <span>Gemma generating draft...</span>
            </>
          ) : (
            <>
              <span>Complete Draft with Gemma</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
};
