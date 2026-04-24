interface GraphControlsProps {
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onFit?: () => void;
  onExport?: () => void;
}

export function GraphControls({
  onZoomIn,
  onZoomOut,
  onFit,
  onExport,
}: GraphControlsProps) {
  return (
    <div className="flex gap-2 bg-ink-800 border border-white/10 rounded-apple-md p-2">
      <button
        onClick={onZoomIn}
        className="p-2 hover:bg-white/5 rounded-apple transition-colors text-ink-200 hover:text-white"
        title="Zoom in"
      >
        ⊕
      </button>
      <button
        onClick={onZoomOut}
        className="p-2 hover:bg-white/5 rounded-apple transition-colors text-ink-200 hover:text-white"
        title="Zoom out"
      >
        ⊖
      </button>
      <div className="w-px bg-white/5" />
      <button
        onClick={onFit}
        className="p-2 hover:bg-white/5 rounded-apple transition-colors text-ink-200 hover:text-white"
        title="Fit to view"
      >
        ◻
      </button>
      <button
        onClick={onExport}
        className="p-2 hover:bg-white/5 rounded-apple transition-colors text-ink-200 hover:text-white"
        title="Export graph"
      >
        ⬇
      </button>
    </div>
  );
}
