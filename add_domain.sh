#!/usr/bin/env bash
# Add domain(s) to DirectDomain.list, regenerate YAML, check, commit and push to origin/main.
# Deterministic replacement for the manual steps in skills/direct-domain-manager/SKILL.md.
#
#   bash add_domain.sh [-c CATEGORY] [-t TYPE] [--new-category] [--no-push] DOMAIN [DOMAIN...]
#
#   -c CATEGORY      category comment to file the domain(s) under (existing one is reused;
#                    without -c they go to the "待确认归属" group at the top)
#   -t TYPE          rule type, default DOMAIN-SUFFIX
#   --new-category   allow creating CATEGORY even though similarly named categories exist
#   --no-push        commit locally, do not push
#
# Exit codes: 0 ok (or nothing to add) | 1 error | 3 domain already exists | 4 category name needs a decision
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

EXPECTED_REMOTE='love1017best/DirectDomainList'
LIST=DirectDomain.list
YAML=DirectDomain.yaml
MAX_TRIES=5

TYPE='DOMAIN-SUFFIX'
CATEGORY=''
NEW_CATEGORY=0
PUSH=1
DOMAINS=()

die() { echo "ERROR: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    -c) [ $# -ge 2 ] || die "-c needs a value"; CATEGORY="$2"; shift 2 ;;
    -t) [ $# -ge 2 ] || die "-t needs a value"; TYPE="$2"; shift 2 ;;
    --new-category) NEW_CATEGORY=1; shift ;;
    --no-push) PUSH=0; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *) DOMAINS+=("$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"); shift ;;
  esac
done
[ ${#DOMAINS[@]} -gt 0 ] || die "no domain given (see --help)"
for d in "${DOMAINS[@]}"; do
  case "$d" in
    *[[:space:],#]*|'') die "invalid domain: '$d'" ;;
  esac
done

# --- safety checks ---------------------------------------------------------
git remote get-url origin 2>/dev/null | grep -q "$EXPECTED_REMOTE" \
  || die "origin is not $EXPECTED_REMOTE; refusing to operate (ask the user)"
[ -z "$(git status --porcelain --untracked-files=no)" ] \
  || die "working tree has uncommitted changes; commit or stash them first"

sync_remote() {
  local n
  for n in 1 2 3; do
    git fetch origin main && break
    [ "$n" -lt 3 ] || { echo "ERROR: cannot fetch origin (network/SSH?); not editing stale data" >&2; return 1; }
    sleep 2
  done
  git rebase origin/main || { git rebase --abort 2>/dev/null || true; echo "ERROR: rebase onto origin/main failed" >&2; return 1; }
}

# Insert domains. Prints ADDED/EXISTS lines. Exit 0 ok, 3 nothing added (all exist), 4 category needs a decision.
apply_changes() {
  python3 - "$LIST" "$TYPE" "$CATEGORY" "$NEW_CATEGORY" "${DOMAINS[@]}" <<'PY'
import sys
path, typ, cat, new_ok, *domains = sys.argv[1:]
lines = open(path, encoding='utf-8').read().splitlines()

def is_comment(l): return l.strip().startswith('#')
def is_rule(l): return bool(l.strip()) and not is_comment(l)
def name(l): return l.strip().lstrip('#').strip()

# existing rules -> group
group, existing = '(no group)', {}
for l in lines:
    if is_comment(l):
        group = name(l)
    elif is_rule(l) and l.startswith('DOMAIN'):
        t, _, v = l.partition(',')
        existing.setdefault(v.split()[0] if v.split() else '', group)

todo = []
for d in domains:
    if d in existing:
        print(f"EXISTS {d} (in: {existing[d]})")
    else:
        todo.append(d)
if not todo:
    sys.exit(3)

def group_end(idx):  # index just after the last rule line of the group starting at comment idx
    i = idx + 1
    while i < len(lines) and is_rule(lines[i]):
        i += 1
    return i

new_rules = [f"{typ},{d}" for d in todo]
if cat:
    heads = [i for i, l in enumerate(lines) if is_comment(l) and name(l) == cat]
    if heads:
        pos = group_end(heads[0])
        lines[pos:pos] = new_rules
    else:
        similar = sorted({name(l) for l in lines if is_comment(l) and name(l)
                          and (cat.lower() in name(l).lower() or name(l).lower() in cat.lower())})
        if similar and new_ok != '1':
            print(f"CATEGORY '{cat}' does not exist, but similar categories do: {similar}")
            print("Reuse one of them with -c, or pass --new-category to create a new one.")
            sys.exit(4)
        lines += [f"# {cat}"] + new_rules
else:
    heads = [i for i, l in enumerate(lines) if is_comment(l) and name(l).startswith('待确认归属')]
    if not heads:
        print("ERROR: '待确认归属' group not found; pass -c CATEGORY")
        sys.exit(1)
    pos = group_end(heads[0])
    lines[pos:pos] = new_rules

open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
for d in todo:
    print(f"ADDED {d}")
PY
}

joined=$(printf '%s, ' "${DOMAINS[@]}"); joined=${joined%, }
if [ -n "$CATEGORY" ]; then
  msg="Add $joined ($CATEGORY) to direct list"
else
  msg="Add $joined to pending-classification area"
fi

# --- main loop: sync -> apply -> convert -> check -> commit -> push --------
attempt=1
while :; do
  sync_remote || exit 1

  rc=0; apply_changes || rc=$?
  case $rc in
    0) ;;
    3) echo "Nothing to add."; exit 3 ;;
    *) exit "$rc" ;;
  esac

  python3 convert_list_to_yaml.py "$LIST" "$YAML" >/dev/null || die "yaml conversion failed"
  bash check.sh || { git checkout -- "$LIST" "$YAML"; die "check.sh failed; changes reverted"; }

  git add "$LIST" "$YAML"
  git commit -q -m "$msg"
  echo "Committed: $(git log --oneline -1)"

  if [ "$PUSH" -eq 0 ]; then echo "--no-push: not pushed."; exit 0; fi

  if git push origin HEAD:main; then
    git fetch -q origin main || true
    echo "Pushed: $(git log --oneline -1)"
    git status -sb | head -1
    exit 0
  fi

  # Push failed. Race (someone pushed after our sync) or something else?
  if ! git fetch -q origin main; then
    echo "ERROR: push failed and origin is unreachable. Committed locally, NOT pushed. Retry later: git push origin HEAD:main" >&2
    exit 1
  fi
  if git merge-base --is-ancestor origin/main HEAD; then
    echo "ERROR: push failed although local is up to date with origin/main (auth/permissions?). Committed locally, NOT pushed." >&2
    exit 1
  fi
  [ "$attempt" -lt "$MAX_TRIES" ] || die "push rejected $MAX_TRIES times; giving up. Last commit kept locally, NOT pushed."
  echo "Push rejected (remote moved). Dropping own commit and re-applying on top of the new origin/main (attempt $((attempt+1))/$MAX_TRIES)..."
  git reset -q --hard HEAD~1
  attempt=$((attempt+1))
done
