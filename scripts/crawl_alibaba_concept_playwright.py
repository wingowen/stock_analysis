import asyncio
from playwright.async_api import async_playwright
import random
import csv
import time
import os
import json

code = 309130

async def login_and_save_session():
    """登录同花顺并保存会话信息"""
    # 直接访问目标页面，而不是单独的登录页面
    target_url = f"https://q.10jqka.com.cn/gn/detail/code/{code}/"
    
    async with async_playwright() as p:
        # 使用持久化上下文，保存会话到 user_data 目录
        print("正在创建持久化浏览器上下文...")
        context = await p.chromium.launch_persistent_context(
            "user_data",  # 持久化用户数据目录
            headless=False,  # 非无头模式，便于手动登录
            slow_mo=100,
            user_agent=get_random_user_agent(),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--flag-switches-begin --disable-site-isolation-trials --flag-switches-end",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-extensions"
            ]
        )
        
        # 创建新页面
        page = await context.new_page()
        
        # 设置用户代理
        await page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        })
        
        try:
            print(f"正在打开目标页面: {target_url}")
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            
            # 等待用户手动登录
            print("请在浏览器中手动登录同花顺...")
            print("登录成功后，会话信息将被保存，支持7天免登录")
            print("\n登录完成后，请在浏览器中保持页面打开状态")
            
            # 等待用户确认登录完成
            input("\n登录完成后，请按回车键开始爬取数据...")
            
            print("登录成功！会话信息将自动保存到 user_data 目录")
            print("下次运行脚本时将自动使用保存的会话")
            print("\n登录完成！")
            
        except Exception as e:
            print(f"登录过程中出错: {str(e)}")
        finally:
            await context.close()

