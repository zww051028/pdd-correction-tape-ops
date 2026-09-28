#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 GitHub Contents API 上传文件（绕过 git 传输）"""
import base64
import json
import os
import sys
import time
import urllib.request

TOKEN = os.environ.get("GH_TOKEN", "").strip()
OWNER = "zww051028"
REPO = "pdd-correction-tape-ops"
SRC = r"D:\workbuddy-github"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

if not TOKEN:
    print("ERROR: GH_TOKEN 未设置")
    sys.exit(1)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "python-uploader")
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")
    except Exception as e:
        return 0, {"message": str(e)}


# 收集所有要上传的文件（跳过 .git）
files = []
for root, dirs, names in os.walk(SRC):
    dirs[:] = [d for d in dirs if d != ".git"]
    for n in names:
        full = os.path.join(root, n)
        rel = os.path.relpath(full, SRC).replace("\\", "/")
        files.append((rel, full))

files.sort()
print(f"待上传 {len(files)} 个文件\n")

ok, fail = 0, 0
for rel, full in files:
    with open(full, "rb") as f:
        content = base64.b64encode(f.read()).decode("ascii")

    # 检查文件是否已存在（需要 sha 才能更新）
    status, info = api("GET", f"{API}/{rel}")
    payload = {"message": f"upload {rel}", "content": content}
    if status == 200 and "sha" in info:
        payload["sha"] = info["sha"]

    status, info = api("PUT", f"{API}/{rel}", payload)
    if status in (200, 201):
        print(f"  OK   {rel}")
        ok += 1
    else:
        print(f"  FAIL {rel}  -> {status}: {info.get('message')}")
        fail += 1
    time.sleep(0.3)

print(f"\n完成：成功 {ok} / 失败 {fail}")
