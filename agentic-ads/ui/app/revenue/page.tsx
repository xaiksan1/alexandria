import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RevenueChart } from "@/components/RevenueChart";

export default function RevenuePage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Energon Revenue</h2>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader><CardTitle className="text-sm text-gray-400">Accumulated kWh</CardTitle></CardHeader>
        <CardContent>
          <RevenueChart data={[]} totalKwh={0} />
          <p className="text-xs text-gray-600 mt-4">
            Target: &gt;10 kWh/hour (Phase 2 gate). Revenue confirmed after payment_confirmed=TRUE only.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
