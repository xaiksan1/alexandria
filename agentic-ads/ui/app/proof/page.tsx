import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ProofPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold">Performance Proofs</h2>
        <Badge variant="outline">Phase 4</Badge>
      </div>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-sm text-gray-400">zk-ML Proofs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">
            Zero-knowledge performance proofs (EZKL / Risc0) — disponibles en Phase 4.
          </p>
          <p className="text-gray-600 text-xs mt-2">
            Phase 3: données brutes d&apos;audit trail disponibles via{" "}
            <code className="text-emerald-600">bid_history</code>.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
