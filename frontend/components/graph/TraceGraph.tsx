'use client';

import { useEffect, useRef, useState } from 'react';
import CytoscapeComponent from 'cytoscape';
import coseLayout from 'cytoscape-cose-bilkent';
import { TraceNode, TraceEdge } from '@/lib/types';
import { terminalTypeColor, formatUsd } from '@/lib/format';

CytoscapeComponent.use(coseLayout);

interface TraceGraphProps {
  nodes: TraceNode[];
  edges: TraceEdge[];
  onSelectNode?: (node: TraceNode) => void;
}

export function TraceGraph({ nodes, edges, onSelectNode }: TraceGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<CytoscapeComponent.Core | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const cytoscape = CytoscapeComponent as unknown as typeof CytoscapeComponent;

      const cy = cytoscape({
        container: containerRef.current,
        headless: false,
        styleEnabled: true,
        elements: [
          ...nodes.map((node) => ({
            data: {
              id: `${node.address}-${node.chain}`,
              label: node.address.slice(0, 6),
              address: node.address,
              terminal: node.terminal_type,
              balance: node.balance_usd,
            },
          })),
          ...edges.map((edge, idx) => ({
            data: {
              id: `edge-${idx}`,
              source: `${edge.from}-${edge.chain}`,
              target: `${edge.to}-${edge.chain}`,
              value: edge.value_usd,
              tx: edge.tx_hash,
            },
          })),
        ],
        style: [
          {
            selector: 'node',
            style: {
              'background-color': (ele: any) =>
                terminalTypeColor(ele.data('terminal') || 'unknown'),
              label: (ele: any) => ele.data('label'),
              'font-size': '10px',
              color: '#fff',
              'text-opacity': 0.9,
              width: 30,
              height: 30,
              'border-width': 1,
              'border-color': '#28282b',
              padding: '5',
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 3,
              'border-color': '#2997ff',
              'background-color': '#0071e3',
            },
          },
          {
            selector: 'edge',
            style: {
              width: (ele: any) => {
                const val = ele.data('value') ?? 0;
                return Math.max(1, Math.min(5, Math.log(val + 1) / 2));
              },
              'line-color': '#6e6e73',
              'target-arrow-color': '#6e6e73',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              opacity: 0.6,
            },
          },
        ] as any,
        layout: {
          name: 'cose-bilkent',
          animate: true,
          animationDuration: 500,
          nodeDimensionsIncludeLabels: true,
          fit: true,
          padding: 30,
          quality: 'default',
          randomize: false,
          numIter: 1000,
        } as any,
      });

      cyRef.current = cy;

      cy.on('tap', 'node', (event) => {
        const node = event.target;
        const address = node.data('address');
        const foundNode = nodes.find(
          (n) => n.address === address
        );
        if (foundNode) {
          onSelectNode?.(foundNode);
        }
      });
    } catch (e) {
      setError(`Failed to initialize graph: ${String(e)}`);
    }

    return () => {
      cyRef.current?.destroy();
    };
  }, [nodes, edges, onSelectNode]);

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-ink-800 border border-red-600 rounded-apple text-red-300">
        <div className="text-center p-4">
          <p className="font-semibold mb-2">Graph Initialization Error</p>
          <p className="text-sm opacity-75">{error}</p>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-ink-800 rounded-apple text-ink-300">
        <p className="text-center">No trace data available</p>
      </div>
    );
  }

  return <div ref={containerRef} className="w-full h-full bg-ink-800 rounded-apple" />;
}
