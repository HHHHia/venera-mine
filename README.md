# venera-mine

自己的 Venera 图源仓库：镜像上游 `venera-app/venera-configs`，叠加本地补丁，生成 `index.json` + `sources/*.js`，用 **GitHub Pages** 托管。

App 里「图源列表地址」填：

```
https://hhhhia.github.io/venera-mine/index.json
```

## 目录

| 路径 | 作用 |
|---|---|
| `overlay/` | **你手动维护的补丁**。放同名 `.js`（例如 `overlay/wnacg.js`），构建时覆盖上游同名文件 |
| `sources/` | 构建产物，33 个源，不要手改 |
| `index.json` | 构建产物，App 拉的就是它 |
| `build.py` | 构建脚本，只依赖 Python 标准库 |
| `base.txt` | 站点根地址 `https://hhhhia.github.io/venera-mine/` |

GitHub Pages 只做静态托管，**不跑** `build.py`：构建在本机跑，产物一起提交。

## 改一个源 / 跟上游同步

```bat
cd /d D:\UUUUse\Study\ChatAI\venera-mine
python build.py --offline --upstream-dir D:\UUUUse\Study\ChatAI\venera-configs
```

联网环境可以去掉 `--offline --upstream-dir ...`，脚本自己去 jsDelivr 拉上游。

然后 `git add -A && git commit -m "..." && git push`，Pages 约 1 分钟重新部署。

被 `overlay/` 覆盖的源会自动：

- 版本号 +1（永远比上游高一级，App 才会提示"有更新"）
- 内部 `url` 字段改写成你的地址（否则点「更新」会拉回上游、把补丁冲掉）

## 已知补丁

- `overlay/wnacg.js`（紳士漫畫）：发布页 `wn01.link` 改版成 JS 渲染（301 → `wnacg01.link` → `wnacglink.com`），静态 HTML 里 0 个 http 链接，上游 `refreshDomains()` 永远抓空 → `Wnacg.domains = []`，导致
  - `baseUrl` 抛 `Selected domain is unavailable`
  - 设置页 `select` 的选项只剩 Custom Domain，已存序号不在选项里 → `Bad state: No element` 崩溃，设置页打不开

  补丁做了三件事：`baseUrl` 越界时回退到自定义域名；`domainSelection` 从 `select` 改成 `input`（彻底躲开崩溃）；默认域名改成 2026-11-19 实测可用的 `www.wnacg.site`。

## 注意

- 仓库是**公开**的：上游也是公开的、文件名和 key 一致，别人 `git diff` 就能看出你改了哪个源。要藏起来只能换私有仓库 + Cloudflare Pages。
- 不要往 js 里写账号密码、cookie、token。
- 域名会变：`www.wnacg.site` 失效时，改 `overlay/wnacg.js` 里 `domain0` 的 `default`，或在 App 源设置里直接改 Custom Domain。
