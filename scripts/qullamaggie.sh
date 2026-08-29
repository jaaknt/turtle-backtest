#!/usr/bin/env bash
#
# Run the Qullamaggie research studies in the pipeline order of docs/research/prompts.md.
#
#   ./scripts/qullamaggie.sh              # everything (hours — see "Runtime" below)
#   ./scripts/qullamaggie.sh cohorts      # only studies whose label contains "cohorts"
#   ./scripts/qullamaggie.sh backtest portfolio
#   ./scripts/qullamaggie.sh -l           # list the labels without running anything
#   ./scripts/qullamaggie.sh -n cohorts   # dry run: print the commands that would run
#
# Parameters come from docs/research/prompts.md and docs/research/qullamaggie-backtest-v4.md.
# Only backtest-v4 and portfolio-sim take arguments — both are run once per evaluation window
# (2010-2015, 2016-2020, 2021-2025/2026) with the output path that window's result doc. Every
# other study hardcodes its own period, so it is invoked bare; changing one of those periods
# means editing that script, not this one.
#
# Memory: every study runs inside its own cgroup scope capped at MEM_MAX with swap disabled.
# On WSL every user process shares one unbounded /init.scope and systemd-oomd is not installed,
# so an uncapped runaway kills the terminal and can wedge the whole VM rather than just failing.
# MemorySwapMax=0 is the important half — it prevents the swap-thrash that makes the OOM kill
# unreapable. A study that dies at exit 137 was OOM-killed: raise MEM_MAX or narrow its input,
# do not just re-run it. Studies run strictly one at a time for the same reason.
#
# Runtime: roughly 1-2 hours for the full set on a warm database. Each study reloads the
# universe from Postgres, so there is no shared cache between them.
#
# Failures do not stop the run — every study is attempted and the summary at the end lists what
# failed, so an overnight run is not lost to one broken study. Exit status is non-zero if any
# study failed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

MEM_MAX="${MEM_MAX:-4G}"
LOG_DIR="${LOG_DIR:-/tmp/qullamaggie-runs/$(date +%Y%m%d-%H%M%S)}"

RESULT_DIR="docs/research"

# label|script and arguments. The label is what the positional filters match on.
STUDIES=(
  # ── Backtest foundation ──
  "backtest-v4-2010-2015|qullamaggie-backtest-v4.py --start-date 2010-01-01 --end-date 2015-12-31 --output $RESULT_DIR/result-qullamaggie-backtest-v4-2010-2015.md"
  "backtest-v4-2016-2020|qullamaggie-backtest-v4.py --start-date 2016-01-01 --end-date 2020-12-31 --output $RESULT_DIR/result-qullamaggie-backtest-v4-2016-2020.md"
  "backtest-v4-2021-2025|qullamaggie-backtest-v4.py --start-date 2021-01-01 --end-date 2025-12-31 --output $RESULT_DIR/result-qullamaggie-backtest-v4.md"
  "longterm-monthly|qullamaggie-longterm-monthly.py"
  "horizon-monthly|qullamaggie-horizon-monthly.py"
  # ── Filter cohort studies ──
  "cohorts-roc|qullamaggie-cohorts-roc.py"
  "cohorts-adr|qullamaggie-cohorts-adr.py"
  "cohorts-adr-compression|qullamaggie-cohorts-adr-compression.py"
  "cohorts-rsi|qullamaggie-cohorts-rsi.py"
  "cohorts-price|qullamaggie-cohorts-price.py"
  "cohorts-vol-surge|qullamaggie-cohorts-vol-surge.py"
  "cohorts-vol-dry-up|qullamaggie-cohorts-vol-dry-up.py"
  "cohorts-tightrange|qullamaggie-cohorts-tightrange.py"
  "cohorts-pct-above-sma50|qullamaggie-cohorts-pct-above-sma50.py"
  "cohorts-sma200|qullamaggie-cohorts-sma200.py"
  "cohorts-spy-sma|qullamaggie-cohorts-spy-sma.py"
  "cohorts-sector|qullamaggie-cohorts-sector.py"
  "cohorts-market-cap|qullamaggie-cohorts-market-cap.py"
  "cohorts-avg-vol|qullamaggie-cohorts-avg-vol.py"
  "cohorts-ranking|qullamaggie-cohorts-ranking.py"
  # ── Entry timing / limit orders ──
  "cohorts-limit-order|qullamaggie-cohorts-limit-order.py"
  "limit-fill-rate|qullamaggie-limit-fill-rate.py"
  # ── Filter relaxation ──
  "relax-sweep|qullamaggie-relax-sweep.py"
  # ── Ranking ──
  "ranking-validation|qullamaggie-ranking-validation.py"
  "ranking-weights|qullamaggie-ranking-weights.py"
  # ── Portfolio simulation ──
  "portfolio-sim-2010-2015|qullamaggie-portfolio-sim.py --start-date 2010-01-01 --end-date 2015-12-31 --output $RESULT_DIR/result-qullamaggie-portfolio-v4-2010-2015.md"
  "portfolio-sim-2016-2020|qullamaggie-portfolio-sim.py --start-date 2016-01-01 --end-date 2020-12-31 --output $RESULT_DIR/result-qullamaggie-portfolio-v4-2016-2020.md"
  "portfolio-sim-2021-2026|qullamaggie-portfolio-sim.py --start-date 2021-01-01 --end-date 2026-06-26 --output $RESULT_DIR/result-qullamaggie-portfolio-v4.md"
  "exit-sweep|qullamaggie-exit-sweep.py"
  # ── Live signal generation (screen reports, meaningful only on the day they run) ──
  "signals-v4|qullamaggie-signals-v4.py"
  "trades-v4|qullamaggie-trades-v4.py"
)

