import os

# Set before any app module is imported
os.environ.setdefault("JWT_SECRET", "test-secret-mini-adam")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")
os.environ.setdefault("RUNNER_URL", "http://runner-mock:4001")
os.environ.setdefault("SHORT_TASK_THRESHOLD_S", "5")
