import React, { useState } from 'react';
import { Calendar, Check, Clock, User, CheckCircle2, Edit3, Send } from 'lucide-react';

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

interface DraftCardProps {
  draft: DraftData;
  onApprove: (draftId: string) => Promise<void>;
  onUpdateDraft?: (draftId: string, replyText: string) => Promise<void>;
}

export const DraftCard: React.FC<DraftCardProps> = ({ draft, onApprove, onUpdateDraft }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [replyText, setReplyText] = useState(draft.proposed_reply);
  const [isApproving, setIsApproving] = useState(false);
  const isApproved = draft.status === 'APPROVED';

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      if (isEditing && onUpdateDraft) {
        await onUpdateDraft(draft.id, replyText);
        setIsEditing(false);
      }
      await onApprove(draft.id);
    } finally {
      setIsApproving(false);
    }
  };

  const handleSaveText = async () => {
    if (onUpdateDraft) {
      await onUpdateDraft(draft.id, replyText);
    }
    setIsEditing(false);
  };

  const sender = draft.thread?.sender || 'Unknown Sender';
  const subject = draft.thread?.subject || '(No Subject)';

  return (
    <div
      className={`bg-slate-900/90 border rounded-xl p-4 shadow-lg transition-all ${
        isApproved
          ? 'border-emerald-500/60 bg-emerald-950/10'
          : 'border-slate-800 hover:border-emerald-500/30'
      }`}
    >
      {/* Header: Weekday & Deadline */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-semibold">
            <Calendar className="w-3 h-3 text-emerald-400" />
            {draft.suggested_weekday}
          </span>

          {draft.detected_deadline && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300 text-[11px]">
              <Clock className="w-3 h-3 text-blue-400" />
              {draft.detected_deadline}
            </span>
          )}
        </div>

        {isApproved ? (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[11px] font-bold">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Approved &amp; Scheduled
          </span>
        ) : (
          <span className="text-[11px] text-slate-400 font-medium">Pending Review</span>
        )}
      </div>

      {/* Subject & Sender */}
      <div className="space-y-0.5 mb-3">
        <h4 className="font-semibold text-sm text-slate-100 line-clamp-1">{subject}</h4>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <User className="w-3 h-3 text-slate-500" />
          <span className="truncate">{sender}</span>
        </div>
      </div>

      {/* Extracted Commitments in Pill Badges */}
      {draft.commitments_found && draft.commitments_found.length > 0 && (
        <div className="mb-3 space-y-1">
          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            Detected Commitments:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {draft.commitments_found.map((commit, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-950/40 border border-emerald-800/50 text-[11px] text-emerald-200"
              >
                <Check className="w-3 h-3 text-emerald-400 shrink-0" />
                <span className="truncate max-w-xs">{commit}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* User clarification notice if incorporated */}
      {draft.user_clarification && (
        <div className="mb-2 px-2.5 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
          <span className="font-semibold">Your input applied: </span>
          <span>{draft.user_clarification}</span>
        </div>
      )}

      {/* Draft Reply Area */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span className="font-medium">Proposed Reply (Gemma):</span>
          {!isApproved && (
            <button
              onClick={() => {
                if (isEditing) {
                  handleSaveText();
                } else {
                  setIsEditing(true);
                }
              }}
              className="text-[11px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
            >
              <Edit3 className="w-3 h-3" />
              <span>{isEditing ? 'Save edits' : 'Edit draft'}</span>
            </button>
          )}
        </div>

        {isEditing ? (
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            rows={5}
            className="w-full p-2.5 rounded-lg bg-slate-950 border border-emerald-500/50 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-400 font-sans resize-y"
          />
        ) : (
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs text-slate-200 whitespace-pre-wrap font-sans leading-relaxed max-h-48 overflow-y-auto">
            {replyText || draft.proposed_reply || '(No reply generated yet)'}
          </div>
        )}
      </div>

      {/* Action: Approve & Schedule */}
      {!isApproved && (
        <button
          onClick={handleApprove}
          disabled={isApproving}
          className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-bold text-xs shadow-md transition disabled:opacity-50"
        >
          {isApproving ? (
            <span>Scheduling...</span>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              <span>Approve &amp; Schedule for {draft.suggested_weekday}</span>
            </>
          )}
        </button>
      )}
    </div>
  );
};
