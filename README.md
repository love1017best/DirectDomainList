# DirectDomainList

个人 Clash / Mihomo / Surge 代理**直连规则列表**。用于把国内服务、CDN、App 端点（无需走代理的域名）加入直连。

## 文件说明

| 文件 | 用途 |
|---|---|
| `DirectDomain.list` | **源文件**，唯一需要手工编辑的文件 |
| `DirectDomain.yaml` | 生成的 Clash/Mihomo 格式订阅规则（**勿手改**，由脚本生成） |
| `convert_list_to_yaml.py` | 列表 → YAML 转换脚本 |
| `preprocess_list.py` | 去重 / 规则格式校验脚本（build 时调用）：同组重复自动删除，**跨分类重复会报错并列出所在分类**，由人决定保留哪处 |
| `build.sh` | 可选的一键构建：去重校验 + 转换 YAML |
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

**0. 修改前先同步远端（防异地冲突）：**
```bash
git pull origin main
```
本地如有未提交改动，先提交/暂存再拉取；若分支分叉用 `git pull --no-rebase origin main` 解决冲突。
拉取失败时不要在旧数据上继续改。在 worktree / 非 `main` 分支上改用 `git fetch origin && git rebase origin/main`，推送用 `git push origin HEAD:main`。

添加前先 `grep` 确认域名不存在（同一域名放进不同分类，git 合并不报错，但 CI 重复检查会失败）。

**push 被拒（non-fast-forward）不是网络问题**，说明别处已推送，重试无效，处理方式：
1. `git pull --rebase origin main`
2. `DirectDomain.list` 冲突：保留两边新增的域名，放回正确分类，再检查重复。
3. **`DirectDomain.yaml` 冲突：不要手动合并，也不要只留一边**。先解决 `.list`，再用脚本重新生成并 `git add`，`git rebase --continue`。
4. 重新 push；仍被拒就重复以上步骤。

**1. 添加/修改域名后转 YAML：**
```bash
python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml
```

**2. 或直接一键构建（去重 + 格式校验 + 转换，批量修改或解决冲突后推荐）：**
```bash
./build.sh
```

**3. 生成后提交推送即可**，其它设备更新订阅 / clone 拉取。

## AI / Skill 辅助维护

本仓库内置 `skills/direct-domain-manager/SKILL.md`，供 AI Agent（如 Claude Code、Minis 等）识别该仓库用途并复用维护流程。其规范与上文的"分类注释规范"一致。
