from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

def crawl_dynamic_page(url,target_xpath):
    """
    提取指定XPATH的所有元素文字，增强容错和调试能力
    :param url: 目标网页URL
    :return: 包含元素文字列表的字典
    """
    # 初始化返回结果
    result = {"elem_texts": []}
    
    # 1. 配置浏览器
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")  # 新增：解决系统权限问题
    chrome_options.add_argument("--disable-dev-shm-usage")  # 新增：解决内存不足问题
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = None
    try:
        # 2. 启动浏览器（增加异常捕获）
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        print(f"✅ 浏览器启动成功，开始访问URL：{url}")

        # 3. 访问页面并等待渲染（延长等待时间，增加日志）
        driver.get(url)
        wait_time = 8  # 延长至8秒，适配JS慢渲染
        print(f"⌛ 等待{wait_time}秒，让页面JS完全渲染...")
        time.sleep(wait_time)

        # 4. 保存渲染后的HTML（调试用，关键！）
        rendered_html = driver.page_source
        print(rendered_html)
        # 5. 提取所有符合XPATH的元素文字
        target_elems = driver.find_elements(By.XPATH, target_xpath)
        
        # 打印定位结果日志
        print(f"🔍 定位到 {len(target_elems)} 个符合XPATH的元素")
        
        if target_elems:
            for idx, elem in enumerate(target_elems, 1):
                # 兼容隐藏元素：优先用innerText，再用text
                elem_text = elem.get_attribute('innerText').strip() or elem.text.strip()
                if elem_text:
                    result["elem_texts"].append(elem_text)
                    print(f"✅ 第{idx}个元素文字：{elem_text[:50]}..." if len(elem_text) > 50 else f"✅ 第{idx}个元素文字：{elem_text}")
            print(f"\n📊 最终提取到 {len(result['elem_texts'])} 个非空的元素文字")
        else:
            print("⚠️ 未找到任何符合该XPATH的元素")
            
    except Exception as e:
        print(f"❌ 抓取过程出错：{str(e)}")
        import traceback
        traceback.print_exc()  # 输出详细错误栈，方便排查

    finally:
        if driver:
            driver.quit()

    return result

# 调用函数
if __name__ == "__main__":
    target_url = "https://www.crxsoso.com/webstore/detail/bpoadfkcbjbfhfodiogcnhhhpibjhbnh"
    target_xpath='//a[@id="online"]/@href'
    result = crawl_dynamic_page(target_url,target_xpath)
    
    # 输出最终结果
    print(f"\n========== 最终提取结果 ==========")
    print(f"📝 符合XPATH的元素文字（共{len(result['elem_texts'])}条）：")
    if result['elem_texts']:
        for idx, text in enumerate(result['elem_texts'], 1):
            print(f"{idx}. {text}")
    else:
        print("（未提取到任何元素文字）")
