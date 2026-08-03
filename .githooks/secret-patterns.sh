#!/usr/bin/env bash
# Gemeinsame Musterquelle für Hook, lokale Validierung, CI und Release.
# Diese Datei wird gesourct und nicht direkt ausgeführt.

SECRET_MUSTER=(
  "JWT / HA-Token|eyJ[A-Za-z0-9_-]{20,}"
  "Telegram-Bot-Token|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}"
  "GitHub-Token|gh[pousr]_[A-Za-z0-9]{36,}"
  "GitHub-PAT|github_pat_[A-Za-z0-9_]{22,}"
  "GitLab-Token|glpat-[A-Za-z0-9_-]{20,}"
  "AWS-Access-Key|AKIA[0-9A-Z]{16}"
  "Google-API-Key|AIza[0-9A-Za-z_-]{30,}"
  "API-Key mit sk-Praefix|sk[-_][A-Za-z0-9_-]{20,}"
  "Anthropic-Key|sk-ant-[A-Za-z0-9_-]{20,}"
  "Slack-Token|xox[baprs]-[A-Za-z0-9-]{10,}"
  "Privater Schluessel|-----BEGIN [A-Z ]*PRIVATE KEY"
  "Private IPv4-Adresse|(^|[^0-9.])(192\.168|10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]{1,3}\.[0-9]{1,3}"
  "Telegram-Chat-ID|-[0-9]{9,13}"
  "Credential-Zuweisung|(password|passwd|credential|api[_-]?key|secret|token|auth)[\"']?[[:space:]]*[:=][[:space:]]*[\"']?[^[:space:]\"'<#][^[:space:]\"']{7,}"
)

# Ausschließlich exakte, nicht geheime Musterwerte zulassen.
PLATZHALTER=(
  "-000000000"
  "-0000000000"
)

scanne_strom() {
  local label="$1" inhalt eintrag name regex roh rc treffer t fund=0
  inhalt=$(cat || true)
  for eintrag in "${SECRET_MUSTER[@]}"; do
    name="${eintrag%%|*}"
    regex="${eintrag#*|}"
    if roh=$(grep -aoiE -e "$regex" <<<"$inhalt"); then rc=0; else rc=$?; fi
    if [ "$rc" -ge 2 ]; then
      echo "INTERNER FEHLER: ungültiges Scan-Muster '$name' (grep rc=$rc)." >&2
      return 2
    fi
    [ "$rc" -ne 0 ] && continue
    treffer=$(printf '%s\n' "$roh" \
      | grep -vxF -f <(printf '%s\n' "${PLATZHALTER[@]}") -- \
      | sed '/^[[:space:]]*$/d' | sort -u | head -5 || true)
    [ -z "$treffer" ] && continue
    fund=1
    while IFS= read -r t; do
      [ -z "$t" ] && continue
      printf '  %s: %s -> %.8s… (redacted)\n' "$name" "$label" "$t"
    done <<<"$treffer"
  done
  return "$fund"
}

ist_textdatei() {
  local datei="$1"
  [ ! -s "$datei" ] && return 0
  LC_ALL=C grep -Iq . "$datei"
}

scanne_datei() {
  local label="$1" datei="$2"
  if ! ist_textdatei "$datei"; then
    echo "  Binärdatei nicht erlaubt: $label"
    return 1
  fi
  scanne_strom "$label" < "$datei"
}
