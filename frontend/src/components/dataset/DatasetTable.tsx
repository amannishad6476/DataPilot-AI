'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Mail,
  Phone,
  Eye,
  CheckCircle2,
  SlidersHorizontal,
} from 'lucide-react';
import { FieldSpec, RecordItem } from '@/lib/types';
import { EvidenceDrawer } from './EvidenceDrawer';

interface DatasetTableProps {
  fields: FieldSpec[];
  records: RecordItem[];
}

export function DatasetTable({ fields, records }: DatasetTableProps) {
  const [search, setSearch] = useState('');
  const [validFilter, setValidFilter] = useState<'all' | 'valid' | 'invalid'>('all');
  const [confidenceFilter, setConfidenceFilter] = useState<'all' | 'HIGH' | 'MEDIUM' | 'LOW'>('all');
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [selectedRecord, setSelectedRecord] = useState<RecordItem | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(() => fields.map((f) => f.name));
  const [showColumnPicker, setShowColumnPicker] = useState(false);

  const toggleColumn = (colName: string) => {
    setVisibleColumns((prev) =>
      prev.includes(colName)
        ? prev.filter((c) => c !== colName)
        : [...prev, colName]
    );
  };

  // Filter records
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // Validity filter
      if (validFilter === 'valid' && !r.is_valid) return false;
      if (validFilter === 'invalid' && r.is_valid) return false;

      // Confidence level filter
      if (confidenceFilter !== 'all') {
        const lvl = r.confidence_level || (r.confidence_score >= 0.85 ? 'HIGH' : r.confidence_score >= 0.70 ? 'MEDIUM' : 'LOW');
        if (lvl !== confidenceFilter) return false;
      }

      // Search filter
      if (!search.trim()) return true;
      const s = search.toLowerCase();
      return Object.values(r.data).some((val) =>
        String(val).toLowerCase().includes(s)
      );
    });
  }, [records, validFilter, confidenceFilter, search]);

  // Sort records
  const sortedRecords = useMemo(() => {
    if (!sortField) return filteredRecords;
    const sorted = [...filteredRecords];
    sorted.sort((a, b) => {
      let valA = a.data[sortField] ?? '';
      let valB = b.data[sortField] ?? '';

      if (sortField === '_confidence') {
        valA = a.confidence_score;
        valB = b.confidence_score;
      }

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDirection === 'asc' ? valA - valB : valB - valA;
      }

      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      return sortDirection === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
    return sorted;
  }, [filteredRecords, sortField, sortDirection]);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      if (sortDirection === 'asc') setSortDirection('desc');
      else {
        setSortField(null);
        setSortDirection('asc');
      }
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const validCount = records.filter((r) => r.is_valid).length;
  const invalidCount = records.length - validCount;

  return (
    <div className="space-y-4">
      {/* Controls Bar: Search, Filters & Column Picker */}
      <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search across companies, locations, contacts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        {/* Filter Tabs & Column Picker */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Validity Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setValidFilter('all')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                validFilter === 'all'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({records.length})
            </button>
            <button
              onClick={() => setValidFilter('valid')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                validFilter === 'valid'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Valid ({validCount})
            </button>
            <button
              onClick={() => setValidFilter('invalid')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                validFilter === 'invalid'
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              Needs Review ({invalidCount})
            </button>
          </div>

          {/* Confidence Filter */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setConfidenceFilter('all')}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                confidenceFilter === 'all' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Conf
            </button>
            <button
              onClick={() => setConfidenceFilter('HIGH')}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                confidenceFilter === 'HIGH' ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              High
            </button>
            <button
              onClick={() => setConfidenceFilter('MEDIUM')}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                confidenceFilter === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Med
            </button>
            <button
              onClick={() => setConfidenceFilter('LOW')}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                confidenceFilter === 'LOW' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Low
            </button>
          </div>

          {/* Column Picker Button & Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowColumnPicker((prev) => !prev)}
              className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
            >
              <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
              <span>Columns ({visibleColumns.length}/{fields.length})</span>
            </button>

            {showColumnPicker && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-40 p-3 space-y-2">
                <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 text-xs">
                  <span className="font-semibold text-slate-300">Visible Columns</span>
                  <button
                    onClick={() => setVisibleColumns(fields.map((f) => f.name))}
                    className="text-[10px] text-cyan-400 hover:underline"
                  >
                    Reset
                  </button>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto text-xs">
                  {fields.map((f) => (
                    <label
                      key={f.name}
                      className="flex items-center gap-2 px-1.5 py-1 rounded hover:bg-slate-800 cursor-pointer text-slate-300 select-none"
                    >
                      <input
                        type="checkbox"
                        checked={visibleColumns.includes(f.name)}
                        onChange={() => toggleColumn(f.name)}
                        className="rounded border-slate-700 bg-slate-950 text-cyan-500 focus:ring-0"
                      />
                      <span className="font-mono text-[11px] truncate">{f.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 overflow-hidden shadow-xl backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/90 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                <th className="py-3 px-4 w-12 text-center">#</th>
                {fields
                  .filter((f) => visibleColumns.includes(f.name))
                  .map((f) => (
                    <th
                      key={f.name}
                      onClick={() => toggleSort(f.name)}
                      className="py-3 px-4 cursor-pointer hover:text-slate-200 select-none transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{f.name.replace(/_/g, ' ')}</span>
                        {sortField === f.name ? (
                          sortDirection === 'asc' ? (
                            <ArrowUp className="w-3.5 h-3.5 text-cyan-400" />
                          ) : (
                            <ArrowDown className="w-3.5 h-3.5 text-cyan-400" />
                          )
                        ) : (
                          <ArrowUpDown className="w-3 h-3 text-slate-600" />
                        )}
                      </div>
                    </th>
                  ))}
                <th
                  onClick={() => toggleSort('_confidence')}
                  className="py-3 px-4 cursor-pointer hover:text-slate-200 select-none transition-colors w-32"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Quality</span>
                    {sortField === '_confidence' ? (
                      sortDirection === 'asc' ? (
                        <ArrowUp className="w-3.5 h-3.5 text-cyan-400" />
                      ) : (
                        <ArrowDown className="w-3.5 h-3.5 text-cyan-400" />
                      )
                    ) : (
                      <ArrowUpDown className="w-3 h-3 text-slate-600" />
                    )}
                  </div>
                </th>
                <th className="py-3 px-4 text-right w-24">Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sortedRecords.length > 0 ? (
                sortedRecords.map((r, idx) => {
                  const confPercent = Math.round((r.confidence_score || 0.95) * 100);
                  const isSelected = selectedRecord?.id === r.id;

                  return (
                    <tr
                      key={r.id}
                      onClick={() => setSelectedRecord(r)}
                      className={`cursor-pointer transition-colors group ${
                        isSelected
                          ? 'bg-cyan-500/10 hover:bg-cyan-500/15'
                          : idx % 2 === 0
                          ? 'bg-slate-950/40 hover:bg-slate-900/60'
                          : 'bg-slate-900/30 hover:bg-slate-900/60'
                      }`}
                    >
                      <td className="py-3 px-4 text-center font-mono text-slate-500">
                        {idx + 1}
                      </td>

                      {fields
                        .filter((f) => visibleColumns.includes(f.name))
                        .map((f) => {
                          const val = r.data[f.name];
                          const valStr = String(val ?? '');

                          // Smart cell rendering based on type
                          if (f.type === 'url' || f.name.includes('website') || f.name.includes('link')) {
                            return (
                              <td key={f.name} className="py-3 px-4">
                                {valStr ? (
                                  <a
                                    href={valStr}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="text-cyan-400 hover:text-cyan-300 font-mono inline-flex items-center gap-1 max-w-[200px] truncate"
                                    title={valStr}
                                  >
                                    <span className="truncate">{valStr.replace(/^https?:\/\//, '')}</span>
                                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                  </a>
                                ) : (
                                  <span className="text-slate-600 italic">None</span>
                                )}
                              </td>
                            );
                          }

                          if (f.type === 'email' || f.name.includes('email')) {
                            return (
                              <td key={f.name} className="py-3 px-4">
                                {valStr ? (
                                  <a
                                    href={`mailto:${valStr}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className="text-indigo-400 hover:text-indigo-300 font-mono inline-flex items-center gap-1"
                                  >
                                    <Mail className="w-3 h-3 text-indigo-400/70" />
                                    <span>{valStr}</span>
                                  </a>
                                ) : (
                                  <span className="text-slate-600 italic">None</span>
                                )}
                              </td>
                            );
                          }

                          if (f.type === 'phone' || f.name.includes('phone')) {
                            return (
                              <td key={f.name} className="py-3 px-4 font-mono text-slate-300">
                                {valStr ? (
                                  <span className="inline-flex items-center gap-1">
                                    <Phone className="w-3 h-3 text-emerald-400/70" />
                                    {valStr}
                                  </span>
                                ) : (
                                  <span className="text-slate-600 italic">None</span>
                                )}
                              </td>
                            );
                          }

                          return (
                            <td key={f.name} className="py-3 px-4 text-slate-200 font-medium">
                              <span className="truncate max-w-[220px] block" title={valStr}>
                                {valStr || <span className="text-slate-600 italic">None</span>}
                              </span>
                            </td>
                          );
                        })}

                      {/* Quality Score & Level Column */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`font-mono font-semibold px-1.5 py-0.5 rounded text-[10px] ${
                              r.is_valid
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {confPercent}%
                          </span>
                          <span
                            className={`text-[9px] font-mono px-1 py-0.2 rounded uppercase font-bold ${
                              (r.confidence_level || 'HIGH') === 'HIGH'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : (r.confidence_level || 'HIGH') === 'MEDIUM'
                                ? 'bg-amber-500/20 text-amber-300'
                                : 'bg-rose-500/20 text-rose-300'
                            }`}
                          >
                            {r.confidence_level || 'HIGH'}
                          </span>
                        </div>
                      </td>

                      {/* Evidence Action */}
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRecord(r);
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors inline-flex items-center gap-1"
                          title="View extraction citations"
                        >
                          <Eye className="w-4 h-4" />
                          <span className="text-[11px] hidden lg:inline">Audit</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={fields.length + 3} className="py-12 text-center text-slate-500">
                    <p className="text-sm font-medium">No records match your criteria.</p>
                    {search && (
                      <button
                        onClick={() => setSearch('')}
                        className="mt-2 text-xs text-cyan-400 hover:underline"
                      >
                        Clear search filter
                      </button>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Evidence Panel */}
      {selectedRecord && (
        <EvidenceDrawer
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
        />
      )}
    </div>
  );
}
