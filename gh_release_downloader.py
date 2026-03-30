import os
import re
import json
import requests

CONFIG_FILE = "data.json"
VERSION_FILE = "last_version.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_releases(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else []

def find_latest(releases, include_pre):
    for rel in releases:
        if not include_pre and rel["prerelease"]:
            continue
        if rel.get("assets"):
            return rel
    return None

def download(asset, save_dir):
    name = asset["name"]
    url = asset["browser_download_url"]
    path = os.path.join(save_dir, name)
    print(f"下载: {name}")
    with requests.get(url, stream=True) as r:
        with open(path, "wb") as f:
            f.write(r.content)

def load_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_version(tag):
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"tag": tag}, f, indent=2)

if __name__ == "__main__":
    cfg = load_config()
    repo = cfg["repo"]
    save_dir = cfg["save_dir"]
    pattern = cfg["include_pattern"]
    pre = cfg["include_pre_release"]

    os.makedirs(save_dir, exist_ok=True)

    releases = get_releases(repo)
    latest = find_latest(releases, pre)
    if not latest:
        print("无版本")
        exit(1)

    tag = latest["tag_name"]
    last = load_version()

    if last and last.get("tag") == tag:
        print(f"✅ 已是最新版: {tag}")
        exit(0)

    print(f"🚀 新版本: {tag}")

    # 🔥 正则匹配文件名
    regex = re.compile(pattern)
    for asset in latest["assets"]:
        if regex.match(asset["name"]):
            download(asset, save_dir)

    save_version(tag)
    print("✅ 完成")
