import asyncio
import random
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
import aiohttp
import logging
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RequestManager:
    def __init__(self, use_stealth: bool = True, use_proxy: bool = True):
        self.use_stealth = use_stealth
        self.use_proxy = use_proxy
        self.browser: Optional[Browser] = None
        self.proxies: List[str] = []
        self.last_request_time = datetime.now()
        self.min_request_interval = 2  # seconds
        self.playwright = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load proxy configuration
        self.proxy_username = os.getenv('PROXY_USERNAME')
        self.proxy_password = os.getenv('PROXY_PASSWORD')
        self.proxy_host = os.getenv('PROXY_HOST', 'proxy.example.com')
        self.proxy_port = os.getenv('PROXY_PORT', '8080')
        
        # Rotating user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
        ]

    async def init_browser(self):
        if self.browser is not None:
            return
            
        try:
            self.playwright = await async_playwright().start()
            browser_args = [
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-component-extensions-with-background-pages',
                '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--mute-audio',
                '--window-size=1920,1080',
                '--start-maximized'
            ]
            
            if self.use_proxy and self.proxy_username and self.proxy_password:
                # Use residential proxy with authentication
                proxy_url = f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}"
                browser_args.append(f'--proxy-server={proxy_url}')
                self.logger.info(f"Using proxy: {self.proxy_host}:{self.proxy_port}")
            else:
                self.logger.warning("No proxy credentials found, running without proxy")
                
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to False to bypass Cloudflare
                args=browser_args
            )
        except Exception as e:
            self.logger.error(f"Error initializing browser: {str(e)}")
            if self.playwright:
                await self.playwright.stop()
            raise

    async def get_page(self) -> Page:
        await self.init_browser()
        try:
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': random.choice(self.user_agents),
                'ignore_https_errors': True,
                'java_script_enabled': True,
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'geolocation': {'latitude': 18.4861, 'longitude': -69.9312},  # Santo Domingo coordinates
                'permissions': ['geolocation'],
                'color_scheme': 'light',
                'reduced_motion': 'no-preference',
                'forced_colors': 'none',
                'accept_downloads': True
            }
            
            if self.use_proxy and self.proxy_username and self.proxy_password:
                context_options['proxy'] = {
                    'server': f'http://{self.proxy_host}:{self.proxy_port}',
                    'username': self.proxy_username,
                    'password': self.proxy_password
                }
            
            context = await self.browser.new_context(**context_options)
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: () => 0
                });
                Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.'
                });
                Object.defineProperty(navigator, 'appVersion', {
                    get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                });
                Object.defineProperty(navigator, 'appName', {
                    get: () => 'Netscape'
                });
                Object.defineProperty(navigator, 'appCodeName', {
                    get: () => 'Mozilla'
                });
                Object.defineProperty(navigator, 'product', {
                    get: () => 'Gecko'
                });
                Object.defineProperty(navigator, 'productSub', {
                    get: () => '20030107'
                });
                Object.defineProperty(navigator, 'oscpu', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'buildID', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'doNotTrack', {
                    get: () => null
                });
                Object.defineProperty(navigator, 'cookieEnabled', {
                    get: () => true
                });
                Object.defineProperty(navigator, 'onLine', {
                    get: () => true
                });
                Object.defineProperty(navigator, 'serviceWorker', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    })
                });
            """)
            
            page = await context.new_page()
            
            if self.use_stealth:
                # Apply stealth settings
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1',
                    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                })
                
            return page
        except Exception as e:
            self.logger.error(f"Error creating new page: {str(e)}")
            raise

    def add_proxy(self, proxy: str):
        self.proxies.append(proxy)

    async def close(self):
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}")
        if self.playwright:
            try:
                await self.playwright.stop()
                self.playwright = None
            except Exception as e:
                self.logger.error(f"Error stopping playwright: {str(e)}")

    async def _wait_for_rate_limit(self):
        elapsed = datetime.now() - self.last_request_time
        if elapsed.total_seconds() < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed.total_seconds())
        self.last_request_time = datetime.now()

    async def _simulate_human_behavior(self, page: Page):
        """Simulate human-like behavior to avoid bot detection"""
        # Random mouse movements
        for _ in range(3):
            x = random.randint(0, 1920)
            y = random.randint(0, 1080)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Random scrolling
        await page.evaluate("""
            window.scrollTo({
                top: Math.random() * document.body.scrollHeight,
                behavior: 'smooth'
            });
        """)
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Scroll back to top
        await page.evaluate("""
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        """)
        await asyncio.sleep(random.uniform(0.5, 1.0))

    async def get(self, url: str, **kwargs) -> Page:
        """Get a page from the given URL with rate limiting and error handling"""
        await self._wait_for_rate_limit()
        self.logger.info(f"Fetching URL: {url}")
        
        page = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                page = await self.get_page()
                
                # Set a longer timeout for the initial page load
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Simulate human behavior
                await self._simulate_human_behavior(page)
                
                # Wait for Cloudflare challenge to complete
                try:
                    # Wait for the challenge to appear
                    await page.wait_for_selector('div[class*="challenge"]', timeout=50000)
                    self.logger.info("Cloudflare challenge detected, waiting for completion...")
                    
                    # Try to find and click the checkbox
                    try:
                        checkbox = await page.wait_for_selector('input[type="checkbox"]', timeout=50000)
                        if checkbox:
                            self.logger.info("Found Cloudflare checkbox, clicking...")
                            # Move mouse to checkbox
                            box = await checkbox.bounding_box()
                            if box:
                                await page.mouse.move(
                                    box['x'] + box['width'] / 2,
                                    box['y'] + box['height'] / 2
                                )
                                await asyncio.sleep(random.uniform(0.1, 0.3))
                                await checkbox.click()
                                await asyncio.sleep(2)
                    except TimeoutError:
                        self.logger.info("No checkbox found, continuing...")
                    
                    # Wait for the challenge to complete (up to 30 seconds)
                    for _ in range(30):
                        if not await page.query_selector('div[class*="challenge"]'):
                            self.logger.info("Cloudflare challenge completed")
                            break
                        await asyncio.sleep(1)
                    
                    # Additional wait to ensure page is fully loaded
                    await asyncio.sleep(5)
                    
                except TimeoutError:
                    self.logger.info("No Cloudflare challenge detected, continuing...")
                
                # Wait for the main content to be visible
                try:
                    await page.wait_for_selector('body', timeout=50000)
                except TimeoutError:
                    self.logger.warning("Body selector not found, continuing anyway")
                
                # Simulate more human behavior after page load
                await self._simulate_human_behavior(page)
                
                return page
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Attempt {retry_count}/{max_retries} failed: {str(e)}")
                if page:
                    await page.close()
                if retry_count == max_retries:
                    raise
                await asyncio.sleep(2 * retry_count)  # Exponential backoff