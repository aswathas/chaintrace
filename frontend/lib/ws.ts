type HopCallback = (data: unknown) => void;
type DoneCallback = (result: unknown) => void;
type ErrorCallback = (error: string) => void;

export function streamTrace(
  jobId: string,
  onHop: HopCallback,
  onDone: DoneCallback,
  onError?: ErrorCallback
): () => void {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  // Backend WebSocket lives under /api/v1, same as REST routes.
  const wsUrl = backendUrl.replace('http', 'ws') + `/api/v1/trace/${jobId}/stream`;

  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnects = 1;

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'hop') {
          onHop(data.payload);
        } else if (data.type === 'done') {
          onDone(data.payload);
          ws?.close();
        } else if (data.type === 'error') {
          onError?.(data.payload.error || 'Unknown error');
          ws?.close();
        }
      } catch (e) {
        onError?.(`Parse error: ${String(e)}`);
      }
    };

    ws.onerror = () => {
      if (reconnectAttempts < maxReconnects) {
        reconnectAttempts++;
        setTimeout(connect, 1000 * reconnectAttempts);
      } else {
        onError?.('WebSocket connection failed');
      }
    };

    ws.onclose = () => {
      // Normal close
    };
  }

  connect();

  return () => {
    ws?.close();
  };
}
