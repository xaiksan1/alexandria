const BID_ENGINE_URL = process.env.NEXT_PUBLIC_BID_ENGINE_URL ?? "http://localhost:3045";
const CACHE_API_URL = process.env.NEXT_PUBLIC_CACHE_API_URL ?? "http://localhost:3044";

export interface OptimizerState {
  vertical: string;
  w1: number;
  w2: number;
  bid_count: number;
  win_rate: number;
  is_reliable: boolean;
}

export interface HealthStatus {
  status: string;
  port: number;
}

async function apiFetch<T>(url: string, label: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url);
  } catch (err) {
    throw new Error(`${label}: network error — ${err}`);
  }
  if (!res.ok) throw new Error(`${label}: HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export function fetchOptimizerState(vertical: string): Promise<OptimizerState> {
  return apiFetch<OptimizerState>(
    `${BID_ENGINE_URL}/optimizer/${encodeURIComponent(vertical)}`,
    "optimizer fetch",
  );
}

export function fetchCacheHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>(`${CACHE_API_URL}/health`, "cache health");
}

export function fetchBidEngineHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>(`${BID_ENGINE_URL}/health`, "bid engine health");
}
