#!/usr/bin/env bash
# Aoba campaign — autonomous daily check.
# Runs via launchd at ~09:57 Lisbon, until launchctl unload kills it.
# Probes site/form health, attempts a post if IG account is flagged active.
set -uo pipefail
REPO="${HOME}/Desktop/workspace/aoba"
cd "$REPO" || exit 1

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
LOG="$REPO/data/daily_log.csv"
REPORT="$REPO/data/daily_report-${DATE}.md"
IG_FLAG="$REPO/data/.ig_active"
mkdir -p "$(dirname "$LOG")"

if [ ! -f "$LOG" ]; then
  echo "date,time,site_status,form_status,ig_live,post_attempted,post_result,notes" > "$LOG"
fi

SITE=$(curl -sI -o /dev/null -w "%{http_code}" "https://www.cochoy.fr/aoba/" || echo "000")
SHOP=$(curl -sI -o /dev/null -w "%{http_code}" "https://www.cochoy.fr/aoba/shop.html" || echo "000")
FORM=$(curl -sI -o /dev/null -w "%{http_code}" "https://formsubmit.co/07ecd00f53dd1c98a5a12493fbe01c0a" || echo "000")

IG_LIVE="not_yet"
POST_ATTEMPTED="no"
POST_RESULT="-"
NOTES="-"

if [ -f "$IG_FLAG" ]; then
  IG_LIVE="active"
  POST_ATTEMPTED="yes"
  if [ -x "$REPO/scripts/post_today.py" ]; then
    set +e
    "$REPO/scripts/post_today.py" >> "$REPO/logs/posting.log" 2>&1
    rc=$?
    set -e
    if [ $rc -eq 0 ]; then POST_RESULT="ok"; else POST_RESULT="failed_rc=${rc}"; fi
  else
    POST_RESULT="script_missing"
  fi
else
  NOTES="IG account not flagged active — touch ${IG_FLAG} to enable posting"
fi

echo "${DATE},${TIME},${SITE}/${SHOP},${FORM},${IG_LIVE},${POST_ATTEMPTED},${POST_RESULT},${NOTES}" >> "$LOG"

{
  echo "# Aoba — autonomous daily report"
  echo ""
  echo "Generated: ${DATE} ${TIME}"
  echo ""
  echo "## Site & form health"
  echo ""
  echo "| Check                      | Status |"
  echo "|----------------------------|--------|"
  echo "| Landing (index.html)       | HTTP ${SITE} |"
  echo "| Shop (shop.html)           | HTTP ${SHOP} |"
  echo "| Formsubmit endpoint        | HTTP ${FORM} |"
  echo "| Instagram @aoba.spread     | ${IG_LIVE} |"
  echo "| Posting attempted today    | ${POST_ATTEMPTED} (${POST_RESULT}) |"
  echo ""
  echo "## Notes"
  echo ""
  echo "- ${NOTES}"
  echo ""
  echo "## Recent activity"
  echo ""
  echo '```'
  tail -8 "$LOG"
  echo '```'
} > "$REPORT"

echo "Wrote $REPORT"
