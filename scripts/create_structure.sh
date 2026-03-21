#!/bin/bash
# ============================================================
#  create_structure.sh - Ubuntu 24.04
#  Reads folders.txt and files.txt and creates a directory
#  structure + empty files in the script execution location.
#
#  Usage:
#    cd /path/where/you/want/to/create/structure
#    bash /path/to/create_structure.sh
#
#  Expected input files (in the same folder as the script):
#    folders.txt - one line = one relative folder path
#    files.txt   - one line = one relative file path
# ============================================================

TARGET_DIR="$(pwd)"

FOLDERS_FILE="${TARGET_DIR}/folders.txt"
FILES_FILE="${TARGET_DIR}/files.txt"

# Counters
FOLDERS_CREATED=0
FOLDERS_SKIPPED=0
FILES_CREATED=0
FILES_SKIPPED=0
ERRORS=0

# -- Output colors ------------------------------------------------
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
CYAN="\e[36m"
RESET="\e[0m"

echo -e "${CYAN}================================================${RESET}"
echo -e "${CYAN}  create_structure.sh - $(date '+%Y-%m-%d %H:%M:%S')${RESET}"
echo -e "${CYAN}  Input files: ${TARGET_DIR}${RESET}"
echo -e "${CYAN}  Target:      ${TARGET_DIR}${RESET}"
echo -e "${CYAN}================================================${RESET}"
echo ""

# -- Input file checks -------------------------------------------
if [[ ! -f "${FOLDERS_FILE}" ]]; then
  echo -e "${RED}File folders.txt not found: ${FOLDERS_FILE}${RESET}"
  exit 1
fi

if [[ ! -f "${FILES_FILE}" ]]; then
  echo -e "${RED}File files.txt not found: ${FILES_FILE}${RESET}"
  exit 1
fi

# -- STEP 1: Create folders --------------------------------------
echo -e "${CYAN}[ 1/2 ] Creating folders...${RESET}"

while IFS= read -r line || [[ -n "${line}" ]]; do
  # Skip empty lines and comments (#)
  [[ -z "${line}" || "${line}" == \#* ]] && continue

  TARGET="${TARGET_DIR}/${line}"

  if [[ -d "${TARGET}" ]]; then
    echo -e "  ${YELLOW}Already exists:${RESET} ${line}"
    (( FOLDERS_SKIPPED++ ))
  else
    if mkdir -p "${TARGET}" 2>/dev/null; then
      echo -e "  ${GREEN}Created:${RESET}       ${line}"
      (( FOLDERS_CREATED++ ))
    else
      echo -e "  ${RED}Error:${RESET}         ${line}"
      (( ERRORS++ ))
    fi
  fi

done < "${FOLDERS_FILE}"

echo ""

# -- STEP 2: Create files ----------------------------------------
echo -e "${CYAN}[ 2/2 ] Creating files...${RESET}"

while IFS= read -r line || [[ -n "${line}" ]]; do
  # Skip empty lines and comments (#)
  [[ -z "${line}" || "${line}" == \#* ]] && continue

  TARGET="${TARGET_DIR}/${line}"
  PARENT_DIR="$(dirname "${TARGET}")"

  # Create parent directory if it does not exist
  if [[ ! -d "${PARENT_DIR}" ]]; then
    mkdir -p "${PARENT_DIR}" 2>/dev/null
  fi

  if [[ -f "${TARGET}" ]]; then
    echo -e "  ${YELLOW}Already exists:${RESET} ${line}"
    (( FILES_SKIPPED++ ))
  else
    if touch "${TARGET}" 2>/dev/null; then
      echo -e "  ${GREEN}Created:${RESET}       ${line}"
      (( FILES_CREATED++ ))
    else
      echo -e "  ${RED}Error:${RESET}         ${line}"
      (( ERRORS++ ))
    fi
  fi

done < "${FILES_FILE}"

# -- Final summary ------------------------------------------------
echo ""
echo -e "${CYAN}================================================${RESET}"
echo -e "${CYAN}  Summary${RESET}"
echo -e "${CYAN}================================================${RESET}"
echo -e "  Folders - created: ${GREEN}${FOLDERS_CREATED}${RESET}  |  skipped: ${YELLOW}${FOLDERS_SKIPPED}${RESET}"
echo -e "  Files   - created: ${GREEN}${FILES_CREATED}${RESET}  |  skipped: ${YELLOW}${FILES_SKIPPED}${RESET}"
if (( ERRORS > 0 )); then
  echo -e "  ${RED}Errors: ${ERRORS}${RESET}"
fi
echo -e "${CYAN}================================================${RESET}"
echo ""

if (( ERRORS > 0 )); then
  exit 1
fi
exit 0
