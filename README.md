# venera-mine

自己的 Venera 图源仓库：镜像上游 `venera-app/venera-configs`，加上本地补丁，生成 `index.json` + `sources/*.js`，用 GitHub Pages 托管，App 里把这个地址填进「图源列表地址」即可。

## 目录

| 路径 | 作用 |
|---|---|
| `overlay/` | **你手动维护的补丁**。放同名的 `.js`（例如 `overlay/wnacg.js`），构建时会覆盖上游同名文件 |
| `sources/` | 构建产物，33 个源，不要手改 |
| `index.json` | 构建产物，App 拉的就是它 |
| `build.py` | 构建脚本，只依赖 Python 标准库 |
| `base.txt` | 你的站点根地址，**改成自己的再构建** |

## 一次性部署

1. 编辑 `base.txt`，填你的 Pages 地址（注意结尾斜杠）：

   ```
   https://<你的GitHub用户名>.github.io/venera-mine/
   ```

2. 构建（Windows 上任意 Python 3.8+ 均可）：

   ```bat
   cd /d D:\UUUUse\Study\ChatAI\venera-mine
   python build.py --offline --upstream-dir D:\UUUUse\Study\ChatAI\venera-configs
   ```

   联网环境可以去掉 `--offline --upstream-dir ...`，脚本会自己去 jsDelivr 拉上游。

3. 用 GitHub Desktop 把这个目录建成仓库（名字建议 `venera-mine`），推送到 GitHub。

4. 仓库 Settings → Pages → Source 选 `Deploy from a branch`，分支 `main`，目录 `/ (root)`，保存。

5. 等 1~2 分钟，浏览器打开 `https://<用户名>.github.io/venera-mine/index.json`，能看到 JSON 就成功。

6. App：设置 → 图源列表地址 → 填

   ```
   https://<用户名>.github.io/venera-mine/index.json
   ```

   然后进图源页面刷新列表，逐个添加你要用的源。

## 日常维护

改某个源的逻辑：

1. 把上游同名文件拷到 `overlay/`（第一次），改它。
2. 跑第 2 步的构建命令。被 `overlay/` 覆盖的源会自动：
   - 版本号 +1（永远比上游高一级，App 才会提示"有更新"）
   - 内部 `url` 字段改写成你的地址（否则点「更新」会拉回上游、把补丁冲掉）
3. 推送。Pages 约 10 分钟内生效。

跟上游同步：定期跑一次构建命令 + 推送即可；上游新增/删除的源会自动跟进（`sources/` 里残留的旧文件会被清掉）。

## 已知补丁

- `overlay/wnacg.js`（紳士漫畫）：发布页 `wn01.link` 改版成 JS 渲染、HTML 里 0 个 http 链接，上游的 `refreshDomains()` 永远抓空 → `Wnacg.domains = []`，导致
  - `baseUrl` 抛 `Selected domain is unavailable`
  - 设置页 `select` 的选项只剩 Custom Domain，已存序号不在选项里 → `Bad state: No element` 崩溃，设置页打不开

  补丁做了三件事：`baseUrl` 越界时回退到自定义域名；`domainSelection` 从 `select` 改成 `input`（彻底躲开崩溃）；默认域名改成当时实测可用的 `www.wnacg.site`。

## 注意

- **公开仓库能被 diff 出你改了哪个源**：上游仓库是公开的、文件名和 key 完全一致，`git diff` 一条命令就能看出。要真的藏起来，只能私有仓库 + Cloudflare Pages（免费，支持私库构建）。
- 不要往 js 里写账号密码、cookie、token。
