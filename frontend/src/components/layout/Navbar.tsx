'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Database, Sparkles, History, Cpu, FileCode2, Menu, X } from 'lucide-react';

export function Navbar() {
  const pathname = usePathname();
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const rawApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    const healthUrl = rawApi.replace(/\/api\/?$/, '') + '/health';
    fetch(healthUrl)
      .then((res) => res.json())
      .then((data) => setBackendHealthy(data.status === 'healthy'))
      .catch(() => setBackendHealthy(false));
  }, []);

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-3 group" onClick={() => setMobileMenuOpen(false)}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-fuchsia-500 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/30 transition-all">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Database className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  DATAPILOT AI
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  AI DATA INTELLIGENCE
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                From Natural Language to Actionable Data
              </p>
            </div>
          </Link>

          {/* Desktop Nav links */}
          <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-800">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${pathname === '/'
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
            >
              <Sparkles className="w-4 h-4 text-cyan-400" />
              Pipeline Studio
            </Link>

            <Link
              href="/history"
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${pathname.startsWith('/history')
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
            >
              <History className="w-4 h-4 text-indigo-400" />
              Runs & History
            </Link>

            <Link
              href="/connectors"
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${pathname.startsWith('/connectors')
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
            >
              <Cpu className="w-4 h-4 text-emerald-400" />
              Source Health
            </Link>
          </nav>
        </div>

        {/* Status & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${backendHealthy === true
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse'
                : backendHealthy === false
                  ? 'bg-rose-400'
                  : 'bg-amber-400'
                }`}
            />
            <span className="text-slate-300 font-mono text-[11px]">
              {backendHealthy === true
                ? 'Engine Online'
                : backendHealthy === false
                  ? 'Backend Offline'
                  : 'Connecting...'}
            </span>
          </div>

          <a
            href="https://datapilot-ai-vdi7.onrender.com/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors"
          >
            <FileCode2 className="w-3.5 h-3.5 text-slate-400" />
            FastAPI Docs
          </a>

          {/* Mobile hamburger menu toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 md:hidden transition-colors"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile navigation drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-800 bg-slate-950 px-4 py-3 space-y-2 animate-in slide-in-from-top duration-200">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${pathname === '/'
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
          >
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Pipeline Studio
          </Link>

          <Link
            href="/history"
            onClick={() => setMobileMenuOpen(false)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${pathname.startsWith('/history')
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
          >
            <History className="w-4 h-4 text-indigo-400" />
            Runs & History
          </Link>

          <Link
            href="/connectors"
            onClick={() => setMobileMenuOpen(false)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${pathname.startsWith('/connectors')
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
          >
            <Cpu className="w-4 h-4 text-emerald-400" />
            Source Health
          </Link>

          <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400 font-mono">
            <span>FastAPI Backend Docs:</span>
            <a
              href="https://datapilot-ai-vdi7.onrender.com/docs"
              target="_blank"
              rel="noreferrer"
              className="text-cyan-400 hover:underline"
            >
              /docs
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
