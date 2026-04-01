import os
import re
import json
import requests
from jsonpath import JSONPath

CONFIG_FILE = "config.json"
INFO_FILE = "data.json"

def load_config(file_path="config.json"):
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
    
# 根据 tag_name 获取 一个 release（已排除 prerelease）
def get_release_by_tag(releases, pattern=".*", index=0):
    """
    根据 tag_name 正则匹配 + 排除 prerelease
    返回单个完整的 release 对象（dict）
    自带异常捕获，任何错误均返回 None
    """
    try:
        # 核心修改：这里同时满足 2 个条件
        # 1. tag_name 匹配正则
        # 2. prerelease == false（排除预览版）
        path2 = f"$..[?(@.prerelease == false)]"
        releases2 = JSONPath(path2).parse(releases)
        print(releases2)
        path = f"$..[?(@.tag_name =~ /{pattern}/)]"
        result = JSONPath(path).parse(releases2)
        return result[index] if (result and len(result) > index) else None

    except Exception:
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

def get_updated_info(config):
    """
    传入配置项 config
    返回 最新版本信息字典（结构和 config 完全一致）
    自动排除 prerelease
    """
    repo = config["repo"]
    tagregex = config["tagregex"]
    assetregex = config["assetregex"]

    # 获取 GitHub 数据
    data = get_releases(repo)
    release = get_release_by_tag(data, tagregex)
    
    if not release:
        print(f"❌ 未找到正式版: {repo}")
        return None
    
    target_asset = get_asset_by_name(release, assetregex)
    if not target_asset:
        print(f"❌ 未找到匹配文件: {repo}")
        return None

    # 解析信息
    last_version = get_first_value(release, '$..tag_name')
    asset_filename = get_first_value(target_asset, '$.name')
    download_url = get_first_value(target_asset, '$.browser_download_url')
    print(f"✅ 获取成功：{repo} → {last_version}") 
    # 返回结构 = 和 config 完全一样！
    return {
        "repo": repo,
        "save_dir": config["save_dir"],
        "tagregex": tagregex,
        "assetregex": assetregex,
        "last_version": last_version,
        "asset_filename": asset_filename,
        "download_url": download_url
    }

def main():
    # 1. 读取配置
    config_list = load_config()
    
    # 2. 遍历每一个配置并更新
    for cfg in config_list:
        print(f"【检查更新】{cfg['repo']}")
        old_version = cfg["last_version"]
        new_info = get_updated_info(cfg)

        if not new_info:
            continue  # 获取失败则跳过

        last_version = new_info["last_version"]
        download_url = new_info["download_url"]
        asset_filename = new_info["asset_filename"]
        save_dir = new_info["save_dir"]

        print(last_version)
        # 版本不同 → 下载 + 更新
        if last_version != old_version:
            print(f"【更新】{cfg['repo']} | {old_version} → {last_version}")
            download_file(download_url, save_dir, asset_filename)

            # 直接用 new_info 覆盖 cfg ✅
            cfg.update(new_info)

    # 保存回文件
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config_list, f, ensure_ascii=False, indent=2)
        
def main2():
    data = get_releases('lalakii/MouseClickTool')
    release = get_release_by_tag(data, tagregex)
if __name__ == "__main__":
    main2()
    print("✅ 完成")
