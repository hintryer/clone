import requests
import json
import re
import csv
from time import sleep

def get_ext_info(extension_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://chrome.google.com/"
    }

    url = f"https://chromewebstore.google.com/detail/{extension_id}"
    
    try:
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15)
        html = resp.text

        # 最新可用的解析规则（2026 最新）
        match = re.search(r'"fileSize":\s*(\d+)', html)
        if not match:
            match = re.search(r'fileSize\\":(\d+)', html)
            
        version_match = re.search(r'"version":"([^"]+)"', html)
        name_match = re.search(r'"name":"([^"]+)"', html)
        update_match = re.search(r'"lastUpdated":"([^"]+)"', html)

        size_bytes = int(match.group(1)) if match else 0
        version = version_match.group(1) if version_match else "未知"
        name = name_match.group(1) if name_match else "未知"
        last_updated = update_match.group(1) if update_match else "未知"

        size_mb = round(size_bytes / 1024 / 1024, 2)

        return {
            "id": extension_id,
            "name": name,
            "version": version,
            "size_mb": size_mb,
            "last_updated": last_updated,
            "store_url": url,
            "download_url": f"https://clients2.google.com/service/update2/crx?response=redirect&x=id%3D{extension_id}%26uc",
            "error": ""
        }

    except Exception as e:
        return {
            "id": extension_id,
            "name": "",
            "version": "",
            "size_mb": "",
            "last_updated": "",
            "store_url": "",
            "download_url": "",
            "error": f"获取失败: {str(e)}"
        }


def batch_query_and_save(ext_ids, filename="extension_info.csv"):
    results = []
    for i, ext_id in enumerate(ext_ids, 1):
        print(f"[{i}/{len(ext_ids)}] 查询中: {ext_id}")
        info = get_ext_info(ext_id)
        results.append(info)
        sleep(1.5)

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "name", "version", "size_mb", "last_updated", "store_url", "download_url", "error"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ 全部完成！已导出到: {filename}")


if __name__ == "__main__":
    # 你要查询的扩展ID
    EXT_ID_LIST = [
        "gcalenpjmijncebpfiojcommlgcdbibn",
        "cjpalhdlnbpafiamejdnhcphjbkeiagm",
        "bgnkhhnnamicmpeenaelnandbfafkfpb"
    ]

    batch_query_and_save(EXT_ID_LIST)
