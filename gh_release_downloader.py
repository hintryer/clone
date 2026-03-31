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
    
# 根据 tag_name 获取 一个 release
def get_release_by_tag(releases, pattern=".*", index=0):
    """
    根据 tag_name 正则匹配，返回单个完整的 release 对象（dict）
    自带异常捕获，任何错误均返回 None
    """
    try:
        path = f"$..[?(@.tag_name =~ /{pattern}/)]"
        result = JSONPath(path).parse(releases)
        return result[index] if (result and len(result) > index) else None

    except (TypeError, AttributeError, IndexError, Exception):
        return None

# 根据 name 获取 一个 asset
def get_asset_by_name(release, pattern=".*", index=0):
    """
    从单个 release 中，根据 asset.name 正则匹配，返回单个 asset 对象（dict）
    自带异常捕获，任何错误均返回 None
    """
    try:
        if not isinstance(release, (dict, list)):
            return None

        path = f"$.assets..[?(@.name =~ /{pattern}/)]"
        result = JSONPath(path).parse(release)
        return result[index] if (result and len(result) > index) else None

    except (TypeError, AttributeError, IndexError, Exception):
        return None


def find_latest(releases, include_pre):
    for rel in releases:
        if not include_pre and rel["prerelease"]:
            continue
        if rel.get("assets"):
            return rel
    return None

def download_file(url, save_dir, filename):
    """
    下载文件到指定目录
    :param url: 下载链接
    :param save_dir: 保存目录
    :param filename: 保存的文件名
    """
    try:
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 拼接完整保存路径
        save_path = os.path.join(save_dir, filename)
        
        print(f"开始下载: {filename}")
        
        # 流式下载（大文件不占内存）
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()  # 抛出 HTTP 错误
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"下载完成: {filename}\n")
        return True

    except Exception as e:
        print(f"下载失败: {filename} | 错误: {str(e)}")
        return False
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
    data=get_releases(repo)
    # 1. 获取匹配的发布版本（默认第一个）
    release = get_release_by_tag(data)
    
    # 2. 从 release 中提取信息
    repo_name      = JSONPath('$.name').parse(release)               # 仓库名
    last_version   = JSONPath('$..tag_name').parse(release)         # 最新版本号
    
    # 3. 获取指定文件的 asset
    target_asset   = get_asset_by_name(release, 'MouseClickTool.exe')
    
    # 4. 从 asset 中提取信息
    asset_filename = JSONPath('$.name').parse(target_asset)         # 文件名
    download_url   = JSONPath('$.browser_download_url').parse(target_asset)  # 下载链接

    # 安全取值（列表 → 字符串）
    final_filename = asset_filename[0] if asset_filename else None
    final_url      = download_url[0] if download_url else None
    
    # 只有都不为空才下载
    if final_url and final_filename:
        download_file(final_url, save_dir, final_filename)
    else:
        print("下载失败：未获取到有效链接或文件名")
    print(download_url)
    print("✅ 完成")