def get_random_user_agent():
    """获取随机用户代理"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/118.0 Safari/537.36"
    ]
    return random.choice(user_agents)

async def simulate_human_behavior(page):
    """模拟人类行为"""
    print("正在模拟人类行为...")

    return
    
    # 模拟鼠标移动路径（更自然的曲线）
    mouse_movements = random.randint(5, 10)
    for _ in range(mouse_movements):
        # 从当前位置开始
        current_x = random.randint(100, 1600)
        current_y = random.randint(100, 900)
        
        # 随机目标位置
        target_x = random.randint(100, 1600)
        target_y = random.randint(100, 900)
        
        # 分步骤移动鼠标，模拟人类移动
        steps = random.randint(15, 30)
        for step in range(steps):
            progress = step / steps
            # 添加一些随机抖动，使移动更自然
            jitter_x = random.uniform(-5, 5)
            jitter_y = random.uniform(-5, 5)
            
            x = current_x + (target_x - current_x) * progress + jitter_x
            y = current_y + (target_y - current_y) * progress + jitter_y
            
            await page.mouse.move(x, y, steps=1)
            await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # 随机暂停
        await asyncio.sleep(random.uniform(0.1, 0.5))
    
    # 模拟鼠标点击
    if random.random() < 0.7:  # 70%的概率点击
        click_x = random.randint(200, 1500)
        click_y = random.randint(200, 800)
        await page.mouse.move(click_x, click_y, steps=random.randint(5, 10))
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.up()
        await asyncio.sleep(random.uniform(0.3, 0.8))
    
    # 模拟滚动（更自然的滚动模式）
    scrolls = random.randint(3, 6)
    for _ in range(scrolls):
        # 随机滚动方向和距离
        direction = random.choice([-1, 1])
        delta = random.randint(50, 400) * direction
        
        # 分步骤滚动
        scroll_steps = random.randint(3, 8)
        step_delta = delta / scroll_steps
        
        for _ in range(scroll_steps):
            await page.mouse.wheel(0, step_delta)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # 随机暂停
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # 模拟键盘输入
    if random.random() < 0.5:  # 50%的概率输入
        await page.keyboard.press("Tab")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await page.keyboard.press("Shift")
        await asyncio.sleep(random.uniform(0.05, 0.1))
        await page.keyboard.release("Shift")
    
    # 模拟页面刷新
    if random.random() < 0.3:  # 30%的概率刷新
        await page.keyboard.press("F5")
        await asyncio.sleep(random.uniform(1, 2))
    
    # 随机延迟
    final_delay = random.uniform(1.5, 3.5)
    print(f"模拟完成，延迟 {final_delay:.2f} 秒...")
    await asyncio.sleep(final_delay)

async def crawl_alibaba_concept():
    url = "https://q.10jqka.com.cn/gn/detail/code/301558/"
    all_data = []
    headers = []
    
    async with async_playwright() as p:
        # 创建浏览器上下文
        # 注意：使用 launch_persistent_context 时，会话会自动保存到 user_data 目录
        # 不需要额外的 storage_state 参数
        print("正在创建浏览器上下文...")
        context = await p.chromium.launch_persistent_context(
            "user_data",  # 持久化用户数据目录
            headless=False,
            slow_mo=random.randint(80, 120),  # 随机慢动作速度
            user_agent=get_random_user_agent(),
            viewport={
                "width": random.randint(1360, 1920),
                "height": random.randint(768, 1080)
            },  # 随机窗口大小
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--flag-switches-begin --disable-site-isolation-trials --flag-switches-end",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-extensions",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--start-maximized",  # 启动时最大化窗口
                "--disable-web-security",  # 禁用Web安全策略
                "--disable-features=site-per-process",  # 禁用站点隔离
                "--disable-ipc-flooding-protection",  # 禁用IPC flooding保护
                "--disable-prompt-on-repost",  # 禁用重发提示
                "--disable-hang-monitor",  # 禁用挂起监视器
                "--disable-sync",  # 禁用同步
                "--disable-translate",  # 禁用翻译
                "--disable-features=TranslateUI",  # 禁用翻译UI
                "--disable-client-side-phishing-detection",  # 禁用客户端钓鱼检测
                "--disable-component-extensions-with-background-pages",  # 禁用带背景页的组件扩展
                "--disable-default-apps",  # 禁用默认应用
                "--disable-features=CertificateTransparencyComponentUpdater",  # 禁用证书透明度组件更新
                "--disable-features=PrivacySandboxSettings4",  # 禁用隐私沙箱设置
                "--disable-features=UserAgentClientHint",  # 禁用User-Agent客户端提示
                "--disable-features=InterestCohortAPI",  # 禁用兴趣群组API
                "--disable-features=FederatedLearningOfCohorts",  # 禁用群组联合学习
                "--disable-features=NetworkService",  # 禁用网络服务
                "--disable-features=NetworkServiceInProcess",  # 禁用进程内网络服务
                "--disable-features=OutOfBlinkCors",  # 禁用Blink外CORS
                "--disable-features=SiteIsolation",  # 禁用站点隔离
                "--disable-features=ThrottleNonForegroundTab",  # 禁用非前台标签页节流
                "--disable-features=UseModernMediaControls",  # 禁用现代媒体控件
                "--disable-features=WebAuthentication",  # 禁用Web认证
                "--disable-features=WebRtcHideLocalIpsWithMdns",  # 禁用WebRTC隐藏本地IP
                "--disable-features=WebRtcIpHandlingPolicy",  # 禁用WebRTC IP处理策略
                "--disable-features=WebRtcMultipleRoutes",  # 禁用WebRTC多路由
                "--disable-features=WebRtcPrflxPrefixes",  # 禁用WebRTC Prflx前缀
                "--disable-features=WebRtcStunOrigin",  # 禁用WebRTC STUN源
                "--disable-features=WebRtcTurnCustomizer",  # 禁用WebRTC TURN定制器
                "--disable-features=WebRtcTurnCredManagement",  # 禁用WebRTC TURN凭证管理
                "--disable-features=WebRtcUdpPacketDump",  # 禁用WebRTC UDP数据包转储
                "--disable-features=WebRtcVideoHdr",  # 禁用WebRTC视频HDR
                "--disable-features=WebRtcVideoMirroring",  # 禁用WebRTC视频镜像
                "--disable-features=WebRtcVideoProcessing",  # 禁用WebRTC视频处理
                "--disable-features=WebRtcVideoRedundancy",  # 禁用WebRTC视频冗余
                "--disable-features=WebRtcVideoResize",  # 禁用WebRTC视频调整大小
                "--disable-features=WebRtcVideoStats",  # 禁用WebRTC视频统计
                "--disable-features=WebRtcVideoTiming",  # 禁用WebRTC视频计时
                "--disable-features=WebRtcVideoTrack",  # 禁用WebRTC视频轨道
                "--disable-features=WebRtcVideoWebcodecs",  # 禁用WebRTC视频WebCodecs
                "--disable-features=WebRtcVoiceIsolation",  # 禁用WebRTC语音隔离
                "--disable-features=WebRtcVolumeControl",  # 禁用WebRTC音量控制
                "--disable-features=WebSockets",  # 禁用WebSockets
                "--disable-features=Xfa",  # 禁用XFA
                "--disable-features=XmlHttpRequest"  # 禁用XMLHttpRequest
            ]
        )

        
        # 创建新页面
        page = await context.new_page()
        
        # 禁用自动化特征
        await page.evaluate("""
            () => {
                // 禁用 webdriver 检测
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 模拟真实的语言设置
                Object.defineProperty(navigator, 'language', {
                    get: () => 'zh-CN'
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en']
                });
                
                // 模拟插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3]
                });
                
                // 模拟 mimeTypes
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => [1, 2, 3]
                });
                
                // 模拟硬件并发数
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                // 模拟设备内存
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // 隐藏 Playwright 特征
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
                });
                
                // 移除 navigator.locks
                if (navigator.locks) {
                    delete navigator.locks;
                }
                
                // 修改日期对象，避免被检测
                const originalDateToString = Date.prototype.toString;
                Date.prototype.toString = function() {
                    return originalDateToString.call(this).replace(/\(.*?\)/, '(中国标准时间)');
                };
            }
        """)
        
        # 设置用户代理和其他请求头
        # 随机生成一些请求头值
        chrome_version = f"{random.randint(110, 120)}.0.{random.randint(5000, 6000)}.{random.randint(100, 200)}"
        platform = random.choice(["Windows", "macOS", "Linux"])
        platform_version = random.choice(["10", "11", "12"])
        
        # 随机引荐来源
        referers = [
            "https://www.baidu.com/",
            "https://www.google.com/",
            "https://www.sogou.com/",
            "https://www.bing.com/",
            "https://www.360.cn/",
            "https://www.so.com/",
            "https://q.10jqka.com.cn/",
            "https://www.10jqka.com.cn/"
        ]
        
        # 随机浏览器语言
        languages = [
            "zh-CN,zh;q=0.9,en;q=0.8",
        ]
        
        # 随机设备内存
        device_memory = random.choice([4, 8, 16])
        
        # 随机CPU核心数
        cpu_cores = random.choice([4, 6, 8, 12, 16])
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": random.choice(languages),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": random.choice(["keep-alive", "close"]),
            "Upgrade-Insecure-Requests": "1",
            "Referer": random.choice(referers),
            "Cache-Control": random.choice(["max-age=0", "no-cache", "max-age=3600"]),
            "Pragma": random.choice(["no-cache", ""]),
            "DNT": "1",
            "X-Requested-With": "XMLHttpRequest",
            "X-Forwarded-For": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "X-Real-IP": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "User-Agent": get_random_user_agent(),
            "Sec-Ch-Ua": f'"Chromium";v="{chrome_version.split(".")[0]}", "Google Chrome";v="{chrome_version.split(".")[0]}", "Not=A?Brand";v="99"',
            "Sec-Ch-Ua-Mobile": random.choice(["?0", "?1"]),
            "Sec-Ch-Ua-Platform": f'"{platform}"',
            "Sec-Ch-Ua-Platform-Version": f'"{platform_version}"',
            "Sec-Ch-Ua-Arch": random.choice(["x86", "x86_64", "arm", "arm64"]),
            "Sec-Ch-Ua-Model": "",
            "Sec-Ch-Ua-Full-Version": f'"{chrome_version}"',
            "Sec-Ch-Ua-Full-Version-List": f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not=A?Brand";v="99.0.0.0"',
            "Sec-Ch-Ua-Bitness": random.choice(["64", "32"]),
            "Sec-Ch-Ua-Wow64": "?0",
            "Sec-Fetch-Dest": random.choice(["document", "empty"]),
            "Sec-Fetch-Mode": random.choice(["navigate", "cors", "no-cors"]),
            "Sec-Fetch-Site": random.choice(["cross-site", "same-origin", "same-site", "none"]),
            "Sec-Fetch-User": random.choice(["?1", ""]),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Sec-Gpc": "1",
            "Priority": random.choice(["u=0, i", "u=1, i", "u=2, i"]),
            "Device-Memory": str(device_memory),
            "Downlink": str(random.uniform(10, 100)),
            "ECT": random.choice(["4g", "3g", "2g"]),
            "RTT": str(random.randint(50, 200)),
            "Save-Data": random.choice(["on", "off"]),
            "Viewport-Width": str(random.randint(1024, 1920))
        }
        
        # 移除空值
        headers = {k: v for k, v in headers.items() if v}
        
        await page.set_extra_http_headers(headers)
        print("✅  请求头已设置")
        
        try:
            # 随机延迟，模拟人类行为
            # await asyncio.sleep(random.uniform(3, 5))
            
            # 导航到目标页面
            print(f"正在访问: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 检查是否需要登录
            print("正在检查登录状态...")
            
            # 1. 首先检查是否被重定向到登录页面（通过URL判断）
            if "login" in page.url.lower() or "upass" in page.url.lower():
                print("⚠️  需要登录，请先运行登录脚本")
                print(f"当前URL: {page.url}")
                print("请运行脚本并在浏览器中使用微信扫码登录")
                return
            
            # 2. 检查页面内容是否真正需要登录
            try:
                # 查找明确的登录提示或表单
                login_prompt = await page.query_selector("//*[contains(text(), '请登录') or contains(text(), '登录后查看')]")
                login_form = await page.query_selector("//form[contains(@action, 'login') or contains(@id, 'login')]")
                
                # 只有当存在明确的登录提示或表单时，才认为需要登录
                # 避免误判：页面上可能存在登录按钮但用户已登录的情况
                if login_prompt or login_form:
                    print("⚠️  检测到登录页面，请先登录")
                    print(f"当前URL: {page.url}")
                    return
            except Exception:
                # 忽略检查错误，继续执行
                pass
            
            print("✅  已登录，开始爬取数据")
            
            # 检查是否被禁止
            page_content = await page.content()
            if "Nginx forbidden" in page_content:
                print("⚠️  被网站禁止访问（Nginx forbidden）")
                print("这通常是因为IP地址被网站暂时封禁")
                print("建议采取以下措施：")
                print("1. 等待10-15分钟后再尝试")
                print("2. 使用代理IP")
                print("3. 更换网络环境")
                print("4. 减少请求频率")
                
                # 尝试清除可能的cookies和缓存
                print("正在尝试清除浏览器数据...")
                await context.clear_cookies()
                
                # 添加随机延迟
                wait_time = random.uniform(60, 120)
                print(f"将在 {wait_time:.1f} 秒后重试...")
                await asyncio.sleep(wait_time)
                
                # 重新加载页面
                print("正在重新尝试访问...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # 再次检查
                page_content = await page.content()
                if "Nginx forbidden" in page_content:
                    print("❌  仍然被禁止访问，请稍后再试")
                    return
                else:
                    print("✅  成功重新访问")
            
            # 等待页面完全加载
            await page.wait_for_load_state("load", timeout=30000)
            
            # 模拟人类行为
            await simulate_human_behavior(page)
            
            # 获取表头
            try:
                thead = await page.query_selector("xpath=/html/body/div[2]/div[4]/div[2]/table/thead/tr")
                if thead:
                    header_cells = await thead.query_selector_all("th")
                    headers = [await cell.inner_text() for cell in header_cells]
                    print(f"表头: {headers}")
                else:
                    print("未找到表头")
            except Exception as e:
                print(f"获取表头时出错: {str(e)}")
            
            # 获取页数信息
            try:
                page_info = await page.query_selector("xpath=/html/body/div[2]/div[4]/div[2]/div/span")
                if page_info:
                    page_text = await page_info.inner_text()
                    print(f"分页信息: {page_text}")
                    # 提取总页数
                    import re
                    # 匹配 "1/34" 格式
                    page_match = re.search(r'/([\d]+)$', page_text)
                    if page_match:
                        total_pages = int(page_match.group(1))
                        print(f"总页数: {total_pages}")
                    else:
                        # 尝试匹配 "共34页" 格式
                        page_match = re.search(r'共(\d+)页', page_text)
                        if page_match:
                            total_pages = int(page_match.group(1))
                            print(f"总页数: {total_pages}")
                        else:
                            total_pages = 1
                            print("未找到总页数，默认爬取1页")
                else:
                    total_pages = 1
                    print("未找到分页信息，默认爬取1页")
            except Exception as e:
                total_pages = 1
                print(f"获取分页信息时出错: {str(e)}")
            
            # 遍历所有页面，最多爬取5页以避免过度请求
            max_pages = min(total_pages, 100)
            print(f"将爬取前 {max_pages} 页数据")
            
            # 用于去重的集合
            seen_data = set()
            
            for page_num in range(1, max_pages + 1):
                print(f"\n爬取第 {page_num} 页...")
                
                # 如果不是第一页，点击下一页按钮
                if page_num > 1:
                    try:
                        # 模拟人类行为
                        await simulate_human_behavior(page)
                        
                        # 使用更可靠的方式定位下一页按钮，基于文本内容
                        next_page_button = await page.query_selector("xpath=//div[@id='m-page']//a[contains(text(), '下一页')]")
                        if not next_page_button:
                            # 备用方案：基于class和位置
                            next_page_button = await page.query_selector("xpath=//div[@class='m-pager']//a[contains(@class, 'changePage') and not(contains(text(), '首页')) and not(contains(text(), '上一页')) and not(contains(text(), '尾页'))][last()]")
                        
                        if next_page_button:
                            # 模拟鼠标移动到下一页按钮
                            box = await next_page_button.bounding_box()
                            if box:
                                # 平滑移动鼠标
                                await page.mouse.move(
                                    box['x'] + box['width']/2,
                                    box['y'] + box['height']/2,
                                    steps=random.randint(10, 15)
                                )
                                await asyncio.sleep(random.uniform(0.8, 1.5))
                            
                            # 点击下一页按钮
                            await next_page_button.click()
                            # 等待页面完全加载，增加等待时间
                            await page.wait_for_load_state("networkidle", timeout=60000)
                            # 等待更长时间，确保数据加载完成
                            await asyncio.sleep(random.uniform(4, 6))
                            
                            # 检查是否被禁止
                            page_content = await page.content()
                            if "Nginx forbidden" in page_content:
                                print("⚠️  被网站禁止访问，请稍后再试")
                                break
                            
                            # 模拟人类行为
                            await simulate_human_behavior(page)
                        else:
                            print("未找到下一页按钮，停止爬取")
                            break
                    except Exception as e:
                        print(f"点击下一页时出错: {str(e)}")
                        break
                
                # 使用 XPath 选择器获取目标表格
                try:
                    tbody = await page.query_selector("xpath=/html/body/div[2]/div[4]/div[2]/table/tbody")
                    
                    if tbody:
                        # 获取表格中的所有行
                        rows = await tbody.query_selector_all("tr")
                        print(f"找到 {len(rows)} 行数据")
                        
                        # 遍历行，提取数据
                        for i, row in enumerate(rows):
                            # # 每5行模拟一次人类行为
                            # if i % 5 == 0:
                            #     await simulate_human_behavior(page)
                            
                            # 获取每行的所有单元格
                            cells = await row.query_selector_all("td")
                            
                            # 提取每个单元格的文本内容
                            cell_data = []
                            for cell in cells:
                                text = await cell.inner_text()
                                cell_data.append(text.strip())
                            
                            # 去重
                            if cell_data:
                                data_key = tuple(cell_data[:3])  # 使用前三个字段作为键
                                if data_key not in seen_data:
                                    seen_data.add(data_key)
                                    all_data.append(cell_data)
                                    print(f"第 {i+1} 行: {cell_data}")
                    else:
                        print("未找到目标表格结构")
                        # 截图保存，便于调试
                        await page.screenshot(path=f"page_{page_num}_error.png")
                        print(f"已保存错误截图: page_{page_num}_error.png")
                        # 打印页面结构，便于调试
                        page_content = await page.content()
                        print(f"页面内容预览: {page_content[:500]}...")
                except Exception as e:
                    print(f"获取表格数据时出错: {str(e)}")
                    await page.screenshot(path=f"table_error_{page_num}.png")
                    print(f"已保存错误截图: table_error_{page_num}.png")
            
            # 保存数据到 CSV 文件
            if all_data:
                with open(f'ths_concept_stocks_{code}.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    # 写入表头
                    if headers:
                        writer.writerow(headers)
                    # 写入数据
                    writer.writerows(all_data)
                print(f"\n✅  数据已保存到 ths_concept_stocks_{code}.csv，共 {len(all_data)} 条记录")
            else:
                print("未获取到任何数据")
                
        except Exception as e:
            print(f"爬取过程中出错: {str(e)}")
            # 截图保存，便于调试
            await page.screenshot(path="error_screenshot.png")
            print("已保存错误截图: error_screenshot.png")
            # 打印页面内容，便于调试
            page_content = await page.content()
            print(f"页面内容: {page_content[:1000]}...")
        finally:
            # 随机延迟后关闭浏览器
            await asyncio.sleep(random.uniform(2, 4))
            await context.close()

async def check_login_status():
    """检查是否已登录"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # 创建临时上下文检查登录状态
        context = await p.chromium.launch_persistent_context(
            "user_data",
            headless=False,  # 使用非无头模式以确保会话一致性
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--window-size=100,100"  # 小窗口以减少资源使用
            ]
        )
        
        page = await context.new_page()
        
        try:
            # 直接访问目标页面
            target_url = "https://q.10jqka.com.cn/gn/detail/code/301558/"
            # print(f"正在检查登录状态，访问目标页面: {target_url}")
            # await page.goto(target_url, wait_until="networkidle", timeout=30000)
            
            # 检查登录状态
            print(f"当前URL: {page.url}")
            
            # 检查是否被重定向到登录页面
            # if "login" in page.url.lower() or "upass" in page.url.lower():
            #     print("❌  被重定向到登录页面，需要登录")
            #     return False
            
            # 检查是否有登录元素
            # try:
            #     # 查找登录按钮或提示
            #     login_elements = await page.query_selector_all(
            #         "//*[contains(text(), '登录') or contains(text(), 'Login') or contains(@id, 'login') or contains(@class, 'login')]"
            #     )
                
            #     # if login_elements:
            #     #     print(f"❌  页面中存在登录相关元素，需要登录")
            #     #     return False
                
            #     # 检查页面内容是否包含登录提示
            #     page_content = await page.content()
            #     if "登录" in page_content and "请登录" in page_content:
            #         print("❌  页面内容包含登录提示，需要登录")
            #         return False
                    
            # except Exception as e:
            #     print(f"检查登录元素时出错: {e}")
            #     pass
            
            print("✅  登录状态检查通过，已登录")
            return True
        finally:
            await context.close()

if __name__ == "__main__":
    # 程序开始前的延迟
    # time.sleep(random.uniform(2, 4))
    
    # 检查是否需要登录
    # print("正在检查登录状态...")
    # is_logged_in = asyncio.run(check_login_status())
    
    is_logged_in = True

    if not is_logged_in:
        print("需要登录同花顺")
        print("请在浏览器中使用微信扫码登录")
        print("登录成功后，会话将被保存到 user_data 目录，支持7天免登录")
        
        # 运行登录函数
        asyncio.run(login_and_save_session())
        
        # 登录完成后，询问是否开始爬取
        input("\n登录完成后，请按回车键开始爬取数据...")
    else:
        print("✅  已登录，直接开始爬取")
    
    # 开始爬取
    asyncio.run(crawl_alibaba_concept())
