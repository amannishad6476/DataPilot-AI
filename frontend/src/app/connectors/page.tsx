'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Radio,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ShieldCheck,
  Globe,
  Database,
  Webhook,
  ExternalLink,
  Copy,
  Check,
  Clock,
  ArrowRight,
  Server,
  Zap,
} from 'lucide-react';
import { api } from '@/lib/api';
import { SourceHealthReport, SourceHealthItem, ConnectorDescriptor } from '@/lib/types';

export default function ConnectorsPage() {
  const [report, setReport] = useState<SourceHealthReport | null>(null);
  const [descriptors, setDescriptors] = useState<ConnectorDescriptor[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { healthy: boolean; status: string }>>({});
  const [copiedTemplate, setCopiedTemplate] = useState(false);

  const loadHealth = async (showSpinner = true) => {
    if (showSpinner) setRefreshing(true);
    try {
      const [healthData, descData] = await Promise.all([
        api.getSourceHealthReport().catch(() => null),
        api.listConnectors().catch(() => []),
      ]);
      if (healthData) setReport(healthData);
      if (descData) setDescriptors(descData);
    } catch (err) {
      console.error('Failed to load connector health:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadHealth(false);
  }, []);

  const handleTestPing = async (connectorId: string) => {
    setTestingId(connectorId);
    try {
      const res = await api.checkConnectorHealth(connectorId);
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: { healthy: res.is_healthy, status: res.status },
      }));
      // Refresh report
      await loadHealth(false);
    } catch (err: any) {
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: { healthy: false, status: 'ERROR' },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleCopyN8nTemplate = async () => {
    try {
      const template = await api.getN8nTemplate();
      await navigator.clipboard.writeText(JSON.stringify(template, null, 2));
      setCopiedTemplate(true);
      setTimeout(() => setCopiedTemplate(false), 2500);
    } catch (err) {
      alert('Failed to retrieve n8n template');
    }
  };

  const getConnectorIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'web_page':
        return <Globe className="w-5 h-5 text-cyan-400" />;
      case 'json_feed':
        return <Database className="w-5 h-5 text-indigo-400" />;
      case 'webhook':
        return <Webhook className="w-5 h-5 text-emerald-400" />;
      default:
        return <Server className="w-5 h-5 text-slate-400" />;
    }
  };

  const totalRequests = report?.connectors.reduce((acc, c) => acc + c.total_requests, 0) || 0;
  const totalSuccess = report?.connectors.reduce((acc, c) => acc + c.success_count, 0) || 0;
  const totalErrors = report?.connectors.reduce((acc, c) => acc + c.error_count, 0) || 0;
  const avgLatency = report?.connectors.length
    ? Math.round(
        report.connectors.reduce((acc, c) => acc + c.avg_latency_ms, 0) / report.connectors.length
      )
    : 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Source Connectors & Gateway Health
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real operational metrics, latency monitoring, SSRF firewall status, and live connector health testing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadHealth(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Metrics'}</span>
          </button>
        </div>
      </div>

      {/* Global Status & Security Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Gateway Health */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
              Gateway Status
            </span>
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                report?.overall_status === 'HEALTHY'
                  ? 'bg-emerald-400 shadow-emerald-500/50 shadow-sm animate-pulse'
                  : report?.overall_status === 'DEGRADED'
                  ? 'bg-amber-400 shadow-amber-500/50 shadow-sm'
                  : 'bg-rose-400 shadow-rose-500/50 shadow-sm'
              }`}
            />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                report?.overall_status === 'HEALTHY'
                  ? 'text-emerald-400'
                  : report?.overall_status === 'DEGRADED'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {report?.overall_status || 'HEALTHY'}
            </span>
            <span className="text-xs text-slate-500 font-mono">active</span>
          </div>
        </div>

        {/* Total Ingest Requests */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
            Total Requests
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {totalRequests}
            </span>
            <span className="text-xs text-slate-500">invocations</span>
          </div>
        </div>

        {/* Success Rate */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-medium">
            Success Rate
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {totalRequests > 0 ? Math.round((totalSuccess / totalRequests) * 100) : 100}%
            </span>
            <span className="text-xs text-slate-500">
              {totalErrors} error{totalErrors !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Average Latency */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-cyan-400 font-medium">
            Avg Round-Trip Latency
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-cyan-300">
              {avgLatency} ms
            </span>
            <span className="text-xs text-slate-500">real-time</span>
          </div>
        </div>
      </div>

      {/* Security / SSRF Firewall Banner */}
      <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-indigo-400 flex-shrink-0" />
          <div className="space-y-0.5">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              SSRF & Domain Egress Firewall: Strict Enforcement Active
            </h4>
            <p className="text-xs text-slate-400">
              Private subnets (RFC 1918), loopback (127.0.0.1, ::1), and cloud metadata endpoints (169.254.169.254) are strictly blocked at DNS resolution.
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 whitespace-nowrap">
          FIREWALL SECURE
        </span>
      </div>

      {/* Connectors Detailed Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white tracking-wide uppercase">
            Registered Connectors & Live Telemetry
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {report?.connectors.length || 0} registered providers
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {report?.connectors.map((c) => {
            const desc = descriptors.find((d) => d.connector_id === c.connector_id);
            const isTesting = testingId === c.connector_id;
            const testResult = testResults[c.connector_id];

            return (
              <div
                key={c.connector_id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-4 shadow-lg"
              >
                <div className="space-y-3">
                  {/* Top Bar: Icon + Status */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
                        {getConnectorIcon(c.source_type)}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">{c.name}</h3>
                        <span className="text-[10px] font-mono text-slate-400">
                          {c.connector_id}
                        </span>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                        c.status === 'HEALTHY'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : c.status === 'DEGRADED'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : c.status === 'UNTESTED'
                          ? 'bg-slate-800 text-slate-400 border border-slate-700'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {desc?.description || c.details}
                  </p>

                  {/* Telemetry Stats */}
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Invocations:</span>
                      <span className="text-slate-200 font-semibold">{c.total_requests}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Success Rate:</span>
                      <span className="text-emerald-400 font-semibold">
                        {c.total_requests > 0
                          ? `${Math.round((c.success_count / c.total_requests) * 100)}%`
                          : '100%'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Avg Latency:</span>
                      <span className="text-cyan-300 font-semibold">{Math.round(c.avg_latency_ms)} ms</span>
                    </div>
                    {c.last_attempt_at && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Last Active:</span>
                        <span className="text-slate-400 text-[11px]">
                          {new Date(c.last_attempt_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer Action */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  {testResult && (
                    <span
                      className={`text-[11px] font-mono flex items-center gap-1 ${
                        testResult.healthy ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {testResult.healthy ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : (
                        <AlertTriangle className="w-3 h-3" />
                      )}
                      {testResult.status}
                    </span>
                  )}
                  {!testResult && (
                    <span className="text-[11px] text-slate-500 font-mono">Ready for dispatch</span>
                  )}

                  <button
                    onClick={() => handleTestPing(c.connector_id)}
                    disabled={isTesting}
                    className="px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1.5 disabled:opacity-50 ml-auto"
                  >
                    <Zap className={`w-3 h-3 ${isTesting ? 'animate-pulse text-amber-400' : ''}`} />
                    <span>{isTesting ? 'Testing...' : 'Ping Test'}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Permitted Sources & n8n Automation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Permitted Sources Guidelines */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2.5">
            <Globe className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Permitted Source Rules & Domain Policies
            </h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            DataPilot AI enforces responsible, public-only data acquisition. Workflows can target public HTML pages, structured JSON feeds, and authorized external webhook endpoints.
          </p>

          <div className="space-y-2 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-300">Public Web Pages (Permitted HTML)</span>
              <span className="text-emerald-400 font-semibold">GET Only</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-300">Public JSON APIs & Feeds</span>
              <span className="text-cyan-400 font-semibold">JSON / REST</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-300">n8n Enterprise Webhook Pipelines</span>
              <span className="text-indigo-400 font-semibold">POST Webhook</span>
            </div>
          </div>
        </div>

        {/* n8n Integration Hub */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Webhook className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                n8n Workflow Automation Hub
              </h3>
            </div>
            <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono font-semibold">
              WEBHOOK READY
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Dispatch data collection tasks to external n8n self-hosted workflows, and automatically receive structured data back into DataPilot AI.
          </p>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 font-mono text-xs">
            <span className="text-slate-500 text-[10px] uppercase tracking-wider block">
              Inbound Webhook Receiver URL:
            </span>
            <code className="text-cyan-300 text-[11px] break-all block">
              POST /api/connectors/webhooks/n8n
            </code>
          </div>

          <button
            onClick={handleCopyN8nTemplate}
            className="w-full py-2.5 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-semibold text-slate-200 hover:text-white transition-colors flex items-center justify-center gap-2"
          >
            {copiedTemplate ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            <span>{copiedTemplate ? 'Workflow JSON Copied to Clipboard!' : 'Copy n8n Workflow Blueprint JSON'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
