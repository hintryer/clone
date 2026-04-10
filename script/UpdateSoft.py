import os
import json
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import urllib3
import zipfile

from updatemode import  load_config
from updatemode import  save_config
from updatemode import  download_file
from updatemode import  check_and_update

# 关闭SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 浏览器伪装
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://www.baidu.com",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def extract_exe(zip_path, pattern=".*\\.exe$", new_name=None):
    import os
    import zipfile
    import re

    if not os.path.exists(zip_path):
        print(f"❌ 压缩包不存在")
        return ""

    extract_dir = os.path.dirname(zip_path)
    extract_dir = os.path.normpath(extract_dir)
    final_name = ""

    try:
        # Windows 中文 ZIP 兼容
        with zipfile.ZipFile(zip_path, "r", metadata_encoding="gbk") as zf:
            regex = re.compile(pattern, re.IGNORECASE)

            for filename in zf.namelist():
                # 跳过文件夹
                if filename.endswith(("/", "\\")):
                    continue

                # 匹配 EXE 文件
                if regex.search(filename):
                    # 直接读取并写入，不移动、不重命名！！！
                    if new_name is None:
                        final_name = os.path.basename(filename)
                    else:
                        final_name = new_name

                    target_path = os.path.join(extract_dir, final_name)
                    target_path = os.path.normpath(target_path)

                    # 🔥 最安全方式：直接从ZIP读取 → 写入文件，永不报错
                    with zf.open(filename) as fsrc, open(target_path, "wb") as fdst:
                        fdst.write(fsrc.read())

                    print(f"✅ 已提取：{final_name}")
                    break

    except Exception as e:
        print(f"❌ 解压异常：{e}")
        final_name = ""

    # 删除压缩包
    try:
        os.remove(zip_path)
    except:
        pass

    return final_name


# ==============================
# 获取软件最新信息
# ==============================
def get_soft_info(config):
    urlid = config["urlid"]
    save_dir = config["save_dir"]
    target_url = f"https://www.downkuai.com/soft/{urlid}.html"

    try:
        response = requests.get(target_url, headers=HEADERS, timeout=15, verify=False)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        info_list = soup.find("ul", class_="gm_sumList")
        spa_spans =info_list.find_all("span")
        version = spa_spans[0].get_text(strip=True) if len(spa_spans)>=1 else "未知"
        size    = spa_spans[1].get_text(strip=True) if len(spa_spans)>=2 else "未知"
        date    = spa_spans[2].get_text(strip=True) if len(spa_spans)>=3 else "未知"
        
        name_list = soup.find("div", id="con_tit")
        name = name_list.get_text(strip=True) if name_list else "未知"
        
        dl_tag = soup.find("dl", class_="pt_dwload bdxz")
        first_download = ""
        if dl_tag:
            a_tag = dl_tag.find("a")
            if a_tag:
                first_download = a_tag.get("href", "")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.downkuai.com/"
        }
        real_url = ""
        if first_download:
            res = requests.get(first_download, headers=headers, allow_redirects=False, timeout=8, verify=False)
            real_url = res.headers.get("Location", "")
        
        return {
            "urlid": urlid,
            "filename": name + ".zip",
            "version": version,
            "date": date,
            "filesize": size,
            "download_link": real_url,
            "save_dir": save_dir
        }

    except Exception as e:
        print(f"爬取失败: {str(e)}")
        return None

# ==============================
# 主程序
# ==============================
def main():
    config_list = load_config('softconfig.json')

    for cfg in config_list:
        print(f"\n=============== 🚀 检查更新：{cfg['filename']} ===============")
        try:
            new_info = get_soft_info(cfg)
            if new_info:

                dl_ok=check_and_update(cfg, new_info)
                
                if dl_ok:
                    new_info["filename"]=extract_exe(os.path.join(new_info["save_dir"], new_info["filename"]))
                    cfg.update(new_info)
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")

    save_config(config_list)

if __name__ == "__main__":
    main()
    print("\n✅ 全部完成")
 
