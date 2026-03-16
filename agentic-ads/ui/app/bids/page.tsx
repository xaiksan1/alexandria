import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BidStream } from "@/components/BidStream";

export default function BidsPage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Live Bid Stream</h2>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader><CardTitle className="text-sm text-gray-400">Real-time auctions</CardTitle></CardHeader>
        <CardContent><BidStream /></CardContent>
      </Card>
    </div>
  );
}
