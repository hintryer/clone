import os
import json
import requests

def load_config(file_path="config.json"):
    """加载配置文件，安全容错"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(base_dir, file_path)
    
    if not os.path.exists(config_file_path):
        return []
    try:
        with open(config_file_path, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except (json.JSONDecodeError, ValueError):
        return []

def save_config(config_list, file_path="config.json"):
    """保存配置到 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config_list, f, ensure_ascii=False, indent=2)

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

def get_file_size_mb(file_path: str) -> float:
    """
    获取文件大小，单位为MB
    文件不存在/非文件，返回0.0
    """
    if not os.path.isfile(file_path):
        return 0.0
    # 字节转换为MB
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 ** 2)
    # 保留两位小数
    return round(size_mb, 2)


def check_and_update(old_info, new_info):
    old_version = old_info.get("version", "")
    new_version = new_info.get("version", "")
    download_url = new_info.get("download_link", "")
    save_dir = new_info.get("save_dir", "./download")
    filename = new_info.get("filename", "")
    old_filename = old_info.get("filename") or filename
    old_file_path = os.path.join(save_dir, old_filename)
    
    current_file_path = os.path.join(save_dir, filename)
    
    MAX_SIZE_MB = 100

    print(f"当前版本: {old_version} → 最新版本: {new_version}")

    if new_version == old_version:
        if os.path.exists(old_file_path):
            print("✅ 已是最新版本")
            return False
        else:
            print("⚠️ 文件丢失，重新下载...")
            return download_file(download_url, save_dir, filename)
    else:
        print(f"📦 开始更新：{filename}")

        # 先下载
        dl_ok = download_file(download_url, save_dir, filename)
        
        # 再获取文件大小
        file_mb = get_file_size_mb(current_file_path)
        is_file_too_big = file_mb > MAX_SIZE_MB

        if dl_ok:
            if not is_file_too_big:
                # 文件不大 → 删除旧文件
                if os.path.exists(old_file_path) and old_file_path != current_file_path:
                    try:
                        os.remove(old_file_path)
                        print("🗑️ 已删除旧文件")
                    except Exception:
                        pass
                print("✅ 更新成功")
            else:
                print(f"⚠️ 文件过大({file_mb:.2f}MB)")

        return dl_ok
    
def main():
    print('test')
if __name__ == "__main__":
    main()
