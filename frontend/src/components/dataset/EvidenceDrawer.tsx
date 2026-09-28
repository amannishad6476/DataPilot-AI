'use client';

import React from 'react';
import { X, ExternalLink, ShieldCheck, AlertTriangle, Clock, Database, CheckCircle2 } from 'lucide-react';
import { RecordItem } from '@/lib/types';

interface EvidenceDrawerProps {
  record: RecordItem | null;
  onClose: () => void;
}

export function EvidenceDrawer({ record, onClose }: EvidenceDrawerProps) {
  if (!record) return null;

  const entityTitle =
    record.data.company_name ||
    record.data.job_title ||
    record.data.entity_name ||
    'Selected Record';

  const confidencePercent = Math.round((record.confidence_score || 0.95) * 100);

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-slate-900 border-l border-slate-800 shadow-2xl z-50 p-6 flex flex-col justify-between overflow-y-auto">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Evidence & Audit Trail
            </span>
            <span className="text-xs text-slate-500 font-mono">
              ID: {record.id.slice(0, 8)}...
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Record Title */}
        <div className="mt-4">
          <h2 className="text-xl font-bold text-white tracking-tight">
            {entityTitle}
          </h2>
          {record.data.industry && (
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Industry: {record.data.industry}
            </p>
          )}
        </div>

        {/* Quality Score Meter */}
        <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Confidence & Integrity Score
            </span>
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                confidencePercent >= 85
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}
            >
              {confidencePercent}% Verified
            </span>
          </div>

          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mb-2">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                confidencePercent >= 85 ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            {record.is_valid ? (
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Passed RFC schema & reachability checks
              </span>
            ) : (
              <span className="flex items-center gap-1 text-rose-400 font-medium">
                <AlertTriangle className="w-3.5 h-3.5" />
                Validation warnings flagged
              </span>
            )}
          </div>
        </div>

        {/* Validation Issues if any */}
        {record.validation_errors && record.validation_errors.length > 0 && (
          <div className="mt-4 p-3 rounded-xl bg-rose-950/30 border border-rose-500/30">
            <h4 className="text-xs font-semibold text-rose-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              Flagged Issues ({record.validation_errors.length})
            </h4>
            <ul className="space-y-1">
              {record.validation_errors.map((err, i) => (
                <li key={i} className="text-xs text-rose-200/90 font-mono">
                  • {err}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Field Validation & Normalization Audit Trail */}
        {record.field_validations && Object.keys(record.field_validations).length > 0 && (
          <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Field Validation & Normalization Audits
            </span>
            <div className="space-y-2">
              {Object.entries(record.field_validations).map(([fKey, fStatus]) => {
                const transforms = record.field_transformations?.[fKey] || [];
                return (
                  <div key={fKey} className="p-2 rounded-lg bg-slate-900/70 border border-slate-800/80 text-xs flex flex-col gap-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-slate-300 font-semibold">{fKey}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono uppercase font-bold ${
                          fStatus === 'VALID'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : fStatus === 'MISSING'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {fStatus}
                      </span>
                    </div>
                    {transforms.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {transforms.map((t, tidx) => (
                          <span key={tidx} className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-cyan-300">
                            {t.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Traceability Citations */}
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Source Citations & Extraction Proof ({record.evidence_items?.length || 0})
          </h3>

          <div className="space-y-3">
            {record.evidence_items && record.evidence_items.length > 0 ? (
              record.evidence_items.map((ev) => (
                <div
                  key={ev.id}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      Field: {ev.field_name}
                    </span>
                    <span className="text-[11px] font-mono text-emerald-400">
                      {Math.round(ev.confidence * 100)}% match
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 italic mb-2.5 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80 leading-relaxed">
                    &ldquo;{ev.snippet}&rdquo;
                  </p>

                  <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60">
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 truncate max-w-[260px]"
                    >
                      <span className="truncate">{ev.source_url}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>

                    <span className="text-slate-500 font-mono text-[10px]">
                      {new Date(ev.collected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic">No direct citation snippets linked.</p>
            )}
          </div>
        </div>

        {/* Raw Fields Explorer */}
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Structured Data Attributes
          </h3>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 overflow-x-auto">
            <dl className="space-y-2 text-xs">
              {Object.entries(record.data).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-slate-900 pb-1.5 last:border-0 last:pb-0">
                  <dt className="text-slate-400 font-mono">{k}:</dt>
                  <dd className="text-slate-200 font-mono font-medium text-right truncate max-w-[240px]" title={String(v)}>
                    {String(v) || <span className="text-slate-600">null</span>}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 mt-6">
        <button
          onClick={onClose}
          className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
}
