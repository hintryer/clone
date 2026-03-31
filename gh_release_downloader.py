import os
import re
import json
import requests
from jsonpath import JSONPath


CONFIG_FILE = "data.json"
VERSION_FILE = "last_version.json"

def load_config(file_path="data.json"):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except (json.JSONDecodeError, ValueError):
        return {}

def get_releases(repo):
    # 请求头（防拦截、兼容 GitHub Actions）
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/octet-stream, */*",
        "Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"
    }

    url = f"https://api.github.com/repos/{repo}/releases"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ 获取 Releases 失败：{response.status_code}")
            return []

        releases = response.json()

    except Exception as e:
        print(f"❌ 获取发布信息失败: {str(e)}")
        return []

    return releases
    
def get_by_tagname(releases, regex=".*", index=0):
    # 拼接 JSONPath 表达式
    path = f"$..[?(@.tag_name =~ /{regex}/)].tag_name"
    # 执行查询
    result = JSONPath(path).parse(releases)
    # 安全取值
    result2 = result[index] if len(result) > index else None
    return result2
    
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
    print(latest)
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
