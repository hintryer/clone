import os
import json
import requests

# ==================== 你的原有基础配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "netconfig.json")

def load_config(file_path=CONFIG_FILE):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except (json.JSONDecodeError, ValueError):
        return []

# ==================== 你要求添加的下载函数 ====================
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

# ==================== .NET 版本获取核心 ====================

def get_dotnet_releases_index():
    url = "https://raw.githubusercontent.com/dotnet/core/main/release-notes/releases-index.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("releases-index", [])
    except Exception:
        return []

def get_dotnet_latest_release(channel_version):
    indexes = get_dotnet_releases_index()
    for item in indexes:
        if item.get("product") == ".NET" and item.get("channel-version") == channel_version:
            return item.get("latest-release", "")
    return ""

def build_dotnet_download_url(version):
    return (
        f"https://builds.dotnet.microsoft.com/dotnet/Runtime/"
        f"{version}/dotnet-runtime-{version}-win-x64.exe"
    )

def get_dotnet_updated_info(config):
    channel = config["channel"]
    version = get_dotnet_latest_release(channel)
    if not version:
        return None

    download_url = build_dotnet_download_url(version)
    asset_filename = f"dotnet-runtime-{version}-win-x64.exe"

    print(f"✅ 获取成功：.NET Runtime {channel} → {version}")
    
    return {
        "repo": f".NET Runtime {channel}",
        "save_dir": config["save_dir"],
        "last_version": version,
        "asset_filename": asset_filename,
        "download_url": download_url,
        "filesize": 0,
        "channel": channel
    }

# ==================== 检查更新 + 下载 ====================
def check_and_update(cfg, new_info):
    old_version = cfg["last_version"]
    last_version = new_info["last_version"]
    download_url = new_info["download_url"]
    asset_filename = new_info["asset_filename"]
    save_dir = new_info["save_dir"]

    current_file = os.path.join(save_dir, asset_filename)
    old_file = os.path.join(save_dir, cfg.get("asset_filename", ""))

    print(f"当前版本: {old_version} → 最新版本: {last_version}")

    if last_version == old_version:
        if os.path.exists(current_file):
            print("✅ 已是最新版本\n")
        else:
            print("⚠️ 文件丢失，重新下载...")
            download_file(download_url, save_dir, asset_filename)
        return False

    # 下载新版本
    print("🔽 开始下载新版本...")
    success = download_file(download_url, save_dir, asset_filename)

    if success:
        if os.path.exists(old_file) and old_file != current_file:
            try:
                os.remove(old_file)
                print("🗑️ 已删除旧文件")
            except:
                pass
        print("✅ 更新成功\n")
    return success

# ==================== 主函数 ====================
def main():
    config_list = load_config()
    for cfg in config_list:
        print(f"\n=============== 🚀 检查 .NET 运行时更新 ===============")
        new_info = get_dotnet_updated_info(cfg)
        if new_info:
            check_and_update(cfg, new_info)
            cfg.update(new_info)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_list, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
    print("✅ 全部完成")
