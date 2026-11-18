# venera-mine

自己的 Venera 图源仓库：镜像上游 `venera-app/venera-configs`，加上本地补丁，生成 `index.json` + `sources/*.js`，用 **Cloudflare Pages（私有仓库）** 托管，App 里把这个地址填进「图源列表地址」即可。

私有仓库 + Cloudflare Pages 的意义：别人看不到你镜像了哪些源、改了哪个源。

## 目录

| 路径 | 作用 |
|---|---|
| `overlay/` | **你手动维护的补丁**。放同名的 `.js`（例如 `overlay/wnacg.js`），构建时会覆盖上游同名文件 |
| `sources/` | 构建产物，33 个源，不要手改 |
| `index.json` | 构建产物，App 拉的就是它 |
| `build.py` | 构建脚本，只依赖 Python 标准库 |
| `base.txt` | 你的站点根地址（默认 `https://venera-mine.pages.dev/`） |

Cloudflare Pages 只做静态托管，**不跑** `build.py`：构建在你本机跑，产物一起提交。

## 一次性部署

1. 确认 `base.txt` 和 Pages 项目名一致。项目名决定域名，如果你建的项目名不是 `venera-mine`，把 `base.txt` 改成：

   ```
   https://<你的项目名>.pages.dev/
   ```

   然后跑一次构建（见第 2 步）。

2. 构建：

   ```bat
   cd /d D:\UUUUse\Study\ChatAI\venera-mine
   python build.py --offline --upstream-dir D:\UUUUse\Study\ChatAI\venera-configs
   ```

   输出应该是 `源数量: 33，其中你改过的: 1 (wnacg.js)`。
   联网环境可以去掉 `--offline --upstream-dir ...`，脚本自己去 jsDelivr 拉上游。

3. GitHub Desktop → File → Add local repository → 选这个目录 → Publish repository：
   - 名字 `venera-mine`
   - **勾上 Private**（私有仓库，必需）

4. Cloudflare Dashboard → **Workers & Pages** → Create → **Pages** → Connect to Git → 授权 GitHub 时选 **Only select repositories**，只勾 `venera-mine`（不要给全账号权限）。

5. 配置构建：
   - Project name：`venera-mine`（决定域名）
   - Framework preset：`None`
   - Build command：留空
   - Build output directory：`/`

   Save and Deploy，等约 1 分钟。

6. 打开 `https://venera-mine.pages.dev/index.json`，能看到 JSON 就成功。

7. App：设置 → 图源列表地址 → 填

   ```
   https://venera-mine.pages.dev/index.json
   ```

   进图源页刷新列表，逐个添加要用的源。

## 日常维护

改某个源的逻辑：

1. 把上游同名文件拷到 `overlay/`（第一次），改它。
2. 跑构建命令（第 2 步）。被 `overlay/` 覆盖的源会自动：
   - 版本号 +1（永远比上游高一级，App 才会提示"有更新"）
   - 内部 `url` 字段改写成你的地址（否则点「更新」会拉回上游、把补丁冲掉）
3. 提交并推送，Cloudflare Pages 自动重新部署（几十秒）。

跟上游同步：定期跑一次构建 + 推送。上游新增/删除的源会自动跟进（`sources/` 里残留的旧文件会被清掉）。

## 已知补丁

- `overlay/wnacg.js`（紳士漫畫）：发布页 `wn01.link` 改版成 JS 渲染（301 → `wnacg01.link` → `wnacglink.com`），HTML 里 0 个 http 链接，上游的 `refreshDomains()` 永远抓空 → `Wnacg.domains = []`，导致
  - `baseUrl` 抛 `Selected domain is unavailable`
  - 设置页 `select` 的选项只剩 Custom Domain，已存序号不在选项里 → `Bad state: No element` 崩溃，设置页打不开

  补丁做了三件事：`baseUrl` 越界时回退到自定义域名；`domainSelection` 从 `select` 改成 `input`（彻底躲开崩溃）；默认域名改成当时（2026-11-19）实测可用的 `www.wnacg.site`。

## 注意

- 不要往 js 里写账号密码、cookie、token。
- 域名会变：`www.wnacg.site` 失效时，改 `overlay/wnacg.js` 里 `domain0` 的 `default`，或在 App 源设置里直接改 Custom Domain。
- 别把 `base.txt` 的域名写错成别人的项目：index.json 里每条都是绝对地址，错了 App 会全部拉不到。
