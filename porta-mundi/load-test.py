#!/usr/bin/env python3
"""
PORTA-MUNDI LOAD TEST SUITE
Comprehensive stress testing for the Porta-Mundi security gateway
with real-time metric monitoring and threat simulation
"""

import requests
import threading
import time
import json
import statistics
from datetime import datetime
from collections import defaultdict
import urllib.request
import concurrent.futures

class LoadTestSuite:
    def __init__(self, gateway_host="localhost", gateway_port=8822,
                 prometheus_host="localhost", prometheus_port=9091):
        self.gateway_url = f"http://{gateway_host}:{gateway_port}"
        self.prometheus_url = f"http://{prometheus_host}:{prometheus_port}"

        self.results = defaultdict(list)
        self.errors = defaultdict(int)
        self.lock = threading.Lock()

        print("\n" + "="*80)
        print("PORTA-MUNDI LOAD TEST SUITE")
        print("="*80)
        print(f"Gateway: {self.gateway_url}")
        print(f"Prometheus: {self.prometheus_url}")
        print("="*80 + "\n")

    def get_prometheus_metric(self, query):
        """Fetch a metric from Prometheus"""
        try:
            url = f"{self.prometheus_url}/api/v1/query?query={query}"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read())
            if data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            return 0
        except:
            return None

    def print_metrics_snapshot(self, phase):
        """Print current Prometheus metrics"""
        print(f"\n📊 Metrics Snapshot - {phase}")
        print("-" * 80)

        metrics = {
            "Vault Unsealed": "vault_core_unsealed",
            "Vault Active": "vault_core_active",
            "Token Count": "vault_token_count",
            "Goroutines": "vault_runtime_num_goroutines",
            "Memory (MB)": "vault_runtime_alloc_bytes",
        }

        for name, query in metrics.items():
            value = self.get_prometheus_metric(query)
            if value is not None:
                if "Memory" in name:
                    value = value / (1024*1024)
                    print(f"  {name:25s}: {value:.2f} MB")
                else:
                    print(f"  {name:25s}: {value:.0f}")
        print("-" * 80)

    def health_check(self):
        """Test basic connectivity to gateway"""
        print("\n🏥 PHASE 1: HEALTH CHECK")
        print("-" * 80)

        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=5)
            print(f"✓ Gateway is UP (Status: {response.status_code})")
            self.print_metrics_snapshot("Health Check")
            return True
        except Exception as e:
            print(f"✗ Gateway is DOWN: {e}")
            return False

    def baseline_test(self, num_requests=10):
        """Establish baseline metrics"""
        print(f"\n📈 PHASE 2: BASELINE TEST ({num_requests} requests)")
        print("-" * 80)

        def make_request():
            try:
                start = time.time()
                response = requests.get(f"{self.gateway_url}/metrics", timeout=5)
                duration = (time.time() - start) * 1000

                with self.lock:
                    self.results['baseline'].append(duration)
                    if response.status_code == 200:
                        print(f"✓ Request completed in {duration:.2f}ms")
                    else:
                        print(f"⚠ Request completed with status {response.status_code}")
            except Exception as e:
                with self.lock:
                    self.errors['baseline'] += 1
                print(f"✗ Request failed: {str(e)[:50]}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            concurrent.futures.wait(futures)

        if self.results['baseline']:
            avg = statistics.mean(self.results['baseline'])
            print(f"\n📊 Baseline Results:")
            print(f"  Average latency: {avg:.2f}ms")
            print(f"  Min: {min(self.results['baseline']):.2f}ms")
            print(f"  Max: {max(self.results['baseline']):.2f}ms")
            print(f"  Errors: {self.errors['baseline']}")

        self.print_metrics_snapshot("After Baseline")

    def gradual_load_test(self, initial=50, peak=200, step=50, duration_per_step=5):
        """Gradually increase load to find breaking point"""
        print(f"\n🔥 PHASE 3: GRADUAL LOAD TEST")
        print(f"   Initial: {initial} req/s | Peak: {peak} req/s")
        print("-" * 80)

        for load_level in range(initial, peak + 1, step):
            print(f"\n⚡ Load Level: {load_level} requests/sec (for {duration_per_step}s)")

            start_time = time.time()
            requests_sent = 0

            def make_request():
                nonlocal requests_sent
                try:
                    start = time.time()
                    response = requests.get(
                        f"{self.gateway_url}/metrics",
                        timeout=2
                    )
                    duration = (time.time() - start) * 1000

                    with self.lock:
                        self.results[f'load_{load_level}'].append(duration)
                        requests_sent += 1
                except Exception as e:
                    with self.lock:
                        self.errors[f'load_{load_level}'] += 1

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                while time.time() - start_time < duration_per_step:
                    for _ in range(load_level):
                        executor.submit(make_request)
                    time.sleep(0.1)

            if self.results[f'load_{load_level}']:
                avg = statistics.mean(self.results[f'load_{load_level}'])
                errors = self.errors[f'load_{load_level}']
                success_rate = ((len(self.results[f'load_{load_level}']) /
                               (len(self.results[f'load_{load_level}']) + errors)) * 100) if (len(self.results[f'load_{load_level}']) + errors) > 0 else 0
                print(f"  Average latency: {avg:.2f}ms | Success rate: {success_rate:.1f}% | Errors: {errors}")

            time.sleep(1)

        self.print_metrics_snapshot("After Gradual Load")

    def ddos_simulation(self, duration=10, concurrent_connections=100):
        """Simulate DDoS attack pattern"""
        print(f"\n💥 PHASE 4: DDoS SIMULATION")
        print(f"   Duration: {duration}s | Concurrent: {concurrent_connections}")
        print("-" * 80)

        print(f"⚠️  Launching simulated attack pattern...")

        start_time = time.time()
        request_count = 0

        def attack_request():
            nonlocal request_count
            try:
                # Rapid-fire requests to simulate botnet
                response = requests.get(
                    f"{self.gateway_url}/metrics",
                    headers={'X-Threat': 'simulated-ddos'},
                    timeout=1
                )
                request_count += 1
            except:
                self.errors['ddos'] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            while time.time() - start_time < duration:
                for _ in range(concurrent_connections):
                    executor.submit(attack_request)
                time.sleep(0.1)

        elapsed = time.time() - start_time
        rps = request_count / elapsed if elapsed > 0 else 0

        print(f"\n📊 DDoS Simulation Results:")
        print(f"  Total requests: {request_count}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Requests/sec: {rps:.2f}")
        print(f"  Errors: {self.errors['ddos']}")

        self.print_metrics_snapshot("During DDoS Attack")

    def stress_burst(self, num_bursts=5, burst_size=500):
        """Send sudden traffic bursts"""
        print(f"\n💢 PHASE 5: STRESS BURST TEST")
        print(f"   Bursts: {num_bursts} | Size per burst: {burst_size}")
        print("-" * 80)

        for burst_num in range(1, num_bursts + 1):
            print(f"\n🔴 Burst {burst_num}/{num_bursts} ({burst_size} requests)")

            def burst_request():
                try:
                    start = time.time()
                    response = requests.get(
                        f"{self.gateway_url}/metrics",
                        timeout=3
                    )
                    duration = (time.time() - start) * 1000
                    with self.lock:
                        self.results[f'burst_{burst_num}'].append(duration)
                except Exception as e:
                    with self.lock:
                        self.errors[f'burst_{burst_num}'] += 1

            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(burst_request) for _ in range(burst_size)]
                concurrent.futures.wait(futures)

            if self.results[f'burst_{burst_num}']:
                avg = statistics.mean(self.results[f'burst_{burst_num}'])
                print(f"  Burst complete | Avg latency: {avg:.2f}ms | Errors: {self.errors[f'burst_{burst_num}']}")

            time.sleep(2)  # Cool down between bursts

        self.print_metrics_snapshot("After Stress Bursts")

    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("📋 FINAL REPORT")
        print("="*80)

        print("\n📊 Summary by Phase:")
        print("-" * 80)

        for phase in ['baseline', 'load_50', 'load_100', 'load_150', 'load_200']:
            if self.results[phase]:
                avg = statistics.mean(self.results[phase])
                errors = self.errors[phase]
                total = len(self.results[phase]) + errors
                success_rate = (len(self.results[phase]) / total * 100) if total > 0 else 0

                phase_name = phase.replace('_', ' ').title()
                print(f"\n{phase_name}:")
                print(f"  Requests: {total}")
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Avg latency: {avg:.2f}ms")
                print(f"  Min/Max: {min(self.results[phase]):.2f}ms / {max(self.results[phase]):.2f}ms")

        print("\n" + "-"*80)
        print("✅ Load test complete!")
        print("\n🔍 Check Grafana for live metrics:")
        print("   → http://localhost:3011/d/vault-dashboard/vault-secrets-management")
        print("\n📈 Prometheus queries:")
        print("   → http://localhost:9091/graph")
        print("="*80 + "\n")

    def run_full_test(self):
        """Run complete test suite"""
        if not self.health_check():
            print("❌ Gateway is not responding. Aborting.")
            return

        time.sleep(2)
        self.baseline_test(num_requests=10)

        time.sleep(3)
        self.gradual_load_test(initial=50, peak=200, step=50, duration_per_step=5)

        time.sleep(3)
        self.ddos_simulation(duration=10, concurrent_connections=100)

        time.sleep(3)
        self.stress_burst(num_bursts=3, burst_size=500)

        self.generate_report()


if __name__ == "__main__":
    import sys

    # Parse command line args
    gateway_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    gateway_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8822

    suite = LoadTestSuite(gateway_host=gateway_host, gateway_port=gateway_port)
    suite.run_full_test()
