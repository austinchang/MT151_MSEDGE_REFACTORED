"""
配置管理模組

統一管理MT151_MSEDGE專案的所有配置項目，包括：
- 系統配置
- 瀏覽器配置  
- 資料配置
- AI模型配置
- 網站配置
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class BrowserConfig(BaseModel):
    """瀏覽器配置"""
    default_browser: str = "msedge"
    headless: bool = False
    slow_mo: int = 500
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_data_dir: Optional[str] = None
    
    # 瀏覽器特定參數
    chrome_args: List[str] = Field(default_factory=lambda: [
        "--start-maximized",
        "--disable-dev-shm-usage", 
        "--no-sandbox",
        "--disable-features=VizDisplayCompositor"
    ])
    
    @validator('default_browser')
    def validate_browser(cls, v):
        allowed = ['msedge', 'chrome', 'chromium', 'firefox', 'webkit']
        if v not in allowed:
            raise ValueError(f'Browser must be one of {allowed}')
        return v


class DataConfig(BaseModel):
    """資料配置"""
    # 預設測試資料
    default_test_data: Dict[str, str] = Field(default_factory=lambda: {
        "料號": "C08GL0DIG017A",
        "站位": "B/I", 
        "版本": "V3.3.5.9_1.16.0.1E3.12-1",
        "描述": "EN0DIGOA1-0322-GL_HL-325L B/I",
        "MFGID群組": "DEFAULT"
    })
    
    # 資料驗證規則
    validation_rules: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "料號": {
            "required": True,
            "pattern": r"^[A-Z0-9]{10,}$",
            "description": "料號必須為10位以上的大寫字母和數字組合"
        },
        "站位": {
            "required": True,
            "allowed_values": ["B/I", "FT", "PT", "SHIP"],
            "description": "站位必須為預定義值之一"
        },
        "版本": {
            "required": True,
            "pattern": r"^V\d+\.\d+\.\d+\.\d+_\d+\.\d+\.\d+\.\d+E\d+\.\d+.*$",
            "description": "版本號必須符合指定格式"
        },
        "描述": {
            "required": True,
            "min_length": 5,
            "description": "描述不能為空且至少5個字符"
        },
        "MFGID群組": {
            "required": False,
            "default": "DEFAULT",
            "description": "MFGID群組可選，預設為DEFAULT"
        }
    })
    
    # 資料檔案路徑
    data_file_path: str = "config/test_data.json"
    backup_data_path: str = "config/backup"
    
    # 批量操作設定
    batch_size: int = 10
    batch_delay: float = 1.0  # 秒


class WebConfig(BaseModel):
    """網站配置"""
    # MMT010系統配置
    base_url: str = "https://accmisportal.accton.com/ACCTON/MMT/MMT010/MMT010_Index"
    login_timeout: int = 120000  # 毫秒
    page_load_timeout: int = 60000  # 毫秒
    element_timeout: int = 10000  # 毫秒
    
    # 頁面元素選擇器
    selectors: Dict[str, str] = Field(default_factory=lambda: {
        "search_button": "#fr_btn_search_MMT010_Index_FormLayout_search_CD",
        "save_all_button": "#cus_btn_masterdetailsave_CD", 
        "grid_container": '[id$="Setting_GridViewPartial"]',
        "data_row": 'tr.dxgvDataRow_DEVMVC',
        "header_row": 'tr.dxgvHeader_DEVMVC',
        "add_button": '[id$="_DXCBtnNew"]',
        "delete_button": '[id$="_DXCBtnDelete"]',
        "edit_button": '[id$="_DXCBtnEdit"]',
        "password_input": "input[type='password']"
    })
    
    # 欄位映射（欄位名稱對應表格列索引）
    column_mapping: Dict[str, int] = Field(default_factory=lambda: {
        "料號": 1,
        "站位": 2, 
        "版本": 3,
        "描述": 4,
        "MFGID群組": 5
    })


class AIConfig(BaseModel):
    """AI配置"""
    # 預設AI模型設定
    default_model: str = "auto"
    provider: str = "auto"  # auto, xai, gemini, openai
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    
    # zen-mcp-server配置
    zen_server_enabled: bool = True
    zen_server_path: Optional[str] = None
    
    # 功能開關
    enable_data_analysis: bool = True
    enable_error_diagnosis: bool = True
    enable_chat_assistance: bool = True
    enable_test_generation: bool = True
    
    # AI提示詞配置
    prompts: Dict[str, str] = Field(default_factory=lambda: {
        "data_analysis": """
        請分析以下測試資料的合理性和完整性：
        資料: {data}
        
        請檢查：
        1. 格式是否正確
        2. 內容是否合理
        3. 是否有潛在問題
        4. 改善建議
        """,
        "error_diagnosis": """
        請分析以下錯誤並提供解決方案：
        錯誤: {error}
        上下文: {context}
        
        請提供：
        1. 錯誤原因分析
        2. 解決步驟
        3. 預防措施
        """,
        "chat_system": """
        你是MT151_MSEDGE專案的AI助手，專門協助用戶進行MMT010系統的自動化操作。
        請用繁體中文回答，保持友善和專業的語調。
        """
    })


class LogConfig(BaseModel):
    """日誌配置"""
    # 日誌級別
    log_level: str = "INFO"
    
    # 日誌檔案配置
    log_file: str = "logs/mt151_msedge.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # 日誌格式
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # 控制台輸出
    console_output: bool = True
    console_level: str = "INFO"
    
    @validator('log_level', 'console_level')
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in allowed:
            raise ValueError(f'Log level must be one of {allowed}')
        return v


class AppConfig(BaseModel):
    """應用主配置"""
    # 版本資訊
    version: str = "2.0.0"
    app_name: str = "MT151_MSEDGE"
    description: str = "MMT010自動化測試工具"
    
    # 子配置
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    logging: LogConfig = Field(default_factory=LogConfig)
    
    # 應用設定
    auto_save: bool = True
    confirm_destructive_actions: bool = True
    max_retry_attempts: int = 3
    retry_delay: float = 2.0
    
    # 開發模式
    debug_mode: bool = False
    verbose_logging: bool = False


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else Path("config/app_config.json")
        self.config = AppConfig()
        self._ensure_config_dir()
        self.load_config()
    
    def _ensure_config_dir(self):
        """確保配置目錄存在"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> AppConfig:
        """載入配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = AppConfig(**config_data)
                print(f"✅ 配置已從 {self.config_path} 載入")
            except Exception as e:
                print(f"⚠️ 載入配置失敗，使用預設配置: {e}")
                self.save_config()  # 儲存預設配置
        else:
            print("📝 使用預設配置")
            self.save_config()  # 建立預設配置檔案
        
        return self.config
    
    def save_config(self):
        """儲存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.config.dict(), 
                    f, 
                    ensure_ascii=False, 
                    indent=2
                )
            print(f"✅ 配置已儲存至 {self.config_path}")
        except Exception as e:
            print(f"❌ 儲存配置失敗: {e}")
    
    def update_config(self, **kwargs):
        """更新配置項目"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"⚠️ 未知的配置項目: {key}")
        self.save_config()
    
    def get_browser_config(self) -> BrowserConfig:
        """獲取瀏覽器配置"""
        return self.config.browser
    
    def get_data_config(self) -> DataConfig:
        """獲取資料配置"""
        return self.config.data
    
    def get_web_config(self) -> WebConfig:
        """獲取網站配置"""
        return self.config.web
    
    def get_ai_config(self) -> AIConfig:
        """獲取AI配置"""
        return self.config.ai
    
    def get_log_config(self) -> LogConfig:
        """獲取日誌配置"""
        return self.config.logging
    
    def is_debug_mode(self) -> bool:
        """是否為除錯模式"""
        return self.config.debug_mode
    
    def get_version(self) -> str:
        """獲取版本號"""
        return self.config.version


# 全域配置管理器實例
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """獲取應用配置"""
    return config_manager.config


def get_browser_config() -> BrowserConfig:
    """獲取瀏覽器配置"""
    return config_manager.get_browser_config()


def get_data_config() -> DataConfig:
    """獲取資料配置"""
    return config_manager.get_data_config()


def get_web_config() -> WebConfig:
    """獲取網站配置"""
    return config_manager.get_web_config()


def get_ai_config() -> AIConfig:
    """獲取AI配置"""
    return config_manager.get_ai_config()


def get_log_config() -> LogConfig:
    """獲取日誌配置"""
    return config_manager.get_log_config()


if __name__ == "__main__":
    # 測試配置管理
    print("測試配置管理器...")
    
    # 載入配置
    config = get_config()
    print(f"應用版本: {config.version}")
    print(f"預設瀏覽器: {config.browser.default_browser}")
    print(f"AI模型: {config.ai.default_model}")
    
    # 顯示預設測試資料
    print("\n預設測試資料:")
    for key, value in config.data.default_test_data.items():
        print(f"  {key}: {value}")
    
    # 顯示網站選擇器
    print("\n重要選擇器:")
    important_selectors = ["search_button", "save_all_button", "grid_container"]
    for selector in important_selectors:
        print(f"  {selector}: {config.web.selectors[selector]}")
    
    print("\n✅ 配置管理器測試完成")