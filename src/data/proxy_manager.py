"""
Proxy Manager Module for Stock Data Fetching

股票数据获取的代理池管理模块

功能：
- 免费代理获取（从多个免费代理源）
- 代理验证和筛选
- 代理轮换机制
- 防爬机制（延迟、重试、User-Agent轮换）

依赖：
    requests: 用于获取代理列表和验证
"""

import random
import time
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
from urllib.parse import urljoin


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """代理对象"""
    ip: str
    port: int
    protocol: str = "http"
    country: str = ""
    anonymity: str = ""
    speed: float = 0.0  # 响应时间（秒）
    last_checked: datetime = field(default_factory=datetime.now)
    fail_count: int = 0
    success_count: int = 0
    
    @property
    def url(self) -> str:
        """返回代理 URL"""
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    @property
    def dict(self) -> Dict[str, str]:
        """返回 requests 使用的代理字典"""
        return {
            "http": self.url,
            "https": self.url
        }
    
    def __str__(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port} ({self.country}, {self.anonymity})"


class ProxyManager:
    """
    代理池管理器
    
    管理免费代理，提供代理轮换和防爬机制
    
    Attributes:
        proxies: 代理列表
        max_fail_count: 最大失败次数，超过则移除
        verify_url: 验证代理可用性的 URL
        timeout: 代理验证超时时间
    """
    
    # 免费代理源 URLs
    PROXY_SOURCES = {
        'free_proxy_list': 'https://free-proxy-list.net/',
        'ssl_proxies': 'https://sslproxies.org/',
        'us_proxy': 'https://us-proxy.org/',
        'socks_proxy': 'https://socks-proxy.net/',
    }
    
    # User-Agent 列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(
        self,
        max_fail_count: int = 3,
        verify_url: str = "http://httpbin.org/ip",
        timeout: int = 10,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        enable_proxy: bool = True
    ):
        """
        初始化代理管理器
        
        Args:
            max_fail_count: 代理最大失败次数，超过则移除
            verify_url: 验证代理可用性的 URL
            timeout: 代理验证超时时间（秒）
            min_delay: 最小请求延迟（秒）
            max_delay: 最大请求延迟（秒）
            enable_proxy: 是否启用代理
        """
        self.proxies: List[Proxy] = []
        self.max_fail_count = max_fail_count
        self.verify_url = verify_url
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enable_proxy = enable_proxy
        self.current_index = 0
        self.last_request_time = None
        
        logger.info(f"代理管理器初始化完成 (代理: {'启用' if enable_proxy else '禁用'})")
    
    def get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    def get_random_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def fetch_proxies_from_free_proxy_list(self) -> List[Proxy]:
        """
        从 free-proxy-list.net 获取免费代理
        
        Returns:
            代理列表
        """
        proxies = []
        try:
            logger.info("正在从 free-proxy-list.net 获取代理...")
            response = requests.get(
                'https://free-proxy-list.net/',
                headers=self.get_random_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', {'class': 'table'})
                
                if table:
                    rows = table.find_all('tr')[1:]  # 跳过表头
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            try:
                                ip = cols[0].text.strip()
                                port = int(cols[1].text.strip())
                                country = cols[3].text.strip()
                                anonymity = cols[4].text.strip()
                                https = cols[6].text.strip()
                                
                                protocol = 'https' if https == 'yes' else 'http'
                                
                                proxy = Proxy(
                                    ip=ip,
                                    port=port,
                                    protocol=protocol,
                                    country=country,
                                    anonymity=anonymity
                                )
                                proxies.append(proxy)
                            except (ValueError, IndexError):
                                continue
                    
                    logger.info(f"从 free-proxy-list.net 获取了 {len(proxies)} 个代理")
            
        except Exception as e:
            logger.error(f"从 free-proxy-list.net 获取代理失败: {e}")
        
        return proxies
    
    def fetch_proxies_from_ssl_proxies(self) -> List[Proxy]:
        """
        从 sslproxies.org 获取 SSL 代理
        
        Returns:
            代理列表
        """
        proxies = []
        try:
            logger.info("正在从 sslproxies.org 获取代理...")
            response = requests.get(
                'https://sslproxies.org/',
                headers=self.get_random_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', {'class': 'table'})
                
                if table:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            try:
                                ip = cols[0].text.strip()
                                port = int(cols[1].text.strip())
                                country = cols[3].text.strip()
                                anonymity = cols[4].text.strip()
                                
                                proxy = Proxy(
                                    ip=ip,
                                    port=port,
                                    protocol='https',
                                    country=country,
                                    anonymity=anonymity
                                )
                                proxies.append(proxy)
                            except (ValueError, IndexError):
                                continue
                    
                    logger.info(f"从 sslproxies.org 获取了 {len(proxies)} 个代理")
            
        except Exception as e:
            logger.error(f"从 sslproxies.org 获取代理失败: {e}")
        
        return proxies
    
    def fetch_proxies(self, max_proxies: int = 50) -> List[Proxy]:
        """
        从所有源获取代理
        
        Args:
            max_proxies: 最多获取的代理数量
            
        Returns:
            代理列表
        """
        if not self.enable_proxy:
            logger.info("代理已禁用，跳过获取")
            return []
        
        all_proxies = []
        
        # 从多个源获取
        all_proxies.extend(self.fetch_proxies_from_free_proxy_list())
        all_proxies.extend(self.fetch_proxies_from_ssl_proxies())
        
        # 去重
        unique_proxies = []
        seen = set()
        for proxy in all_proxies:
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        # 限制数量
        self.proxies = unique_proxies[:max_proxies]
        
        logger.info(f"共获取 {len(self.proxies)} 个唯一代理")
        return self.proxies
    
    def verify_proxy(self, proxy: Proxy) -> bool:
        """
        验证代理是否可用
        
        Args:
            proxy: 代理对象
            
        Returns:
            是否可用
        """
        try:
            start_time = time.time()
            response = requests.get(
                self.verify_url,
                proxies=proxy.dict,
                headers=self.get_random_headers(),
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                proxy.speed = elapsed
                proxy.success_count += 1
                proxy.last_checked = datetime.now()
                logger.debug(f"代理验证成功: {proxy.url} (响应时间: {elapsed:.2f}s)")
                return True
            else:
                proxy.fail_count += 1
                return False
                
        except Exception as e:
            proxy.fail_count += 1
            logger.debug(f"代理验证失败: {proxy.url} - {e}")
            return False
    
    def verify_all_proxies(self, sample_size: Optional[int] = None) -> List[Proxy]:
        """
        验证所有代理，移除无效的
        
        Args:
            sample_size: 如果指定，只验证随机样本（加快验证速度）
            
        Returns:
            可用代理列表
        """
        if not self.proxies:
            logger.warning("代理列表为空，请先获取代理")
            return []
        
        logger.info(f"开始验证代理 (共 {len(self.proxies)} 个)...")
        
        # 如果指定了样本大小，随机选择
        proxies_to_verify = self.proxies
        if sample_size and sample_size < len(self.proxies):
            proxies_to_verify = random.sample(self.proxies, sample_size)
            logger.info(f"随机选择 {sample_size} 个代理进行验证")
        
        valid_proxies = []
        for proxy in proxies_to_verify:
            if self.verify_proxy(proxy):
                valid_proxies.append(proxy)
            time.sleep(0.1)  # 避免验证过快
        
        self.proxies = valid_proxies
        logger.info(f"验证完成，可用代理: {len(self.proxies)} 个")
        return self.proxies
    
    def get_proxy(self) -> Optional[Proxy]:
        """
        获取一个可用代理（轮询方式）
        
        Returns:
            代理对象，如果没有可用代理返回 None
        """
        if not self.enable_proxy or not self.proxies:
            return None
        
        # 移除失败次数过多的代理
        self.proxies = [p for p in self.proxies if p.fail_count < self.max_fail_count]
        
        if not self.proxies:
            logger.warning("没有可用代理")
            return None
        
        # 轮询获取
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        
        return proxy
    
    def get_random_proxy(self) -> Optional[Proxy]:
        """
        随机获取一个代理
        
        Returns:
            代理对象
        """
        if not self.enable_proxy or not self.proxies:
            return None
        
        # 移除失败次数过多的代理
        self.proxies = [p for p in self.proxies if p.fail_count < self.max_fail_count]
        
        if not self.proxies:
            return None
        
        return random.choice(self.proxies)
    
    def apply_delay(self):
        """
        应用随机延迟，防止请求过快
        """
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # 如果距离上次请求时间太短，额外延迟
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < delay:
                extra_delay = delay - elapsed
                logger.debug(f"请求间隔太短，额外延迟 {extra_delay:.2f}s")
                time.sleep(extra_delay)
        
        time.sleep(delay)
        self.last_request_time = time.time()
    
    def request(
        self,
        url: str,
        method: str = "GET",
        max_retries: int = 3,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        使用代理发送请求（带重试机制）
        
        Args:
            url: 请求 URL
            method: 请求方法
            max_retries: 最大重试次数
            **kwargs: 传递给 requests 的其他参数
            
        Returns:
            响应对象，失败返回 None
        """
        # 应用延迟
        self.apply_delay()
        
        # 添加随机请求头
        if 'headers' not in kwargs:
            kwargs['headers'] = self.get_random_headers()
        
        for attempt in range(max_retries):
            try:
                # 获取代理
                proxy = self.get_proxy() if self.enable_proxy else None
                
                if proxy:
                    kwargs['proxies'] = proxy.dict
                    logger.debug(f"使用代理: {proxy.url}")
                else:
                    kwargs.pop('proxies', None)
                
                # 发送请求
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    if proxy:
                        proxy.success_count += 1
                    return response
                else:
                    logger.warning(f"请求返回状态码: {response.status_code}")
                    if proxy:
                        proxy.fail_count += 1
                    
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if proxy:
                    proxy.fail_count += 1
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增延迟
                    logger.info(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
        
        logger.error(f"请求失败，已达最大重试次数: {url}")
        return None
    
    def remove_proxy(self, proxy: Proxy):
        """移除指定代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"移除代理: {proxy.url}")
    
    def get_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            'total_proxies': len(self.proxies),
            'http_proxies': len([p for p in self.proxies if p.protocol == 'http']),
            'https_proxies': len([p for p in self.proxies if p.protocol == 'https']),
            'avg_speed': sum(p.speed for p in self.proxies) / len(self.proxies) if self.proxies else 0,
            'countries': list(set(p.country for p in self.proxies)),
        }


def create_proxy_manager(enable_proxy: bool = True) -> ProxyManager:
    """
    创建并初始化代理管理器的便捷函数
    
    Args:
        enable_proxy: 是否启用代理
        
    Returns:
        代理管理器实例
    """
    manager = ProxyManager(enable_proxy=enable_proxy)
    
    if enable_proxy:
        # 获取代理
        manager.fetch_proxies(max_proxies=30)
        
        # 验证代理（验证样本以加快速度）
        if manager.proxies:
            manager.verify_all_proxies(sample_size=min(10, len(manager.proxies)))
    
    return manager


# 便捷函数
def with_retry(max_retries: int = 3, delay: float = 1.0):
    """
    装饰器：为函数添加重试机制
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"{func.__name__} 已达最大重试次数")
                        raise
            return None
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试代理管理器
    print("="*70)
    print("代理管理器测试")
    print("="*70)
    
    # 创建代理管理器
    manager = ProxyManager(enable_proxy=True)
    
    # 获取代理
    print("\n1. 获取代理...")
    manager.fetch_proxies(max_proxies=20)
    
    if manager.proxies:
        # 验证代理
        print("\n2. 验证代理...")
        manager.verify_all_proxies(sample_size=5)
        
        # 显示统计
        print("\n3. 代理统计:")
        stats = manager.get_stats()
        print(f"   总代理数: {stats['total_proxies']}")
        print(f"   HTTP: {stats['http_proxies']}, HTTPS: {stats['https_proxies']}")
        print(f"   平均速度: {stats['avg_speed']:.2f}s")
        
        # 测试请求
        print("\n4. 测试请求...")
        response = manager.request("http://httpbin.org/ip")
        if response:
            print(f"   请求成功: {response.text}")
        else:
            print("   请求失败")
    else:
        print("未获取到代理")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
