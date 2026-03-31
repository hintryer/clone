import os
import re
import json
import requests
from jsonpath import JSONPath

current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "releases.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
print("读取成功！文件内容：")


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

def download_file(url, save_dir, filename):
    """
    下载文件到指定目录
    :param url: 下载链接
    :param save_dir: 保存目录
    :param filename: 保存的文件名
    """
    if not url or not filename:
        print("下载失败：未获取到有效链接或文件名")
        return False

    try:
        # 自动创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        
        print(f"开始下载: {filename}")
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"下载完成: {filename}\n")
        return True

    except Exception as e:
        print(f"下载失败: {filename} | 错误: {str(e)}")
        return False

# 安全提取字符串
def get_first_value(obj, path):
    try:
        res = JSONPath(path).parse(obj)
        return res[0] if res else None
    except:
        return None
def main():
    cfg = load_config()
    repo = cfg["repo"]
    save_dir = cfg["save_dir"]

    data=get_releases(repo)

    release = get_release_by_tag(data)
    target_asset = get_asset_by_name(release, 'MouseClickTool.exe')
    
    # 直接获取字符串
    repo_name = get_first_value(release, '$.name')
    last_version = get_first_value(release, '$..tag_name')
    asset_filename = get_first_value(target_asset, '$.name')
    download_url = get_first_value(target_asset, '$.browser_download_url')

    download_file(download_url, save_dir, asset_filename)

if __name__ == "__main__":
    main()
    print("✅ 完成")
