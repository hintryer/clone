from playwright.sync_api import sync_playwright

def get_crx_download_url(url):
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问页面
        page.goto(url)
        page.wait_for_selector('a#online', timeout=10000)  # 自动等待按钮出现
        
        # ✅ 提取下载链接（你要的核心）
        download_link = page.get_attribute('a#online', 'download')
        
        browser.close()
        return download_link

# --- 调用 ---
if __name__ == "__main__":
    target_url = "https://www.crxsoso.com/webstore/detail/bpoadfkcbjbfhfodiogcnhhhpibjhbnh"
    link = get_crx_download_url(target_url)
    print("✅ 下载链接：")
    print(link)
