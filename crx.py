import os
import json
import requests
import urllib.parse
from playwright.sync_api import sync_playwright
import subprocess  # 用于自动安装

# ==============================================
# 🔥 核心：Python 内部自动安装 Playwright 浏览器
# ==============================================
def install_playwright_browser():
    try:
        print("🔧 检查 Playwright 浏览器...")
        # 自动安装 chromium（Linux 会自动装依赖）
        subprocess.run(
            ["playwright", "install", "--with-deps", "chromium"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Playwright 浏览器准备完成")
    except Exception:
        pass

# 启动时自动安装
install_playwright_browser()

CONFIG_FILE = "crxconfig.json"

def load_config(file_path=CONFIG_FILE):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except (json.JSONDecodeError, ValueError):
        return []

def download_file(url, save_dir, filename):
    if not url or not filename:
        print("下载失败：未获取到有效链接或文件名")
        return False

    try:
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        
        print(f"开始下载: {filename}")
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"下载完成: {filename}\n")
        return True

    except Exception as e:
        print(f"下载失败: {filename} | 错误: {str(e)}")
        return False

def get_crxupdated_info(config):
    urlid = config["urlid"]
    save_dir = config["save_dir"]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )
        page = browser.new_page()
        target_url = f"https://www.crxsoso.com/webstore/detail/{urlid}"
        
        page.goto(target_url, timeout=60000)
        page.wait_for_selector('#right-info', timeout=15000)

        # 下载链接
        download_link = page.get_attribute("a#online", "href")
        download_link = download_link.replace("type=install", "type=dl")

        # 版本
        version = page.inner_text("#right-info div:has-text('版本') + div").split()[0]

        # 更新日期
        update_date = page.locator("#right-info div:has-text('更新日期') + div").text_content().strip()
        update_date = update_date.split()[0]

        # 文件名解码
        key = "filename="
        start = download_link.find(key) + len(key)
        end = download_link.find("&type=")
        encoded_name = download_link[start:end]
        filename = urllib.parse.unquote(encoded_name).strip()

        # 文件大小（MB）
        size_text = page.inner_text("#right-info div:has-text('大小') + div").strip().upper()
        size_num = float(''.join([c for c in size_text if c.isdigit() or c == '.']))
        
        if "KIB" in size_text:
            size_mb = size_num / 1024  # KiB → MiB
        elif "MIB" in size_text:
            size_mb = size_num          # 已经是 MiB
        else:
            size_mb = 0.0

        browser.close()

        return {
            "urlid": urlid,
            "filename": filename,
            "version": version,
            "update_date": update_date,
            "download_link": download_link,
            "filesize": size_mb,
            "save_dir": save_dir
        }

def check_and_update(cfg, new_info):
    old_version = cfg.get("version", "")
    last_version = new_info["version"]
    download_url = new_info["download_link"]
    asset_filename = new_info["filename"]
    save_dir = new_info["save_dir"]
    filesize = new_info["filesize"]

    current_file_path = os.path.join(save_dir, asset_filename)
    old_file_path = os.path.join(save_dir, cfg.get("filename", ""))

    MAX_SIZE_MB = 100
    is_file_too_big = filesize > MAX_SIZE_MB

    print(f"当前版本: {old_version} → 最新版本: {last_version}")
    if is_file_too_big:
        print(f"⚠️ 文件过大({filesize:.2f}MB)，仅更新版本信息")

    # 版本相同
    if last_version == old_version:
        if os.path.exists(current_file_path) or is_file_too_big:
            print("✅ 已是最新版本")
            return False
        else:
            print("⚠️ 文件丢失，重新下载...")
            return download_file(download_url, save_dir, asset_filename)

    # 需要更新
    dl_ok = True
    if not is_file_too_big:
        dl_ok = download_file(download_url, save_dir, asset_filename)
        if dl_ok:
            if os.path.exists(old_file_path) and old_file_path != current_file_path:
                try:
                    os.remove(old_file_path)
                    print("🗑️ 已删除旧文件")
                except:
                    pass
            print("✅ 更新成功")
    else:
        print("✅ 版本信息已更新（文件过大未下载）")

    return dl_ok

def main():
    config_list = load_config()
    if not config_list:
        print("❌ 配置文件为空或不存在")
        return

    for cfg in config_list:
        print(f"\n=============== 🚀 检查更新：{cfg['filename']} ===============")
        try:
            new_info = get_crxupdated_info(cfg)
            check_and_update(cfg, new_info)
            cfg.update(new_info)
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_list, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
    print("\n✅ 全部完成")
