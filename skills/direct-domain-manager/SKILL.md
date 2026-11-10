---
name: direct-domain-manager
description: Manage DirectDomainList repository for proxy rules. Use when user wants to add domains to direct connection list, convert list format, or commit changes. Triggers on phrases like "add domain", "直连列表", "添加域名", "DOMAIN-SUFFIX", or any domain management requests related to proxy rules.
---

# Direct Domain Manager

Manage the DirectDomainList repository (`DirectDomain.list` source + generated `DirectDomain.yaml`) for Clash/Mihomo/Surge proxy rules.
Several agents / devices edit this repo independently, so the workflow below is built to avoid conflicts. See also `AGENTS.md` at the repo root.

## Repository Requirements

**CRITICAL**: Only operate on a repository with remote URL matching:
```
github.com:love1017best/DirectDomainList.git
```

Verify with `git remote -v`. If the remote URL doesn't match, ask the user for confirmation before proceeding. (`add_domain.sh` refuses automatically.)

Find the repository: check the working dir first (e.g. `/var/minis/workspace/DirectDomainList`).

## Supported Operations

### 1. Add Domain to Direct List

When user says things like:
- "添加 xxx 到直连列表"
- "在直连列表中加入 xxx"
- "Add xxx to direct list"
- "DOMAIN-SUFFIX,xxx"
- "under the <comment> section add xxx"

**Use the script. It is the standard path** (deterministic; do not re-implement its steps by hand unless it cannot run):

```bash
bash add_domain.sh -c <category> <domain> [<domain> ...]
```

- Without `-c`, domains go to the "待确认归属" group at the top.
- `-t TYPE` changes the rule type (default `DOMAIN-SUFFIX`). `--no-push` commits without pushing.
- It does, in order: verify remote → require a clean tree → fetch + `rebase origin/main` (stops if the fetch fails, never edits stale data) → duplicate check → insert under the category → regenerate YAML → `check.sh` → commit (`Add <domain> (<category>) to direct list`) → `git push origin HEAD:main`.
- If the push is rejected (remote moved), it drops its own commit, re-syncs, re-applies and pushes again (up to 5 attempts). If the remote is unreachable it stops and says the commit is local only.
- Exit codes: `0` ok · `1` error · `3` domain already exists (tell the user where) · `4` category name is similar to existing ones (reuse one with `-c`, or confirm with the user and pass `--new-category`).

**Category naming:** before creating a category, check existing ones (`grep '^# ' DirectDomain.list`) and reuse when possible (avoid "京东" vs "京东服务" style near-duplicates). A category is a comment on its own line **ABOVE** its domain rule(s):

✅ **正确格式**:
```
# 校友邦
DOMAIN-SUFFIX,xybsyw.com
```

❌ **错误格式**（不要用行尾注释）:
```
DOMAIN-SUFFIX,xybsyw.com  # 校友邦
```

**Expected, not a bug:** all new domains land at the same spot (end of a group), so two agents adding at about the same time produce a textual conflict. Resolution = keep both sides' additions, regenerate the YAML. The script does this automatically.

#### Manual fallback (only if the script cannot run)

1. `git fetch origin && git rebase origin/main` (retry a couple of times; if it keeps failing, STOP and tell the user). Commit/stash local changes first.
2. Duplicate check: `grep -nE '^DOMAIN[^,]*,<domain>([^A-Za-z0-9.-]|$)' DirectDomain.list`; if present, don't add it again.
3. Add the category comment (if new) and `DOMAIN-SUFFIX,<domain>` beneath it.
4. `python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml`, then `bash check.sh`.
5. `git add DirectDomain.list DirectDomain.yaml && git commit -m "Add <domain> (<category>) to direct list"`
6. `git push origin HEAD:main`, then verify with `git status` and `git log --oneline -1`.

Never modify the files without committing and pushing (unpushed commits are lost when a worktree is recycled).

### Conflict Handling (manual flow: push rejected / merge conflicts)

A push rejected as non-fast-forward means another device pushed after your sync. It is NOT a network error; retrying the same push never succeeds.

1. `git fetch origin && git rebase origin/main` (always rebase; do not create merge commits).
2. If `DirectDomain.list` conflicts: keep BOTH sides' added domains, each in the correct category section (comment line above its domains). Re-run the duplicate check on the merged result.
3. **`DirectDomain.yaml` conflicts: NEVER hand-merge, and never just pick one side.** Resolve the `.list` first, then regenerate:
   ```bash
   python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
   git add DirectDomain.list DirectDomain.yaml
   git rebase --continue
   ```
4. `bash check.sh`, then push again. If rejected again, repeat from 1.
5. If anything is unclear (e.g. same domain filed under different categories on both sides), ask the user instead of guessing.

### 2. Convert List to YAML

```bash
python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
```

Optional full build (use after bulk edits or conflict resolution): `bash build.sh` runs `preprocess_list.py` and then the conversion above. The preprocessor auto-removes duplicates **within the same category group** in place (backup `DirectDomain.list.bak` is gitignored), validates rule types, and **fails (without modifying the file) if the same rule appears under more than one category**, listing the groups involved. Decide which category keeps it, delete the other, and re-run.

### 3. Check

```bash
bash check.sh
```

Duplicates (global), rule format, YAML in sync with the list (+ YAML parse if PyYAML is installed). CI runs exactly this script, so run it before every push.

### 4. View Current List

Read `DirectDomain.list` to show current domains grouped by category comments.

## File Structure

```
DirectDomainList/
├── DirectDomain.list                    # Source list file (edit this)
├── DirectDomain.yaml                    # Generated YAML for Clash/Mihomo (do not edit by hand)
├── add_domain.sh                        # Standard way to add domains (sync, dedupe, insert, convert, check, commit, push w/ retry)
├── check.sh                             # Duplicate / format / YAML-sync checks; shared by CI and local use
├── convert_list_to_yaml.py              # Conversion script (run from repo root)
├── preprocess_list.py                   # Dedup + rule-format validation; called by build.sh
├── build.sh                             # Optional full build: preprocess + convert
├── AGENTS.md / CLAUDE.md                # Short rules for agents (CLAUDE.md just imports AGENTS.md)
└── skills/direct-domain-manager/
    └── SKILL.md                         # This skill definition
```

## Safety Checks

Always verify:
1. Correct repository (`git remote -v` matches DirectDomainList)
2. **Remote synced first** (`git fetch` + `rebase origin/main` succeeded) before any file modification; if it fails, stop
3. Clean working tree before starting
4. `bash check.sh` passes before pushing
5. Ask user for confirmation if anything is uncertain
