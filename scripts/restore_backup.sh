#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
export LANG=C

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/ict-bot-v2-backup.tar.gz" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="$1"
CHECKSUM="$ARCHIVE.sha256"

if [ ! -f "$ARCHIVE" ]; then
  echo "Backup archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ -f "$CHECKSUM" ]; then
  shasum -a 256 -c "$CHECKSUM"
fi

cd "$ROOT_DIR"
mkdir -p database data/documents data/conversations data/processed
tar -xzf "$ARCHIVE"

echo "Backup restored into: $ROOT_DIR"
