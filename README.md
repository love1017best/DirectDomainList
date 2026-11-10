# DirectDomainList

个人 Clash / Mihomo / Surge 代理**直连规则列表**。用于把国内服务、CDN、App 端点（无需走代理的域名）加入直连。

## 文件说明

| 文件 | 用途 |
|---|---|
| `DirectDomain.list` | **源文件**，唯一需要手工编辑的文件 |
| `DirectDomain.yaml` | 生成的 Clash/Mihomo 格式订阅规则（**勿手改**，由脚本生成） |
| `add_domain.sh` | **添加域名的标准方式**：同步远端、查重、插入分类、生成 YAML、检查、提交、推送（被拒自动重试） |
| `check.sh` | 重复 / 格式 / YAML 同步检查，CI 与本地共用，推送前运行 |
| `convert_list_to_yaml.py` | 列表 → YAML 转换脚本 |
| `preprocess_list.py` | 去重 / 规则格式校验脚本（build 时调用）：同组重复自动删除，**跨分类重复会报错并列出所在分类**，由人决定保留哪处 |
| `build.sh` | 可选的一键构建：去重校验 + 转换 YAML |
| `AGENTS.md` / `CLAUDE.md` | 给 AI Agent 的简短硬规则（`CLAUDE.md` 仅引用 `AGENTS.md`） |
| `skills/direct-domain-manager/` | 内置的 AI Skill 定义，供各端 AI Agent 读取复用 |

## 规则文件格式

`DirectDomain.list` 为纯文本，每条规则一行，支持 Clash 语法：

```
DOMAIN-SUFFIX,example.com
DOMAIN,sub.example.com
DOMAIN-KEYWORD,kwai
USER-AGENT,Hodor*
```

### 分类注释规范（重要）

分类（如 App / 服务归属）用注释行表示，**注释单独成行、置于该分类全部域名上方**。每个分类注释下可包含多条同属域名：

```
# 火山SDK
DOMAIN-SUFFIX,volces.com

# 抖音商城
DOMAIN-SUFFIX,bytegecko.com
DOMAIN-SUFFIX,ecombdimg.com
```

> ⚠️ 不要使用行尾注释（`DOMAIN-SUFFIX,x.com  # 飞书`），分类会用问题。
> 个别官方细粒度注释如 `blog.google // Google Blog` 的 `//` 是 Clash 兼容语法，可保留。

列表**最顶部**为一批**尚未确认归属**的域名（集中放置，不属于任何分类），确认归属后可移入对应分类注释下。

## 使用方式

多台设备 / 多个 agent 会各自修改本仓库，所以**添加域名一律用脚本**，不要手动走 git 步骤：

```bash
bash add_domain.sh -c 分类名 域名1 [域名2 ...]    # 不带 -c 则放入顶部「待确认归属」组
```

脚本依次完成：校验远端是 `love1017best/DirectDomainList` → 要求工作区干净 → `fetch` + `rebase origin/main`（失败即停，不在旧数据上改）→ 查重 → 插入到分类下 → 生成 YAML → 跑 `check.sh` → 提交 → `git push origin HEAD:main`。
push 被拒（别处已推送）时，脚本会丢弃自己的提交，在最新的 `origin/main` 上重新应用并再推，最多 5 次。

| 退出码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 出错（远端不符、工作区不干净、同步失败等） |
| 3 | 域名已存在（会显示在哪个分类） |
| 4 | 分类名与已有分类相似，请复用已有分类（`-c`），或确认后加 `--new-category` |

其它选项：`-t TYPE` 指定规则类型（默认 `DOMAIN-SUFFIX`），`--no-push` 只提交不推送。

**新建分类前先查已有分类名**（`grep '^# ' DirectDomain.list`），能复用就复用，避免「京东」「京东服务」这类近似重复。

> 所有新域名都追加在同一处（某分类末尾或「待确认归属」组末尾），所以两个 agent 同时添加会产生文本冲突，这是**预期行为**。解决方式是保留两边新增并重新生成 YAML，脚本会自动处理。

### 手动流程（仅脚本无法运行时）

1. 同步：`git fetch origin && git rebase origin/main`（统一用 rebase，不产生合并提交；失败就停下）。本地有未提交改动先提交/暂存。
2. 用 `grep` 确认域名不存在（同一域名放进不同分类，git 合并不报错，但 CI 重复检查会失败）。
3. 编辑 `DirectDomain.list`，然后 `python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml`（或 `bash build.sh`：去重 + 格式校验 + 转换，批量修改或解决冲突后推荐）。
4. `bash check.sh` 通过后提交，并 `git push origin HEAD:main`。

**push 被拒（non-fast-forward）不是网络问题**，重试同一个 push 没用：
1. `git fetch origin && git rebase origin/main`
2. `DirectDomain.list` 冲突：保留两边新增的域名，放回正确分类，再检查重复。
3. **`DirectDomain.yaml` 冲突：不要手动合并，也不要只留一边**。先解决 `.list`，再用脚本重新生成并 `git add`，`git rebase --continue`。
4. 重新 push；仍被拒就重复以上步骤。

### 检查

```bash
bash check.sh
```

检查重复（全局）、规则格式、YAML 是否与列表同步。CI 跑的就是这个脚本，推送前请先在本地运行。

## AI / Skill 辅助维护

根目录的 `AGENTS.md`（`CLAUDE.md` 引用它）给出 agent 必须遵守的硬规则；`skills/direct-domain-manager/SKILL.md` 供 AI Agent（如 Claude Code、Minis 等）识别该仓库用途并复用维护流程。两者与上文的"分类注释规范"一致。
