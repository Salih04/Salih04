#!/usr/bin/env bash
# Terminal "whoami" typing animation for the profile README panel.
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
RESET='\033[0m'

type_out() {
  local text="$1"
  local delay="${2:-0.03}"
  for ((i = 0; i < ${#text}; i++)); do
    printf '%s' "${text:$i:1}"
    sleep "$delay"
  done
  printf '\n'
}

print_line() {
  sleep "${2:-0.4}"
  printf '%b\n' "$1"
}

clear
printf '%b' "${GREEN}guest@basel${RESET}:${CYAN}~${RESET}\$ "
type_out "whoami" 0.09
sleep 0.5

print_line "" 0.2
print_line "${BOLD}${YELLOW}Salih Camci${RESET}" 0.3
print_line "Data Science · Machine Learning · Backend Engineering" 0.15
print_line "" 0.2
print_line "${CYAN}role${RESET}       Backend Engineering Intern @ Crytek GmbH (Go, Redis, REST)" 0.25
print_line "${CYAN}next${RESET}       MSc Data Science, University of Basel — Sep 2026" 0.25
print_line "${CYAN}based${RESET}      Istanbul -> Basel, Switzerland" 0.25
print_line "${CYAN}stack${RESET}      Python · Go · SQL · PyTorch · FastAPI · Docker" 0.25
print_line "${CYAN}github${RESET}     github.com/Salih04" 0.25
print_line "${CYAN}email${RESET}      salihcamci04@gmail.com" 0.25
print_line "" 0.2

sleep 0.5
printf '%b' "${GREEN}guest@basel${RESET}:${CYAN}~${RESET}\$ "
sleep 2
