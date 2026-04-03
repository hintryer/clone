from playwright.sync_api import sync_playwright

def get_crx_download_url(url):
    with sync_playwright() as p:
        # 🔥 Linux / GitHub Actions 必须加这些启动参数！
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
        page.goto(url, timeout=60000)
        page.wait_for_selector('a#online', timeout=15000)

        # 1. 提取版本号
        version = page.locator('.detail-info li:has-text("版本") span').text_content().strip()
        print("版本：", version)

        # 2. 提取更新日期
        update_date = page.locator('.detail-info li:has-text("更新时间") span').text_content().strip()
        print("更新日期：", update_date)

        # 3. 提取下载链接（正确用 href）
        download_link = page.get_attribute("a#online", "href")

        browser.close()
        return download_link

# --- 调用 ---
if __name__ == "__main__":
    target_url = "https://www.crxsoso.com/webstore/detail/bpoadfkcbjbfhfodiogcnhhhpibjhbnh"
    link = get_crx_download_url(target_url)
    print("✅ 下载链接：")
    print(link)
