#!/usr/bin/env python3
"""
INTEGRATED LOAD TEST SUITE
Test Vault metrics and Docker services with load generation
"""

import requests
import threading
import time
import json
import statistics
from collections import defaultdict
import urllib.request
import concurrent.futures

class IntegratedLoadTest:
    def __init__(self):
        self.vault_url = "http://localhost:8200"
        self.prometheus_url = "http://localhost:9091"
        self.module_endpoints = {
            "aegis": "http://localhost:7000/health",
            "phoenix": "http://localhost:8082/health",
            "aker": "http://localhost:8888/health",
            "zangetsu": "http://localhost:7500/health",
            "sentinelle": "http://localhost:9000/health",
            "chapel-xvi": "http://localhost:6001/health",
            "paint-shop": "http://localhost:5000/health",
            "alexa": "http://localhost:8777/health",
            "kheper": "http://localhost:9999/health",
        }

        self.results = defaultdict(list)
        self.errors = defaultdict(int)
        self.lock = threading.Lock()

        print("\n" + "="*80)
        print("INTEGRATED LOAD TEST - PORTA-MUNDI ECOSYSTEM")
        print("="*80)
        print(f"Vault: {self.vault_url}")
        print(f"Prometheus: {self.prometheus_url}")
        print(f"Docker Modules: 9 services")
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
            "Vault Status": "vault_core_unsealed",
            "Active Leader": "vault_core_active",
            "Token Count": "vault_token_count",
            "Cache Hits": "vault_cache_hit",
            "Cache Misses": "vault_cache_miss",
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

    def test_module_health(self):
        """Test all Docker module endpoints"""
        print("\n🏥 PHASE 1: MODULE HEALTH CHECK")
        print("-" * 80)

        up_count = 0
        down_count = 0

        for module, url in self.module_endpoints.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print(f"✓ {module:20s} UP (Status: {response.status_code})")
                    up_count += 1
                else:
                    print(f"⚠ {module:20s} RESPONDING (Status: {response.status_code})")
                    up_count += 1
            except requests.exceptions.ConnectError:
                print(f"✗ {module:20s} DOWN (Connection refused)")
                down_count += 1
            except requests.exceptions.Timeout:
                print(f"✗ {module:20s} TIMEOUT")
                down_count += 1
            except Exception as e:
                print(f"✗ {module:20s} ERROR: {str(e)[:30]}")
                down_count += 1

        print(f"\n  Summary: {up_count} UP, {down_count} DOWN")
        self.print_metrics_snapshot("Health Check")

    def vault_baseline(self, num_requests=50):
        """Test Vault with baseline requests"""
        print(f"\n📈 PHASE 2: VAULT BASELINE TEST ({num_requests} requests)")
        print("-" * 80)

        def vault_request():
            try:
                start = time.time()
                # Request Vault's metrics endpoint
                response = requests.get(f"{self.vault_url}/v1/sys/metrics", timeout=5)
                duration = (time.time() - start) * 1000

                with self.lock:
                    self.results['vault_baseline'].append(duration)
                print(f"✓ Vault request completed in {duration:.2f}ms")
            except Exception as e:
                with self.lock:
                    self.errors['vault_baseline'] += 1
                print(f"✗ Vault request failed: {str(e)[:40]}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(vault_request) for _ in range(num_requests)]
            concurrent.futures.wait(futures)

        if self.results['vault_baseline']:
            avg = statistics.mean(self.results['vault_baseline'])
            print(f"\n  Average latency: {avg:.2f}ms")
            print(f"  Min: {min(self.results['vault_baseline']):.2f}ms")
            print(f"  Max: {max(self.results['vault_baseline']):.2f}ms")
            print(f"  Errors: {self.errors['vault_baseline']}/{num_requests}")

        self.print_metrics_snapshot("After Baseline")

    def distributed_module_load(self, requests_per_module=50):
        """Load test all modules simultaneously"""
        print(f"\n🔥 PHASE 3: DISTRIBUTED MODULE LOAD")
        print(f"   {requests_per_module} requests per module")
        print("-" * 80)

        def module_request(module, url):
            try:
                start = time.time()
                response = requests.get(url, timeout=3)
                duration = (time.time() - start) * 1000

                with self.lock:
                    self.results[f'module_{module}'].append(duration)
            except:
                with self.lock:
                    self.errors[f'module_{module}'] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for module, url in self.module_endpoints.items():
                for _ in range(requests_per_module):
                    executor.submit(module_request, module, url)
            executor.shutdown(wait=True)

        print("\n📊 Module Load Results:")
        for module in self.module_endpoints.keys():
            results = self.results[f'module_{module}']
            errors = self.errors[f'module_{module}']
            if results:
                avg = statistics.mean(results)
                success_rate = (len(results) / (len(results) + errors) * 100) if (len(results) + errors) > 0 else 0
                print(f"  {module:20s}: {len(results)} success | Avg: {avg:.2f}ms | Success rate: {success_rate:.1f}%")
            else:
                print(f"  {module:20s}: 0 success | {errors} errors")

        self.print_metrics_snapshot("After Distributed Load")

    def vault_stress_test(self, duration=15, concurrent_connections=30):
        """Sustained load on Vault"""
        print(f"\n💥 PHASE 4: VAULT STRESS TEST")
        print(f"   Duration: {duration}s | Concurrent: {concurrent_connections}")
        print("-" * 80)

        print("⚡ Generating sustained load on Vault...")
        start_time = time.time()
        request_count = 0

        def vault_stress():
            nonlocal request_count
            try:
                response = requests.get(
                    f"{self.vault_url}/v1/sys/health",
                    timeout=2
                )
                request_count += 1
            except:
                self.errors['vault_stress'] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            while time.time() - start_time < duration:
                for _ in range(concurrent_connections):
                    executor.submit(vault_stress)
                time.sleep(0.5)

        elapsed = time.time() - start_time
        rps = request_count / elapsed if elapsed > 0 else 0

        print(f"\n📊 Vault Stress Results:")
        print(f"  Total requests: {request_count}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Requests/sec: {rps:.2f}")
        print(f"  Errors: {self.errors['vault_stress']}")

        self.print_metrics_snapshot("During Stress Test")

    def prometheus_query_load(self, num_queries=100):
        """Load test Prometheus query endpoint"""
        print(f"\n📊 PHASE 5: PROMETHEUS QUERY LOAD ({num_queries} queries)")
        print("-" * 80)

        queries = [
            "vault_core_unsealed",
            "vault_token_count",
            "vault_cache_hit",
            "vault_runtime_num_goroutines",
            "up",
        ]

        def prometheus_query():
            query = queries[hash(threading.current_thread()) % len(queries)]
            try:
                start = time.time()
                url = f"{self.prometheus_url}/api/v1/query?query={query}"
                response = urllib.request.urlopen(url, timeout=5)
                duration = (time.time() - start) * 1000

                with self.lock:
                    self.results['prometheus'].append(duration)
            except:
                with self.lock:
                    self.errors['prometheus'] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(prometheus_query) for _ in range(num_queries)]
            concurrent.futures.wait(futures)

        if self.results['prometheus']:
            avg = statistics.mean(self.results['prometheus'])
            print(f"  Average query time: {avg:.2f}ms")
            print(f"  Min: {min(self.results['prometheus']):.2f}ms")
            print(f"  Max: {max(self.results['prometheus']):.2f}ms")
            print(f"  Errors: {self.errors['prometheus']}/{num_queries}")

        self.print_metrics_snapshot("After Prometheus Load")

    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("📋 FINAL REPORT - INTEGRATED LOAD TEST")
        print("="*80)

        total_requests = sum(len(v) for v in self.results.values())
        total_errors = sum(self.errors.values())

        print(f"\n📊 Overall Summary:")
        print(f"  Total requests: {total_requests}")
        print(f"  Total errors: {total_errors}")
        print(f"  Success rate: {(total_requests/(total_requests+total_errors)*100) if (total_requests+total_errors) > 0 else 0:.1f}%")

        print("\n📊 Detailed Phase Results:")
        print("-" * 80)

        for phase in ['vault_baseline', 'module_aegis', 'prometheus', 'vault_stress']:
            if self.results[phase]:
                avg = statistics.mean(self.results[phase])
                phase_name = phase.replace('_', ' ').title()
                print(f"{phase_name}: Avg {avg:.2f}ms | Errors: {self.errors[phase]}")

        print("\n" + "-"*80)
        print("✅ Load test complete!")
        print("\n🔍 Monitor in real-time:")
        print("   → Grafana: http://localhost:3011/d/vault-dashboard/vault-secrets-management")
        print("   → Prometheus: http://localhost:9091/graph")
        print("="*80 + "\n")

    def run_full_test(self):
        """Run complete test suite"""
        self.test_module_health()
        time.sleep(2)

        self.vault_baseline(num_requests=50)
        time.sleep(2)

        self.distributed_module_load(requests_per_module=30)
        time.sleep(2)

        self.vault_stress_test(duration=15, concurrent_connections=30)
        time.sleep(2)

        self.prometheus_query_load(num_queries=100)

        self.generate_report()


if __name__ == "__main__":
    suite = IntegratedLoadTest()
    suite.run_full_test()
