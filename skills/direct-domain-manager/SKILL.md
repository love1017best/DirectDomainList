---
name: direct-domain-manager
description: Manage DirectDomainList repository for proxy rules. Use when user wants to add domains to direct connection list, convert list format, or commit changes. Triggers on phrases like "add domain", "直连列表", "添加域名", "DOMAIN-SUFFIX", or any domain management requests related to proxy rules.
---

# Direct Domain Manager

Manage the DirectDomainList repository (`DirectDomain.list` source + generated `DirectDomain.yaml`) for Clash/Mihomo/Surge proxy rules.

## Repository Requirements

**CRITICAL**: Only operate on a repository with remote URL matching:
```
github.com:love1017best/DirectDomainList.git
```

Verify with `git remote -v`. If the remote URL doesn't match, ask the user for confirmation before proceeding.

## Supported Operations

### 1. Add Domain to Direct List

When user says things like:
- "添加 xxx 到直连列表"
- "在直连列表中加入 xxx"
- "Add xxx to direct list"
- "DOMAIN-SUFFIX,xxx"
- "under the <comment> section add xxx"

**Comment Format (IMPORTANT):**
A comment (中文分类名 like 飞书 / 校友邦 / 抖音商城 or a brand name) must be on its own line **ABOVE** the domain rule(s):

✅ **正确格式**:
```
# 校友邦
DOMAIN-SUFFIX,xybsyw.com
```

❌ **错误格式**（不要用行尾注释）:
```
DOMAIN-SUFFIX,xybsyw.com  # 校友邦
```

To group a new domain under an existing comment section, insert the new `DOMAIN-SUFFIX,<domain>` line directly beneath that category's comment.

**Steps (must ALL be completed):**
1. Parse the domain and optional comment/category from the user's request
2. Find the DirectDomainList repository (check working dir first: `/var/minis/workspace/DirectDomainList`)
3. Verify it's the correct repository by checking `git remote -v`
4. **Sync remote BEFORE touching any file** (mandatory — prevents conflicts with edits made on other devices):
   ```bash
   git pull origin main
   ```
   - Retry a couple times if it fails (e.g. SSH `Connection closed by ... port 22` / network issue).
   - If the working tree has uncommitted changes, commit (or stash) them first, then pull.
   - If branches have diverged, use `git pull --no-rebase origin main` and resolve any conflicts before continuing.
   - If the pull fails after retries, STOP. Do not edit on top of stale data; tell the user.
   - On a worktree / non-`main` branch (where `main` is checked out elsewhere): `git fetch origin && git rebase origin/main` (or `git merge --ff-only origin/main`) instead of `git pull origin main`.
5. **Duplicate check BEFORE adding** (git cannot detect semantic duplicates; CI will fail on them):
   ```bash
   grep -nE '^DOMAIN[^,]*,<domain>([^A-Za-z0-9.-]|$)' DirectDomain.list
   ```
   If the domain already exists (under any category), do not add it again; tell the user where it is.
6. **If there is a comment**: add the comment line first (if not already present), then add `DOMAIN-SUFFIX,<domain>` on the next line
7. Run the conversion script:
   ```bash
   python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
   ```
8. **Git add**: `git add DirectDomain.list DirectDomain.yaml`
9. **Git commit**: `git commit -m "Add <domain> (<comment>) to direct list"`
10. **Git push**: `git push origin main` (on a worktree / non-`main` branch: `git push origin HEAD:main`). If rejected (non-fast-forward), do NOT just retry — follow "Conflict Handling" below.
11. **Verify push**: run `git status` (clean working tree) and `git log --oneline -1` (shows the latest commit). If push fails (e.g. SSH `Connection closed by ... port 22` or network issue), retry a couple times; if still failing, tell the user it's committed locally but not yet pushed, and offer to retry later.

**⚠️ 重要**: Always sync BEFORE editing (step 4), and run steps 8–10 together — never modify the files without committing and pushing.

### Conflict Handling (push rejected / merge conflicts)

A push rejected as non-fast-forward means another device pushed after your sync. It is NOT a network error; retrying the same push will never succeed.

1. `git pull --rebase origin main` (worktree / non-`main` branch: `git fetch origin && git rebase origin/main`).
2. If `DirectDomain.list` conflicts: resolve it by keeping BOTH sides' added domains, in the correct category sections (comment line above its domains). Re-run the duplicate check from step 5 on the merged result.
3. **`DirectDomain.yaml` conflicts: NEVER hand-merge, and never just pick one side.** Resolve the `.list` first, then regenerate:
   ```bash
   python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
   git add DirectDomain.list DirectDomain.yaml
   git rebase --continue
   ```
4. Push again (step 10). If it is rejected again, repeat from 1.
5. If anything is unclear (e.g. same domain filed under different categories on both sides), ask the user instead of guessing.

### 2. Convert List to YAML

Run manually when needed:
```bash
python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
```

### 3. View Current List

Read `DirectDomain.list` to show current domains grouped by category comments.

## File Structure

```
DirectDomainList/
├── DirectDomain.list                    # Source list file (edit this)
├── DirectDomain.yaml                    # Generated YAML for Clash/Mihomo (do not edit by hand)
├── convert_list_to_yaml.py              # Conversion script (run from repo root)
├── preprocess_list.py                   # (legacy) preprocessing helper
├── build.sh                             # (legacy) build helper
└── skills/direct-domain-manager/
    └── SKILL.md                         # This skill definition
```

## Safety Checks

Always verify:
1. Correct repository (`git remote -v` matches DirectDomainList)
2. **Remote synced first**: `git pull origin main` completed before any file modification (prevents cross-device conflicts)
3. File exists before modification
4. Git status is clean or handle pending changes accordingly
5. Ask user for confirmation if anything is uncertain