# Result docs carrying a hand-written `## Findings` section that their own script does not
# regenerate. The script opens the file with "w", so a re-run silently drops everything from
# that heading down. Each is saved before the run and re-appended after.
FINDINGS_DOCS=(
  "$RESULT_DIR/result-qullamaggie-portfolio-v4.md"
  "$RESULT_DIR/result-qullamaggie-portfolio-v4-2010-2015.md"
  "$RESULT_DIR/result-qullamaggie-portfolio-v4-2016-2020.md"
)

usage() {
  sed -n '3,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

list_studies() {
  printf '%s\n' "${STUDIES[@]}" | cut -d'|' -f1
}

# Stash the `## Findings` tail of every doc that has one, into $LOG_DIR/findings/.
save_findings() {
  mkdir -p "$LOG_DIR/findings"
  local doc
  for doc in "${FINDINGS_DOCS[@]}"; do
    [[ -f $doc ]] || continue
    grep -q '^## Findings' "$doc" || continue
    sed -n '/^## Findings/,$p' "$doc" >"$LOG_DIR/findings/$(basename "$doc")"
  done
}

# Put each stashed tail back, but only if the regenerated doc really lost it — so a script that
# learns to emit its own Findings section later does not end up with two.
restore_findings() {
  local doc saved
  for doc in "${FINDINGS_DOCS[@]}"; do
    saved="$LOG_DIR/findings/$(basename "$doc")"
    [[ -f $saved && -f $doc ]] || continue
    if ! grep -q '^## Findings' "$doc"; then
      # `$(<file)` strips trailing newlines from both sides, so the separator below is exactly
      # one blank line — two in a row would fail markdownlint MD012.
      printf '%s\n\n%s\n' "$(<"$doc")" "$(<"$saved")" >"$doc.tmp" && mv "$doc.tmp" "$doc"
      echo "  restored ## Findings in $doc"
    fi
  done
}

DRY_RUN=0
while getopts ":lnh" opt; do
  case $opt in
    l) list_studies; exit 0 ;;
    n) DRY_RUN=1 ;;
    h) usage 0 ;;
    *) echo "unknown option -$OPTARG" >&2; usage 1 ;;
  esac
done
shift $((OPTIND - 1))

if ! command -v systemd-run >/dev/null 2>&1; then
  echo "systemd-run not found — refusing to run uncapped." >&2
  echo "These studies load millions of rows; an uncapped OOM takes down the whole WSL distro," >&2
  echo "not just the script. See CLAUDE.md, 'Running Research Studies'." >&2
  exit 1
fi

# Keep the declared order; a study is selected if its label contains any of the filters.
selected=()
for entry in "${STUDIES[@]}"; do
  label=${entry%%|*}
  if [[ $# -eq 0 ]]; then
    selected+=("$entry")
    continue
  fi
  for filter in "$@"; do
    if [[ $label == *"$filter"* ]]; then
      selected+=("$entry")
      break
    fi
  done
done

if [[ ${#selected[@]} -eq 0 ]]; then
  echo "No studies match: $*" >&2
  echo "Available labels:" >&2
  list_studies >&2
  exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  for entry in "${selected[@]}"; do
    read -ra argv <<<"${entry#*|}"
    echo "systemd-run --user --scope -q -p MemoryMax=$MEM_MAX -p MemorySwapMax=0 uv run scripts/${argv[*]}"
  done
  exit 0
fi

mkdir -p "$LOG_DIR"
save_findings

echo "Qullamaggie research run — ${#selected[@]} studies, MemoryMax=$MEM_MAX"
echo "Logs: $LOG_DIR"
echo

failed=()
oomed=()
started_at=$SECONDS

for entry in "${selected[@]}"; do
  label=${entry%%|*}
  read -ra argv <<<"${entry#*|}"
  echo "──────────────────────────────────────────────────────────────────────"
  echo "▶ $label"
  step_started=$SECONDS

  systemd-run --user --scope -q -p MemoryMax="$MEM_MAX" -p MemorySwapMax=0 \
    uv run "scripts/${argv[0]}" "${argv[@]:1}" 2>&1 | tee "$LOG_DIR/$label.log"
  status=${PIPESTATUS[0]}

  elapsed=$((SECONDS - step_started))
  if [[ $status -eq 0 ]]; then
    printf '✔ %s (%dm%02ds)\n\n' "$label" $((elapsed / 60)) $((elapsed % 60))
  elif [[ $status -eq 137 ]]; then
    oomed+=("$label")
    printf '✘ %s — OOM-killed at MemoryMax=%s (%dm%02ds)\n\n' "$label" "$MEM_MAX" $((elapsed / 60)) $((elapsed % 60))
  else
    failed+=("$label")
    printf '✘ %s — exit %d (%dm%02ds)\n\n' "$label" "$status" $((elapsed / 60)) $((elapsed % 60))
  fi
done

restore_findings

total=$((SECONDS - started_at))
echo "──────────────────────────────────────────────────────────────────────"
printf 'Done in %dh%02dm. %d ok, %d failed, %d OOM.\n' \
  $((total / 3600)) $(((total % 3600) / 60)) \
  $((${#selected[@]} - ${#failed[@]} - ${#oomed[@]})) "${#failed[@]}" "${#oomed[@]}"
[[ ${#failed[@]} -gt 0 ]] && printf 'failed: %s\n' "${failed[*]}"
if [[ ${#oomed[@]} -gt 0 ]]; then
  printf 'OOM:    %s\n' "${oomed[*]}"
  echo "Raise MEM_MAX or narrow the study's input — re-running unchanged will OOM again."
fi
echo "Logs: $LOG_DIR"

[[ ${#failed[@]} -eq 0 && ${#oomed[@]} -eq 0 ]]
