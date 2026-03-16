"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

interface BidEvent {
  bid_id: string;
  vertical: string;
  winner: boolean;
  cache_hit: boolean;
  latency_ms: number;
  timestamp: string;
}

export function BidStream() {
  const [events, setEvents] = useState<BidEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Connect to cortex-ws port 8083 (read-only subscription)
    let ws: WebSocket;
    try {
      ws = new WebSocket("ws://localhost:8083/bids");
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as BidEvent;
          setEvents((prev) => [event, ...prev].slice(0, 50));
        } catch {}
      };
    } catch {
      setConnected(false);
    }
    return () => ws?.close();
  }, []);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Live Bid Stream</span>
        <Badge variant={connected ? "default" : "outline"} className="text-xs">
          {connected ? "● LIVE" : "disconnected"}
        </Badge>
      </div>
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {events.length === 0 && (
          <p className="text-xs text-gray-600">Waiting for bids...</p>
        )}
        {events.map((e) => (
          <div key={e.bid_id} className="flex gap-2 text-xs py-1 border-b border-gray-800">
            <span className="text-gray-500">{e.vertical}</span>
            <Badge variant={e.winner ? "default" : "secondary"} className="text-xs">
              {e.winner ? "WIN" : "LOSS"}
            </Badge>
            {e.cache_hit && <Badge variant="outline" className="text-xs">CACHED</Badge>}
            <span className="text-gray-600 ml-auto">{e.latency_ms}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}
