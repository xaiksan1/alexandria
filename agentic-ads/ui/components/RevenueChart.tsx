"use client";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface DataPoint {
  time: string;
  kwh: number;
}

interface RevenueChartProps {
  data: DataPoint[];
  totalKwh: number;
}

export function RevenueChart({ data, totalKwh }: RevenueChartProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-400">Energon Earned</span>
        <span className="text-2xl font-bold text-emerald-400">
          {totalKwh.toLocaleString()} kWh
        </span>
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={data}>
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#6b7280" }} />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} />
          <Tooltip contentStyle={{ background: "#111", border: "1px solid #374151" }} />
          <Area type="monotone" dataKey="kwh" stroke="#10b981" fill="#10b98120" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
