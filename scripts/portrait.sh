#!/usr/bin/env bash
# Reveals outputs/portrait_ascii.txt line by line for the portrait panel.
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
DIM='\033[2;37m'
RESET='\033[0m'

ASCII_FILE="${1:-outputs/portrait_ascii.txt}"

clear
printf '%b' "${GREEN}guest@basel${RESET}:${CYAN}~${RESET}\$ "
sleep 0.3
printf 'cat portrait.txt\n'
sleep 0.4

printf '%b' "${DIM}"
while IFS= read -r line; do
  printf '%s\n' "$line"
  sleep 0.05
done < "$ASCII_FILE"
printf '%b' "${RESET}"

sleep 0.5
printf '%b' "${GREEN}guest@basel${RESET}:${CYAN}~${RESET}\$ "
sleep 2
