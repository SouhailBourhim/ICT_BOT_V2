#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
export LANG=C

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/ict-bot-v2-$TIMESTAMP.tar.gz"
CHECKSUM="$ARCHIVE.sha256"

mkdir -p "$BACKUP_DIR"

cd "$ROOT_DIR"

tar -czf "$ARCHIVE" \
  --exclude="data/conversations/.gitkeep" \
  database \
  data/documents \
  data/conversations \
  data/processed

shasum -a 256 "$ARCHIVE" > "$CHECKSUM"

find "$BACKUP_DIR" -type f \( -name "ict-bot-v2-*.tar.gz" -o -name "ict-bot-v2-*.tar.gz.sha256" \) \
  -mtime "+$RETENTION_DAYS" -delete

echo "Backup written: $ARCHIVE"
echo "Checksum written: $CHECKSUM"
