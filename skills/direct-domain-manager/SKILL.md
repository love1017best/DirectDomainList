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
4. **If there is a comment**: add the comment line first (if not already present), then add `DOMAIN-SUFFIX,<domain>` on the next line
5. Run the conversion script:
   ```bash
   python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
   ```
6. **Git add**: `git add DirectDomain.list DirectDomain.yaml`
7. **Git commit**: `git commit -m "Add <domain> (<comment>) to direct list"`
8. **Git push**: `git push origin main`
9. **Verify push**: run `git status` (clean working tree) and `git log --oneline -1` (shows the latest commit). If push fails (e.g. SSH `Connection closed by ... port 22` or network issue), retry a couple times; if still failing, tell the user it's committed locally but not yet pushed, and offer to retry later.

**⚠️ 重要**: Steps 6–8 must run together — never modify the files without committing and pushing.

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
2. File exists before modification
3. Git status is clean or handle pending changes accordingly
4. Ask user for confirmation if anything is uncertain
