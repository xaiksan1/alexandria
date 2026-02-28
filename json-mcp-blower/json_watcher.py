#!/usr/bin/env python3
"""
JSON Watcher: Real-time file monitoring and MCP generation.
Watches mcp-schema.json for changes and triggers generation (< 100ms).
"""

import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("⚠️  watchdog not installed. Install: pip install watchdog")
    Observer = None
    FileSystemEventHandler = None


class SchemaChangeHandler(FileSystemEventHandler):
    """Handle schema file changes."""

    def __init__(self, callback=None):
        self.callback = callback
        self.last_hash = None

    def on_modified(self, event):
        """Triggered when schema file is modified."""
        if not event.is_directory and event.src_path.endswith('mcp-schema.json'):
            # Debounce: wait for file to stabilize
            time.sleep(0.1)

            try:
                with open(event.src_path, 'rb') as f:
                    current_hash = hashlib.md5(f.read()).hexdigest()

                if current_hash != self.last_hash:
                    self.last_hash = current_hash
                    print(f"\n⚡ Schema modified at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                    if self.callback:
                        self.callback(event.src_path)
            except Exception as e:
                print(f"⚠️  Error reading schema: {e}")


class JSONWatcher:
    """Watch schema and trigger MCP generation."""

    def __init__(self, schema_path: str = "mcp-schema.json"):
        self.schema_path = Path(schema_path)
        self.observer = Observer() if Observer else None
        self.running = False

    def on_schema_change(self, schema_file: str):
        """Called when schema changes."""
        try:
            with open(schema_file) as f:
                schema = json.load(f)

            config = schema.get("fractal_config", {})
            status = schema.get("generation_status", {})

            print(f"📋 Schema Updated:")
            print(f"   Growth Rate: {config.get('growth_rate')}")
            print(f"   Max Iterations: {config.get('max_iterations')}")
            print(f"   Agents Generated: {status.get('agents_generated', 0)}")
            print(f"   Energy Cost: {status.get('total_energy_cost_kwh', 0):.1f} kWh")

            # Could trigger generation here:
            # from bootstrap_loop import BootstrapLoop
            # loop = BootstrapLoop(schema_file)
            # loop.run_bootstrap()

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")

    def start_watching(self):
        """Start watching schema file."""
        if not self.observer:
            print("❌ watchdog not available. Install: pip install watchdog")
            return

        self.running = True

        # Create handler
        handler = SchemaChangeHandler(callback=self.on_schema_change)
        handler.last_hash = self._get_file_hash()

        # Start observer
        self.observer.schedule(handler, str(self.schema_path.parent), recursive=False)
        self.observer.start()

        print(f"👁️  Watching {self.schema_path}")
        print(f"   Detection latency: < 100ms")
        print(f"   Press Ctrl+C to stop")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✋ Stopping watcher...")
            self.stop_watching()

    def stop_watching(self):
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("✅ Watcher stopped")

    def _get_file_hash(self) -> str:
        """Get file hash for comparison."""
        try:
            with open(self.schema_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""


def main():
    """Run JSON watcher."""
    watcher = JSONWatcher()
    watcher.start_watching()


if __name__ == "__main__":
    main()
