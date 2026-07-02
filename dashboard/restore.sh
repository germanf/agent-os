#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup-file>"
    echo "Restore dashboard/data/chat.db from a backup file."
    exit 1
fi

BACKUP="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB="$SCRIPT_DIR/data/chat.db"

if [ ! -f "$BACKUP" ]; then
    echo "Error: backup file not found: $BACKUP"
    exit 1
fi

echo "Verifying backup integrity..."
python3 -c "
import sqlite3
con = sqlite3.connect('$BACKUP')
cursor = con.execute('PRAGMA integrity_check')
result = cursor.fetchone()[0]
con.close()
if result != 'ok':
    print('FAIL: backup is corrupt')
    exit(1)
print('OK: backup integrity check passed')
" || exit 1

echo "Backing up current DB to ${DB}.prev..."
[ -f "$DB" ] && cp "$DB" "${DB}.prev"

echo "Restoring from $BACKUP..."
python3 -c "
import sqlite3, os
db_path = '$DB'
backup_path = '$BACKUP'
bck = sqlite3.connect(backup_path)
dst = sqlite3.connect(db_path)
bck.backup(dst)
dst.close()
bck.close()
print('Restore complete: {}'.format(os.path.getsize(db_path)))
"

echo "Done."
