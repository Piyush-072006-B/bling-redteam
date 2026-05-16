import { useState, useEffect, useRef, useCallback } from 'react';

const RECONNECT_BASE_MS = 1500;
const RECONNECT_MAX_MS = 15000;
const API_BASE = 'http://localhost:8081';

export function useSandboxSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [], metrics: {}, lineage: [] });
  const [status, setStatus] = useState({ state: 'IDLE' });
  const [lastPacket, setLastPacket] = useState(null);
  const [lastMutation, setLastMutation] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const ws = useRef(null);
  const reconnectTimer = useRef(null);
  const reconnectAttempt = useRef(0);
  const isMounted = useRef(true);

  // ── Backend health probe ──────────────────────────────────────────────────
  useEffect(() => {
    const probe = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
        const data = await r.json();
        if (isMounted.current) setBackendHealth(data);
      } catch {
        if (isMounted.current) setBackendHealth(null);
      }
    };
    probe();
    const id = setInterval(probe, 5000);
    return () => clearInterval(id);
  }, []);

  // ── WebSocket with exponential-backoff reconnect ──────────────────────────
  const connect = useCallback(() => {
    if (!isMounted.current) return;

    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      if (!isMounted.current) return;
      reconnectAttempt.current = 0;
      setIsConnected(true);
      setReconnectCount(0);
    };

    socket.onclose = () => {
      if (!isMounted.current) return;
      setIsConnected(false);

      // Exponential backoff capped at RECONNECT_MAX_MS
      const delay = Math.min(
        RECONNECT_BASE_MS * Math.pow(1.6, reconnectAttempt.current),
        RECONNECT_MAX_MS
      );
      reconnectAttempt.current += 1;
      setReconnectCount(reconnectAttempt.current);
      reconnectTimer.current = setTimeout(connect, delay);
    };

    socket.onerror = () => {
      // onclose fires after onerror, so reconnect is handled there
      socket.close();
    };

    socket.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }

      if (msg.type === 'FULL_STATE') {
        setGraphData(msg.data);
      } else if (msg.type === 'STATUS_UPDATE') {
        setStatus(msg.data);
      } else if (msg.type === 'GRAPH_UPDATE') {
        const e = msg.data;
        setLastPacket(e);
        setGraphData(prev => {
          const newNodes = [...prev.nodes];
          if (!newNodes.find(n => n.id === e.node_from)) newNodes.push({ id: e.node_from, type: e.attack_type ? 'suspicious' : 'normal' });
          if (!newNodes.find(n => n.id === e.node_to))   newNodes.push({ id: e.node_to,   type: e.attack_type ? 'suspicious' : 'normal' });
          const newLinks = [...prev.links, { source: e.node_from, target: e.node_to, attack_type: e.attack_type }];
          return { ...prev, nodes: newNodes, links: newLinks };
        });
      } else if (msg.type === 'MUTATION_EVENT') {
        setLastMutation(msg.data);
      } else if (msg.type === 'EVASION_EVENT') {
        setLastMutation(msg.data);
      } else if (msg.type === 'METRICS_UPDATE') {
        setGraphData(prev => ({ ...prev, metrics: msg.data }));
      }
    };
  }, [url]);

  useEffect(() => {
    isMounted.current = true;
    connect();
    return () => {
      isMounted.current = false;
      clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  // ── REST helpers ──────────────────────────────────────────────────────────
  const apiCall = async (endpoint, payload = null) => {
    const opts = { method: 'POST' };
    if (payload) {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(payload);
    }
    const r = await fetch(`${API_BASE}/api/sandbox/${endpoint}`, opts);
    return r.json();
  };

  const startSandbox = (config) => apiCall('start', config);
  const stopSandbox  = ()       => apiCall('stop');
  const createBundle = ()       => apiCall('bundle');
  const clearGraph   = ()       => apiCall('clear');

  return {
    isConnected,
    backendHealth,
    graphData,
    status,
    startSandbox,
    stopSandbox,
    createBundle,
    clearGraph,
    lastPacket,
    lastMutation,
    reconnectCount,
  };
}
