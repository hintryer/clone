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
        download_link = page.get_attribute("a#online", "href")
        version      = page.inner_text("#right-info div:has-text('版本') + div").split()[0]
        update_date  = page.inner_text("#right-info div:has-text('更新日期') + div").split("\n")[0]

        print("版本:", version)
        print("更新日期:", update_date)
        print("下载链接:", download_link)
        
        browser.close()
        return download_link

# --- 调用 ---
if __name__ == "__main__":
    target_url = "https://www.crxsoso.com/webstore/detail/bpoadfkcbjbfhfodiogcnhhhpibjhbnh"
    link = get_crx_download_url(target_url)
    print("✅ 下载链接：")
    print(link)
