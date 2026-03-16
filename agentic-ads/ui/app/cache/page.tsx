import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CacheGauge } from "@/components/CacheGauge";

export default function CachePage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Semantic Bid Cache — The Moat</h2>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader><CardTitle className="text-sm text-gray-400">Hit Rate</CardTitle></CardHeader>
        <CardContent>
          <CacheGauge hitRate={0} avgLatencyMs={0} />
          <p className="text-xs text-gray-600 mt-4">
            Target: &gt;50% after 7 days (Phase 1) → &gt;70% (Phase 4)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
