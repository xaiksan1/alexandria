import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CacheGauge } from "@/components/CacheGauge";
import { RevenueChart } from "@/components/RevenueChart";

async function getStats() {
  try {
    const [cacheRes, bidRes] = await Promise.all([
      fetch("http://localhost:3044/health", { next: { revalidate: 10 } }),
      fetch("http://localhost:3045/health", { next: { revalidate: 10 } }),
    ]);
    return {
      cache: await cacheRes.json(),
      bids: await bidRes.json(),
    };
  } catch {
    return { cache: null, bids: null };
  }
}

export default async function HomePage() {
  const stats = await getStats();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-emerald-400">
        Agentic-Ads — Alexandria Layer 8
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader><CardTitle className="text-sm text-gray-400">Cache API</CardTitle></CardHeader>
          <CardContent>
            <span className={`text-lg font-bold ${stats.cache ? "text-emerald-400" : "text-red-400"}`}>
              {stats.cache ? "● ONLINE" : "● OFFLINE"}
            </span>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader><CardTitle className="text-sm text-gray-400">Bid Engine</CardTitle></CardHeader>
          <CardContent>
            <span className={`text-lg font-bold ${stats.bids ? "text-emerald-400" : "text-red-400"}`}>
              {stats.bids ? "● ONLINE" : "● OFFLINE"}
            </span>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader><CardTitle className="text-sm text-gray-400">Revenue (24h)</CardTitle></CardHeader>
          <CardContent>
            <RevenueChart data={[]} totalKwh={0} />
          </CardContent>
        </Card>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader><CardTitle className="text-sm text-gray-400">Cache Health</CardTitle></CardHeader>
        <CardContent>
          <CacheGauge hitRate={0} avgLatencyMs={0} />
        </CardContent>
      </Card>
    </div>
  );
}
