from playwright.sync_api import sync_playwright

def get_crx_download_url(url):
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问页面
        page.goto(url)
        page.wait_for_selector('a#online', timeout=10000)  # 自动等待按钮出现
        
        # 1. 提取版本号（定位：版本标签后的文本）
        version = page.locator('.detail-info li:has-text("版本") span').text_content().strip()
        print(version)
        # 2. 提取更新日期（定位：更新时间标签后的文本）
        update_date = page.locator('.detail-info li:has-text("更新时间") span').text_content().strip()
        print(update_date)
        # 3. 提取下载链接
        download_link = page.get_attribute("a#online", "download")
        
        browser.close()
        return download_link

# --- 调用 ---
if __name__ == "__main__":
    target_url = "https://www.crxsoso.com/webstore/detail/bpoadfkcbjbfhfodiogcnhhhpibjhbnh"
    link = get_crx_download_url(target_url)
    print("✅ 下载链接：")
    print(link)
