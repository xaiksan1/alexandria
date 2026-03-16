"use client";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

interface CacheGaugeProps {
  hitRate: number; // 0-100
  avgLatencyMs: number;
}

export function CacheGauge({ hitRate, avgLatencyMs }: CacheGaugeProps) {
  const color = hitRate >= 70 ? "text-emerald-400" : hitRate >= 50 ? "text-yellow-400" : "text-red-400";
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-400">Cache Hit Rate</span>
        <span className={`text-2xl font-bold ${color}`}>{hitRate.toFixed(1)}%</span>
      </div>
      <Progress value={hitRate} className="h-3" />
      <div className="flex justify-between text-xs text-gray-500">
        <span>Target: &gt;70%</span>
        <Badge variant="outline" className="text-xs">
          avg {avgLatencyMs.toFixed(2)}ms
        </Badge>
      </div>
    </div>
  );
}
