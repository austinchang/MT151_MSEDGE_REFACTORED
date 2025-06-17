"""
瀏覽器管理模組

統一管理瀏覽器的啟動、配置和操作，支援多種瀏覽器：
- Microsoft Edge
- Google Chrome  
- Chromium
- Firefox
- Safari (macOS)
"""

import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from config import BrowserConfig, get_browser_config


class BrowserInfo:
    """瀏覽器資訊類別"""
    
    def __init__(self, browser: Union[Browser, BrowserContext], page: Page, 
                 browser_type: str, name: str, mode: str = "normal"):
        self.browser = browser
        self.page = page
        self.browser_type = browser_type  # chromium, firefox, webkit
        self.name = name  # Microsoft Edge, Google Chrome, etc.
        self.mode = mode  # normal, persistent
        self.temp_dir: Optional[str] = None
    
    async def close(self):
        """關閉瀏覽器"""
        try:
            if self.mode == "persistent":
                await self.browser.close()
            else:
                await self.browser.close()
        except Exception as e:
            logging.warning(f"關閉瀏覽器時發生警告: {e}")
    
    def __str__(self):
        return f"{self.name} ({self.browser_type}, {self.mode})"


class BrowserSelector:
    """瀏覽器選擇器"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or get_browser_config()
        self.logger = logging.getLogger(__name__)
        
        # 支援的瀏覽器配置
        self.available_browsers = {
            "1": {
                "name": "Microsoft Edge",
                "channel": "msedge", 
                "executable": "chromium",
                "description": "推薦用於企業環境"
            },
            "2": {
                "name": "Google Chrome",
                "channel": "chrome",
                "executable": "chromium",
                "description": "廣泛使用的瀏覽器"
            },
            "3": {
                "name": "Chromium",
                "channel": None,
                "executable": "chromium",
                "description": "開源Chromium核心"
            },
            "4": {
                "name": "Firefox",
                "channel": None,
                "executable": "firefox",
                "description": "Mozilla開發的瀏覽器"
            },
            "5": {
                "name": "Safari",
                "channel": None,
                "executable": "webkit",
                "description": "僅限 macOS"
            }
        }
    
    def show_menu(self):
        """顯示瀏覽器選擇選單"""
        print("\n" + "="*70)
        print("🌐 請選擇要使用的瀏覽器:")
        print("="*70)
        
        for key, browser in self.available_browsers.items():
            print(f"  {key}. {browser['name']:<20} - {browser['description']}")
        
        print(f"  0. 自動選擇                  - 系統推薦 (當前預設: {self.config.default_browser})")
        print("="*70)
    
    def get_user_choice(self) -> Optional[str]:
        """獲取用戶選擇"""
        while True:
            try:
                choice = input("請輸入選項 (0-5): ").strip()
                
                if choice == "0":
                    return "auto"
                elif choice in self.available_browsers:
                    return choice
                else:
                    print("❌ 無效選項，請重新輸入")
                    
            except KeyboardInterrupt:
                print("\n程式已取消")
                return None
            except Exception as e:
                print(f"❌ 輸入錯誤: {e}")
    
    async def launch_browser(self, playwright: Playwright, 
                           choice: str = "auto") -> Optional[BrowserInfo]:
        """根據選擇啟動瀏覽器"""
        
        if choice == "auto":
            return await self._auto_launch(playwright)
        else:
            browser_config = self.available_browsers[choice]
            return await self._launch_specific_browser(playwright, browser_config)
    
    async def _auto_launch(self, playwright: Playwright) -> Optional[BrowserInfo]:
        """自動選擇並啟動瀏覽器"""
        print("🔄 正在自動選擇最佳瀏覽器...")
        
        # 根據配置確定優先順序
        default_browser = self.config.default_browser.lower()
        
        # 建立瀏覽器嘗試列表，將預設瀏覽器放在首位
        browsers_to_try = []
        
        # 預設瀏覽器映射
        browser_mapping = {
            "msedge": {"name": "Microsoft Edge", "channel": "msedge", "executable": "chromium"},
            "chrome": {"name": "Google Chrome", "channel": "chrome", "executable": "chromium"},
            "chromium": {"name": "Chromium", "channel": None, "executable": "chromium"},
            "firefox": {"name": "Firefox", "channel": None, "executable": "firefox"},
            "webkit": {"name": "Safari", "channel": None, "executable": "webkit"}
        }
        
        # 首先嘗試預設瀏覽器
        if default_browser in browser_mapping:
            browsers_to_try.append(browser_mapping[default_browser])
        
        # 然後嘗試其他瀏覽器
        for browser_config in browser_mapping.values():
            if browser_config not in browsers_to_try:
                browsers_to_try.append(browser_config)
        
        # 逐一嘗試啟動瀏覽器
        for browser_config in browsers_to_try:
            try:
                print(f"🔄 嘗試啟動 {browser_config['name']}...")
                
                result = await self._launch_specific_browser(playwright, browser_config)
                if result:
                    print(f"✅ 成功啟動 {browser_config['name']}")
                    return result
                    
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                print(f"❌ {browser_config['name']} 啟動失敗: {error_msg}")
                continue
        
        # 所有瀏覽器都失敗
        print("❌ 無法啟動任何瀏覽器，請檢查Playwright安裝")
        return None
    
    async def _launch_specific_browser(self, playwright: Playwright, 
                                     browser_config: Dict[str, Any]) -> Optional[BrowserInfo]:
        """啟動指定瀏覽器"""
        browser_name = browser_config["name"]
        channel = browser_config["channel"]
        executable = browser_config["executable"]
        
        self.logger.info(f"啟動瀏覽器: {browser_name}")
        
        # 獲取瀏覽器實例
        if executable == "chromium":
            browser_instance = playwright.chromium
        elif executable == "firefox":
            browser_instance = playwright.firefox
        elif executable == "webkit":
            browser_instance = playwright.webkit
        else:
            raise Exception(f"不支援的瀏覽器類型: {executable}")
        
        # 先嘗試持久化模式 (僅適用於Chromium核心瀏覽器)
        if executable == "chromium" and channel in ["msedge", "chrome"]:
            try:
                print(f"  🔄 嘗試 {browser_name} 持久化模式...")
                return await self._launch_persistent_context(
                    browser_instance, browser_name, channel
                )
            except Exception as e:
                print(f"  ⚠️  持久化模式失敗: {str(e)[:100]}")
        
        # 嘗試普通模式
        try:
            print(f"  🔄 嘗試 {browser_name} 普通模式...")
            return await self._launch_normal_browser(
                browser_instance, browser_name, channel
            )
        except Exception as e:
            print(f"  ❌ 普通模式也失敗: {str(e)[:100]}")
            raise e
    
    async def _launch_persistent_context(self, browser_instance, browser_name: str, 
                                       channel: str) -> BrowserInfo:
        """啟動持久化瀏覽器上下文"""
        temp_dir = tempfile.mkdtemp(prefix=f"playwright_{channel}_")
        
        launch_args = {
            "user_data_dir": temp_dir,
            "channel": channel,
            "headless": self.config.headless,
            "slow_mo": self.config.slow_mo,
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            },
            "args": self.config.chrome_args.copy()
        }
        
        # 如果有指定用戶資料目錄，使用它
        if self.config.user_data_dir:
            launch_args["user_data_dir"] = self.config.user_data_dir
        
        browser_context = await browser_instance.launch_persistent_context(**launch_args)
        
        # 獲取或建立頁面
        if len(browser_context.pages) > 0:
            page = browser_context.pages[0]
        else:
            page = await browser_context.new_page()
        
        browser_info = BrowserInfo(
            browser=browser_context,
            page=page,
            browser_type="chromium",
            name=browser_name,
            mode="persistent"
        )
        browser_info.temp_dir = temp_dir
        
        return browser_info
    
    async def _launch_normal_browser(self, browser_instance, browser_name: str,
                                   channel: Optional[str]) -> BrowserInfo:
        """啟動普通瀏覽器"""
        launch_args = {
            "headless": self.config.headless,
            "slow_mo": self.config.slow_mo,
            "args": self.config.chrome_args.copy()
        }
        
        # 只有Chromium核心瀏覽器才支援channel參數
        if channel:
            launch_args["channel"] = channel
        
        browser = await browser_instance.launch(**launch_args)
        page = await browser.new_page()
        
        # 設置視窗大小
        await page.set_viewport_size({
            "width": self.config.viewport_width,
            "height": self.config.viewport_height
        })
        
        return BrowserInfo(
            browser=browser,
            page=page,
            browser_type=browser_instance.name,
            name=browser_name,
            mode="normal"
        )


class BrowserManager:
    """瀏覽器管理器"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or get_browser_config()
        self.selector = BrowserSelector(self.config)
        self.browser_info: Optional[BrowserInfo] = None
        self.playwright: Optional[Playwright] = None
        self.logger = logging.getLogger(__name__)
    
    async def start_browser(self, choice: str = "auto") -> Optional[BrowserInfo]:
        """啟動瀏覽器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser_info = await self.selector.launch_browser(
                self.playwright, choice
            )
            
            if self.browser_info:
                self.logger.info(f"瀏覽器啟動成功: {self.browser_info}")
                
                # 設置頁面超時
                self.browser_info.page.set_default_timeout(self.config.timeout)
                
                return self.browser_info
            else:
                await self.close()
                return None
                
        except Exception as e:
            self.logger.error(f"啟動瀏覽器失敗: {e}")
            await self.close()
            return None
    
    async def get_page(self) -> Optional[Page]:
        """獲取當前頁面"""
        if self.browser_info:
            return self.browser_info.page
        return None
    
    async def navigate_to(self, url: str, wait_for_load: bool = True) -> bool:
        """導航到指定URL"""
        if not self.browser_info:
            self.logger.error("瀏覽器未啟動")
            return False
        
        try:
            page = self.browser_info.page
            await page.goto(url, timeout=self.config.timeout)
            
            if wait_for_load:
                await page.wait_for_load_state('networkidle', timeout=self.config.timeout)
            
            self.logger.info(f"成功導航到: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"導航失敗: {e}")
            return False
    
    async def wait_for_login(self, login_url_pattern: str = "**/MMT010_Index*", 
                           timeout: int = 120000) -> bool:
        """等待用戶登入"""
        if not self.browser_info:
            return False
        
        try:
            page = self.browser_info.page
            
            # 檢查是否有密碼輸入框（表示需要登入）
            password_inputs = await page.locator("input[type='password']").count()
            
            if password_inputs > 0:
                print("⚠️  檢測到登入頁面，請手動登入後繼續...")
                
                # 等待URL變更為登入後的頁面
                await page.wait_for_url(login_url_pattern, timeout=timeout)
                print("✅ 登入完成，繼續執行...")
                
                # 額外等待頁面完全載入
                await page.wait_for_load_state('networkidle', timeout=30000)
                
            return True
            
        except Exception as e:
            self.logger.error(f"等待登入時發生錯誤: {e}")
            return False
    
    async def take_screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """擷取螢幕截圖"""
        if not self.browser_info:
            return None
        
        try:
            if path is None:
                # 自動生成檔案名
                timestamp = asyncio.get_event_loop().time()
                path = f"logs/screenshot_{timestamp:.0f}.png"
            
            # 確保目錄存在
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            await self.browser_info.page.screenshot(path=path, full_page=True)
            self.logger.info(f"螢幕截圖已儲存: {path}")
            return path
            
        except Exception as e:
            self.logger.error(f"擷取螢幕截圖失敗: {e}")
            return None
    
    async def keep_alive(self):
        """保持瀏覽器開啟"""
        if not self.browser_info:
            return
        
        print("🌐 瀏覽器將保持開啟狀態...")
        print("   按 Ctrl+C 退出程式")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n📋 收到中斷信號，正在關閉瀏覽器...")
            await self.close()
    
    async def close(self):
        """關閉瀏覽器和Playwright"""
        try:
            if self.browser_info:
                await self.browser_info.close()
                self.browser_info = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self.logger.info("瀏覽器已關閉")
            
        except Exception as e:
            self.logger.warning(f"關閉瀏覽器時發生警告: {e}")
    
    def __str__(self):
        if self.browser_info:
            return f"BrowserManager({self.browser_info})"
        return "BrowserManager(未啟動)"


if __name__ == "__main__":
    # 測試瀏覽器管理器
    async def test_browser_manager():
        print("🧪 測試瀏覽器管理器...")
        
        manager = BrowserManager()
        
        # 顯示選單並啟動瀏覽器
        manager.selector.show_menu()
        choice = manager.selector.get_user_choice()
        
        if choice:
            browser_info = await manager.start_browser(choice)
            
            if browser_info:
                print(f"✅ 瀏覽器啟動成功: {browser_info}")
                
                # 測試導航
                success = await manager.navigate_to("https://www.google.com")
                if success:
                    print("✅ 導航測試成功")
                
                # 測試截圖
                screenshot_path = await manager.take_screenshot()
                if screenshot_path:
                    print(f"✅ 截圖測試成功: {screenshot_path}")
                
                # 保持開啟
                await manager.keep_alive()
            else:
                print("❌ 瀏覽器啟動失敗")
        else:
            print("❌ 未選擇瀏覽器")
    
    # 運行測試
    asyncio.run(test_browser_manager())