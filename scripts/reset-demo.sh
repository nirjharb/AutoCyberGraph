#!/usr/bin/env bash
# Reset the local database and load the demo dataset from scratch.
set -euo pipefail
cd "$(dirname "$0")/../backend"
rm -f autocybergraph.db
bash ../scripts/seed.sh
echo "Demo database reset complete."
