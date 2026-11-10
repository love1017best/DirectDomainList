# DirectDomainList：给 AI Agent 的操作说明

个人 Clash / Mihomo / Surge 直连规则仓库。**多个 agent / 多台设备会各自独立修改它**，下面的规则用来避免冲突。
完整流程见 `skills/direct-domain-manager/SKILL.md`，文件说明见 `README.md`。

## 添加域名：只用脚本

```bash
bash add_domain.sh -c 分类名 域名1 [域名2 ...]   # 不带 -c 则放入顶部「待确认归属」组
```

脚本会自动完成：校验远端、同步 `origin/main`、查重、插入到分类下、生成 YAML、跑 `check.sh`、提交、推送；push 被拒时自动在最新的 `origin/main` 上重做，最多 5 次。
退出码：`3` 域名已存在；`4` 分类名与已有分类相似，需要复用已有分类（`-c`）或加 `--new-category`。

## 硬规则

1. **改之前先同步远端**。同步失败就停下，不要在旧数据上继续改。统一用 rebase，不要产生合并提交：`git fetch origin && git rebase origin/main`。
2. **只手工编辑 `DirectDomain.list`**。`DirectDomain.yaml` 由脚本生成，永远不要手改，也不要手动合并它的冲突：解决 `.list` 后重新运行 `python3 convert_list_to_yaml.py DirectDomain.list DirectDomain.yaml`。
3. **改完必须提交并推送到 `main`**，不要只改不推（worktree / 非 main 分支用 `git push origin HEAD:main`）。未推送的提交在 worktree 被回收时会丢失。
4. **推送前跑 `bash check.sh`**（重复、格式、yaml 同步），CI 跑的是同一个脚本。
5. **push 被拒（non-fast-forward）不是网络问题**，重试同一个 push 没用：重新同步、重新应用改动、再推。
6. **分类注释独占一行，放在该分类域名上方**，不要用行尾注释。
7. **新建分类前先查已有分类名**（`grep '^# ' DirectDomain.list`），能复用就复用，避免「京东」「京东服务」这类近似重复。
8. 只在 `origin` 为 `love1017best/DirectDomainList` 的仓库里操作，否则先问用户。

## 预期内的现象

所有新域名都追加在同一处（「待确认归属」组末尾或某分类末尾），所以两个 agent 先后添加时，**文本冲突是预期行为**，不是异常。解决方式：保留两边新增的域名，再重新生成 yaml。使用 `add_domain.sh` 时这一步是自动的。

## .git 损坏时

沙盒文件系统（iSH 等）上偶发 `.git/objects` 目录损坏（`fsck` 报 missing object / `Not a directory`）。**不要尝试修复对象库**：本地永远没有远端没有的内容（规则1保证了改动都会及时推送），所以直接重来：

```bash
mv DirectDomainList DirectDomainList.broken   # 坏树的 readdir 可能异常，rm -rf 未必删得掉
git clone git@github.com:love1017best/DirectDomainList.git
```
新克隆 `git fsck` 干净、`bash check.sh` 通过后再继续；损坏目录事后清理即可。

## 不适用

本仓库没有版本号，全局约定里的 `vX.Y.Z` 规则在这里不适用。
