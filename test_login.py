import asyncio
from playwright.async_api import async_playwright
import time

async def test_login():
    """测试登录功能"""
    login_url = "https://upass.10jqka.com.cn/login"
    
    try:
        async with async_playwright() as p:
            # 启动浏览器
            print("正在启动浏览器...")
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=50
            )
            
            # 创建新页面
            page = await browser.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            
            # 访问登录页面
            print(f"正在访问登录页面: {login_url}")
            response = await page.goto(login_url, wait_until="networkidle", timeout=60000)
            print(f"响应状态: {response.status}")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 打印当前URL
            print(f"当前URL: {page.url}")
            
            # 打印页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 打印页面内容预览
            content = await page.content()
            print(f"页面内容预览: {content[:500]}...")
            
            # 等待用户输入
            input("请在浏览器中完成登录后，按回车键继续...")
            
            # 打印登录后的URL
            print(f"登录后URL: {page.url}")
            
            # 关闭浏览器
            await browser.close()
            print("测试完成！")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    time.sleep(2)
    asyncio.run(test_login())
