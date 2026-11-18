#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成自己的 Venera 图源仓库 (index.json + sources/*.js)。

流程:
  1. 拉上游 venera-configs 的 index.json 和每个图源的 js
  2. overlay/ 里有同名文件的，用你的版本替换（这就是"我的修改"）
  3. 被替换的源，版本号自动 +1（永远比上游高一级），并把 js 内部的 url 字段
     改写成你自己的地址（否则 App 点"更新"会拉上游、把你的补丁冲掉）
  4. 输出 sources/*.js + index.json

用法:
  python build.py --base https://<你的用户名>.github.io/venera-mine/ \
                  --upstream-dir D:\\UUUUse\\Study\\ChatAI\\venera-configs

  不加 --upstream-dir 时走网络（jsDelivr）；加 --offline 则只用本地副本。
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.join(ROOT, "sources")
OVERLAY_DIR = os.path.join(ROOT, "overlay")
INDEX_PATH = os.path.join(ROOT, "index.json")

UPSTREAM_INDEX = "https://cdn.jsdelivr.net/gh/venera-app/venera-configs@main/index.json"
NOT_A_SOURCE = {"_template_.js", "_venera_.js"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def load_upstream_index(local_dir):
    if local_dir:
        path = os.path.join(local_dir, "index.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def local_read(name):
            with open(os.path.join(local_dir, name), "r", encoding="utf-8") as fh:
                return fh.read()

        return data, path, local_read
    return (
        json.loads(http_get(UPSTREAM_INDEX)),
        UPSTREAM_INDEX,
        (lambda name: http_get(UPSTREAM_INDEX.rsplit("/", 1)[0] + "/" + name)),
    )


def bump_version(version):
    """"1.0.6" -> "1.0.7"；带后缀的只动数字部分。"""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", version.strip())
    if not m:
        return None
    major, minor, patch, suffix = m.groups()
    return "%s.%s.%d%s" % (major, minor, int(patch) + 1, suffix)


def rewrite_url(content, new_url):
    """改 js 顶部的 url = "..."（也就是源内声明的更新地址）。"""
    pattern = re.compile(r'(^\s*url\s*=\s*")([^"]*)(")', re.M)
    if not pattern.search(content):
        return content, False
    return pattern.sub(lambda m: m.group(1) + new_url + m.group(3), content, count=1), True


def rewrite_version(content, version):
    pattern = re.compile(r'(^\s*version\s*=\s*")([^"]*)(")', re.M)
    if not pattern.search(content):
        return content, False
    return pattern.sub(lambda m: m.group(1) + version + m.group(3), content, count=1), True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="", help="你自己的站点根地址，例如 https://name.github.io/venera-mine/")
    ap.add_argument("--upstream-dir", default="", help="本地 venera-configs 克隆目录（离线模式）")
    ap.add_argument("--offline", action="store_true", help="只读本地副本，不联网")
    args = ap.parse_args()

    base = args.base.strip()
    if not base:
        base_file = os.path.join(ROOT, "base.txt")
        if os.path.exists(base_file):
            with open(base_file, "r", encoding="utf-8") as f:
                base = f.read().strip()
    if base and not base.endswith("/"):
        base += "/"

    upstream_dir = args.upstream_dir.strip() or ""
    if args.offline and not upstream_dir:
        sys.exit("--offline 需要同时给 --upstream-dir")
    if not base:
        sys.exit(
            "缺少站点地址：请把 base.txt 里的 PLACEHOLDER 改成你的 Pages 地址，"
            "或加 --base https://xxx/"
        )

    upstream, origin, fetch_file = load_upstream_index(upstream_dir)
    os.makedirs(SOURCES_DIR, exist_ok=True)
    os.makedirs(OVERLAY_DIR, exist_ok=True)

    overrides = {
        f for f in os.listdir(OVERLAY_DIR)
        if f.endswith(".js") and f not in NOT_A_SOURCE
    }

    index = []
    patched, bumped = [], []

    for entry in upstream:
        name = entry["name"]
        file_name = entry["fileName"]
        if file_name in NOT_A_SOURCE:
            continue

        if file_name in overrides:
            with open(os.path.join(OVERLAY_DIR, file_name), "r", encoding="utf-8") as f:
                content = f.read()
            patched.append(file_name)

            new_version = bump_version(str(entry.get("version", "0.0.0")))
            old_version = entry.get("version")
            if new_version:
                content, ok = rewrite_version(content, new_version)
                if not ok:
                    print("  ! %s 里没找到 version = \"...\" 行" % file_name)
                entry = dict(entry, version=new_version)
                bumped.append((file_name, old_version, new_version))

            content, ok = rewrite_url(content, base + "sources/" + file_name)
            if not ok:
                print("  ! %s 里没找到 url = \"...\" 行，更新时可能拉回上游版本" % file_name)
        else:
            content = fetch_file(file_name)

        with open(os.path.join(SOURCES_DIR, file_name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        # 每条都给绝对 url：App 会优先用它（comic_source_page.dart:481），
        # 不依赖 index.json 所在目录去拼文件名，文件放 sources/ 子目录也能用。
        out = dict(entry)
        out["url"] = base + "sources/" + file_name
        index.append(out)

    with open(INDEX_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, ensure_ascii=False, indent=4)
        f.write("\n")

    # 清掉上游已删除、但本地残留的源
    keep = {e["fileName"] for e in index}
    for f in os.listdir(SOURCES_DIR):
        if f.endswith(".js") and f not in keep:
            os.remove(os.path.join(SOURCES_DIR, f))
            print("  - 删除已不存在于上游的: %s" % f)

    print("上游索引: %s" % origin)
    print("源数量: %d，其中你改过的: %d%s" % (
        len(index), len(patched), (" (" + ", ".join(sorted(patched)) + ")") if patched else ""))
    for fn, _old, new in bumped:
        print("  ~ %s 版本提升到 %s" % (fn, new))
    if base:
        print("index.json: %s" % INDEX_PATH)


if __name__ == "__main__":
    main()
