#!/usr/bin/env bash
# Start local development environment using Docker Compose.
# Usage: ./scripts/local_dev.sh [up|down|logs]

set -euo pipefail

CMD="${1:-up}"

case "$CMD" in
  up)
    echo "Starting MemVault local dev environment..."
    cp -n .env.example .env 2>/dev/null || true
    docker compose up --build -d
    echo ""
    echo "Services:"
    echo "  Upload Service   → http://localhost:8001/docs"
    echo "  Delivery Service → http://localhost:8002/docs"
    echo "  Auth Service     → http://localhost:8003/docs"
    echo "  Studio Portal    → http://localhost:3000"
    echo "  Firestore UI     → http://localhost:4000 (if firebase emulators running)"
    ;;
  down)
    docker compose down -v
    ;;
  logs)
    docker compose logs -f
    ;;
  *)
    echo "Usage: $0 [up|down|logs]"
    exit 1
    ;;
esac
