#!/bin/bash
# ============================================================
#  nas_scan.sh - Synology NAS DS925+
#  Scans the current directory and creates two output files:
#    folders.txt  - list of all folders (relative path)
#    files.txt    - list of all files (relative path)
#
#  Usage:
#    cd /volume1/my-data         # move to the folder you want to scan from
#    bash nas_scan.sh            # run the script
#
#  Output files are saved to the directory where you run the script.
# ============================================================

# Scan root directory = current working directory
BASE_DIR="$(pwd)"

# Output files
FOLDERS_OUT="${BASE_DIR}/folders.txt"
FILES_OUT="${BASE_DIR}/files.txt"

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

echo "================================================" | tee /dev/stderr
echo "  NAS Scan - ${TIMESTAMP}"                        | tee /dev/stderr
echo "  Scan root: ${BASE_DIR}"                         | tee /dev/stderr
echo "================================================" | tee /dev/stderr

# ---------- FOLDERS.TXT ----------
{
  echo "# =============================================="
  echo "# FOLDER LIST"
  echo "# Generated: ${TIMESTAMP}"
  echo "# Root:      ${BASE_DIR}"
  echo "# =============================================="
  echo ""
  find . -mindepth 1 -type d \
    -not \( -name '@*' -prune \) | sort | sed 's|^\./||'
  echo ""
  echo "# Total folders: $(find . -mindepth 1 -type d -not \( -name '@*' -prune \) | wc -l)"
} > "${FOLDERS_OUT}"

echo "Folders saved to: ${FOLDERS_OUT}" | tee /dev/stderr

# ---------- FILES.TXT ----------
{
  echo "# =============================================="
  echo "# FILE LIST"
  echo "# Generated: ${TIMESTAMP}"
  echo "# Root:      ${BASE_DIR}"
  echo "# =============================================="
  echo ""
  find . -type f \
    -not \( -path '*/@*' -prune \) | sort | sed 's|^\./||'
  echo ""
  echo "# Total files: $(find . -type f -not \( -path '*/@*' -prune \) | wc -l)"
} > "${FILES_OUT}"

echo "Files saved to: ${FILES_OUT}" | tee /dev/stderr
echo ""
echo "Done!" | tee /dev/stderr
