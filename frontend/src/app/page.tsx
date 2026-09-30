'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  ArrowRight,
  Database,
  Layers,
  ShieldCheck,
  GitMerge,
  Cpu,
  Loader2,
  CheckCircle2,
  FileSearch,
} from 'lucide-react';
import { api } from '@/lib/api';

const EXAMPLE_PROMPTS = [
  {
    title: 'College Event Sponsor Intelligence',
    prompt:
      'Find 30 potential sponsors for a college technical fest in Lucknow. Collect company name, industry, website, public business email, phone, location and source. Remove duplicates and validate the results.',
    tag: 'Sponsorship Intelligence',
    count: 30,
  },
  {
    title: 'B2B Technology Companies',
    prompt:
      'Extract 25 high-growth AI and Cloud startups in Bangalore with company name, founders, website, careers page, funding stage and public contact email.',
    tag: 'Market Intelligence',
    count: 25,
  },
  {
    title: 'Platform & DevOps Talent Intelligence',
    prompt:
      'Gather 40 remote Senior DevOps & Platform Engineer jobs with company name, salary range, tech stack, apply link and verified posting date.',
    tag: 'Talent Intelligence',
    count: 40,
  },
  {
    title: 'Climate & Clean Energy Investor Intelligence',
    prompt:
      'Find 20 venture capital and angel funds in India actively investing in ClimateTech & Clean Energy with portfolio size, lead partner, and contact URL.',
    tag: 'Investment Intelligence',
    count: 20,
  },
];

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState(EXAMPLE_PROMPTS[0].prompt);
  const [targetCount, setTargetCount] = useState<number>(30);
  const [isPlanning, setIsPlanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isPlanning) return;

    setIsPlanning(true);
    setError(null);

    try {
      const response = await api.planWorkflow(prompt, targetCount);
      router.push(`/plan/${response.id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to generate workflow. Ensure FastAPI backend is running on port 8000.');
      setIsPlanning(false);
    }
  };

  return (
    <div className="space-y-12 max-w-5xl mx-auto">
      {/* Hero Section */}
      <div className="text-center space-y-4 pt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold tracking-wide">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AUTONOMOUS DATA INTELLIGENCE PLATFORM</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white">
          From Natural Language to{' '}
          <span className="bg-gradient-to-r from-cyan-400 via-indigo-400 to-fuchsia-400 bg-clip-text text-transparent">
            Actionable Data.
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Eliminate rigid, hardcoded scrapers. Describe the public intelligence you need, and our dynamic AI planner constructs, visualizes, validates, and executes an auditable data pipeline.
        </p>
      </div>

      {/* Main Input Form */}
      <div className="relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 backdrop-blur-xl shadow-2xl shadow-cyan-950/20">
        <form onSubmit={handleGenerateWorkflow} className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="prompt-box" className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Natural Language Intelligence Request
              </label>
              <span className="text-xs text-slate-500">
                AI dynamically infers fields, validation rules & DAG steps
              </span>
            </div>

            <textarea
              id="prompt-box"
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what you need to research, enrich, validate or monitor. For example: Find potential technology partners for our next event and collect company name, industry, website, public contact details, location and source evidence."
              className="w-full p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm sm:text-base focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-sans leading-relaxed resize-none shadow-inner"
              required
            />
          </div>

          {/* Parameters & Action Button */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-xs">
                <span className="text-slate-400">Target Records:</span>
                <input
                  type="number"
                  min={5}
                  max={100}
                  value={targetCount}
                  onChange={(e) => setTargetCount(Number(e.target.value))}
                  className="w-16 bg-slate-900 border border-slate-700 rounded-lg px-2 py-0.5 text-center text-cyan-400 font-mono font-bold focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="hidden md:flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-slate-300">Public & Permitted Sources</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={isPlanning || !prompt.trim()}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-500 to-fuchsia-500 hover:from-cyan-400 hover:via-indigo-400 hover:to-fuchsia-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/25 active:scale-98 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isPlanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Dynamic DAG...</span>
                </>
              ) : (
                <>
                  <span>Generate Workflow</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs">
              <p className="font-semibold">Workflow Generation Error:</p>
              <p className="font-mono mt-1">{error}</p>
            </div>
          )}
        </form>

        {/* Quick Example Prompts / Workflow Templates */}
        <div className="mt-8 pt-6 border-t border-slate-800/80">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-3">
            <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Workflow Templates
            </p>
            <span className="text-[11px] text-slate-500">
              Start with a proven intelligence workflow or describe your own requirement.
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {EXAMPLE_PROMPTS.map((ex, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setPrompt(ex.prompt);
                  setTargetCount(ex.count);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all text-xs flex flex-col justify-between group ${
                  prompt === ex.prompt
                    ? 'bg-cyan-500/10 border-cyan-500/30 text-slate-200'
                    : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1.5">
                  <span className="font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors">
                    {ex.title}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400">
                    {ex.tag}
                  </span>
                </div>
                <p className="line-clamp-2 text-slate-400 text-[11px] leading-relaxed">
                  {ex.prompt}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Product Architecture Differentiators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4">
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Cpu className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white">Genuine Dynamic Planner</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Zero hardcoded keyword scrapers. LLM decomposes requests into typed DAG steps with explicit dependency graphs.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white">RFC & Format Validation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Validates email standards, phone numbers, and URL reachability with confidence integrity scoring.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <GitMerge className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white">Fuzzy Similarity Dedup</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Jaro-Winkler, Levenshtein and root domain matching catches aliases and near-duplicates before consolidation.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <FileSearch className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white">100% Traceability Evidence</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every cell links back to its verified public source URL with exact citation quotes and collection timestamps.
          </p>
        </div>
      </div>
    </div>
  );
}
