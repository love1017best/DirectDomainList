#!/usr/bin/env bash
# Repo checks shared by CI and local use (agents: run before every push).
#   bash check.sh
# 1. no duplicate rules (global, across all category groups)
# 2. every non-empty / non-comment line starts with a known rule keyword
# 3. DirectDomain.yaml parses (if PyYAML is installed) and is in sync with DirectDomain.list
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"

LIST=DirectDomain.list
YAML=DirectDomain.yaml
fail=0

err() {
  if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::error::$1"; else echo "ERROR: $1"; fi
  fail=1
}

# NOTE: `uniq -d` / `grep -v` exit nonzero in the healthy case, so never `set -e` here.

# 1. duplicates (key = rule type + value up to first space, so a trailing `// comment` is ignored)
dups=$(grep -oE "^DOMAIN[^,]+,[^ ]+" "$LIST" | sort | uniq -d || true)
if [ -n "$dups" ]; then
  err "Duplicate rules found:"; echo "$dups"
else
  echo "OK: no duplicate rules"
fi

# 2. format
bad=$(grep -vE '^(#|$|DOMAIN-SUFFIX|DOMAIN-KEYWORD|DOMAIN,|USER-AGENT|IP-CIDR|IP-CIDR6|GEOIP|DST-PORT|PROCESS-NAME|RULE-SET|AND,|OR,)' "$LIST" || true)
if [ -n "$bad" ]; then
  err "Lines with unknown/unsupported rule format:"; echo "$bad"
else
  echo "OK: rule formats valid"
fi

# 3. yaml valid + in sync
tmp=$(mktemp "${TMPDIR:-/tmp}/ddl-check.XXXXXX")
trap 'rm -f "$tmp"' EXIT
if ! python3 convert_list_to_yaml.py "$LIST" "$tmp" >/dev/null; then
  err "convert_list_to_yaml.py failed"
elif ! cmp -s "$YAML" "$tmp"; then
  err "$YAML is out of sync with $LIST. Run: python3 convert_list_to_yaml.py $LIST $YAML"
else
  echo "OK: $YAML is in sync with $LIST"
fi

if python3 -c "import yaml" 2>/dev/null; then
  if python3 - "$YAML" <<'EOF'
import sys, yaml
d = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))
sys.exit(0 if isinstance(d, dict) and isinstance(d.get('payload'), list) else 1)
EOF
  then echo "OK: $YAML parses, payload is a list"
  else err "$YAML is not valid (payload must be a list)"; fi
else
  echo "SKIP: PyYAML not installed, YAML parse check skipped (CI runs it)"
fi

exit $fail
