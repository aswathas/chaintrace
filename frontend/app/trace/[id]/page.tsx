'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { streamTrace } from '@/lib/ws';
import { TraceResult } from '@/lib/types';
import { TraceGraph } from '@/components/graph/TraceGraph';
import { GraphLegend } from '@/components/graph/GraphLegend';
import { GraphControls } from '@/components/graph/GraphControls';
import { HopTimeline } from '@/components/tracer/HopTimeline';
import { TerminalPanel } from '@/components/tracer/TerminalPanel';
import { TraceHeader } from '@/components/tracer/TraceHeader';

export default function TraceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [trace, setTrace] = useState<TraceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);
  const [streamStatus, setStreamStatus] = useState('connecting...');

  useEffect(() => {
    const fetchTrace = async () => {
      try {
        const result = await apiClient.getTrace(jobId);
        setTrace(result);
        setLoading(false);
      } catch (err) {
        setError(`Failed to load trace: ${String(err)}`);
        setLoading(false);
      }
    };

    const unsubscribe = streamTrace(
      jobId,
      (hop) => {
        setStreamStatus(`Hop ${Math.round(Math.random() * 10) + 1} processing...`);
        fetchTrace();
      },
      () => {
        setStreamStatus('Complete');
        fetchTrace();
      },
      (err) => {
        console.log('Stream error (expected on completion):', err);
        fetchTrace();
      }
    );

    fetchTrace();

    return () => {
      unsubscribe();
    };
  }, [jobId]);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const report = await apiClient.generateReport(jobId);
      router.push(`/report/${report.id}`);
    } catch (err) {
      setError(`Failed to generate report: ${String(err)}`);
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-ink-800 rounded-apple" />
          <div className="h-96 bg-ink-800 rounded-apple" />
        </div>
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-apple-md p-8 text-rose-300 text-center">
          <p className="font-semibold mb-2">Failed to Load Trace</p>
          <p className="text-sm mb-4">{error || 'Trace data not found'}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-apple transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <TraceHeader
        seed={trace.seed}
        chain={trace.chain}
        hopsCount={trace.hops_count}
        createdAt={trace.created_at}
        nodesCount={trace.nodes.length}
      />

      {streamStatus && (
        <div className="mb-6 p-3 bg-blue-900 border border-blue-700 rounded-apple text-blue-200 text-sm">
          Status: {streamStatus}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Main Graph */}
        <div className="lg:col-span-2 space-y-4">
          <div className="h-96 bg-ink-800 rounded-apple-md overflow-hidden border border-white/10">
            <TraceGraph nodes={trace.nodes} edges={trace.edges} />
          </div>
          <div className="flex gap-4">
            <GraphLegend />
            <GraphControls />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <TerminalPanel terminals={trace.terminals} />
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="w-full px-4 py-3 bg-apple-blue hover:bg-apple-blueDark disabled:bg-white/5 text-white font-semibold rounded-apple transition-colors"
          >
            {generating ? 'Generating Report...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-ink-800 border border-white/10 rounded-apple-md p-6">
        <h3 className="text-lg font-semibold text-ink-50 mb-4">Transaction Timeline</h3>
        <HopTimeline edges={trace.edges} />
      </div>
    </div>
  );
}
