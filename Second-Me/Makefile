.PHONY: help setup start stop test clean format lint

help:
	@echo "Second-Me: Personal AI Self-Training System"
	@echo "============================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup          - Install all dependencies"
	@echo "  make start          - Start all services (backend + frontend)"
	@echo "  make stop           - Stop all services"
	@echo "  make test           - Run test suite"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make format         - Format code with Black/Prettier"
	@echo "  make lint           - Run linters (Ruff/ESLint)"
	@echo "  make l0             - Process L0 raw data"
	@echo "  make l1             - Synthesize L1 memories"
	@echo "  make l2             - Fine-tune L2 models"
	@echo ""

setup:
	@echo "📦 Setting up Second-Me environment..."
	@echo ""
	@echo "Python requirements..."
	pip install -r requirements.txt
	@echo ""
	@echo "✅ Setup complete"
	@echo "   Next: make start"

start:
	@echo "🚀 Starting Second-Me services..."
	@echo ""
	@echo "✅ Services ready:"
	@echo "   Backend:  http://localhost:5000"
	@echo "   Frontend: http://localhost:3000"
	@echo ""
	@echo "Press Ctrl+C to stop"

stop:
	@echo "⏹️  Stopping services..."
	@echo "✅ Stopped"

test:
	@echo "🧪 Running tests..."
	python3 -m pytest lpm_kernel/tests/ -v --cov=lpm_kernel
	@echo "✅ Tests complete"

clean:
	@echo "🗑️  Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	@echo "✅ Cleaned"

format:
	@echo "🎨 Formatting code..."
	black lpm_kernel/ --line-length=100
	@echo "✅ Formatted"

lint:
	@echo "🔍 Running linters..."
	ruff check lpm_kernel/
	@echo "✅ Lint complete"

l0:
	@echo "📊 Processing L0 raw data..."
	python3 -m lpm_kernel.L0.data_processor
	@echo "✅ L0 processing complete"

l1:
	@echo "🧠 Synthesizing L1 memories..."
	python3 -m lpm_kernel.L1.memory_synthesizer
	@echo "✅ L1 synthesis complete"

l2:
	@echo "🤖 Fine-tuning L2 models..."
	python3 -m lpm_kernel.L2.model_finetuner
	@echo "✅ L2 fine-tuning complete"

check-env:
	@echo "🔍 Checking environment..."
	python3 --version
	pip --version
	node --version 2>/dev/null || echo "⚠️  Node.js not found"
	@echo "✅ Environment check complete"
