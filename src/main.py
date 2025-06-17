"""
MT151_MSEDGE 主程式

整合所有模組，提供完整的MMT010自動化操作功能：
- 瀏覽器管理和啟動
- 資料管理和驗證
- AI輔助功能
- MMT010系統自動化操作
- 完整的用戶互動介面
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 加入src目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

from ai_integration import AIAssistant, AIModelConfig
from browser_manager import BrowserManager
from config import get_config, get_log_config
from data_manager import DataManager, TestData
from mmt010_automation import MMT010Automation


class MT151App:
    """MT151_MSEDGE 主應用程式類別"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = self._setup_logging()
        
        # 核心組件
        self.browser_manager: Optional[BrowserManager] = None
        self.data_manager: Optional[DataManager] = None
        self.ai_assistant: Optional[AIAssistant] = None
        self.automation: Optional[MMT010Automation] = None
        
        # 應用狀態
        self.is_running = False
        self.current_operation = None
        
        self.logger.info(f"MT151_MSEDGE v{self.config.version} 初始化完成")
    
    def _setup_logging(self) -> logging.Logger:
        """設置日誌系統"""
        log_config = get_log_config()
        
        # 確保日誌目錄存在
        log_file = Path(log_config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 設置根日誌記錄器
        logging.basicConfig(
            level=getattr(logging, log_config.log_level),
            format=log_config.log_format,
            datefmt=log_config.date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler() if log_config.console_output else logging.NullHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("日誌系統初始化完成")
        return logger
    
    def show_welcome(self):
        """顯示歡迎訊息"""
        print("="*80)
        print(f"🚀 歡迎使用 {self.config.app_name} v{self.config.version}")
        print(f"📝 {self.config.description}")
        print("="*80)
        print("功能特色:")
        print("  🌐 多瀏覽器支援 (Edge、Chrome、Firefox)")
        print("  🤖 AI智能輔助 (資料分析、錯誤診斷)")
        print("  📊 完整資料管理 (新增、編輯、刪除、批量操作)")
        print("  🔄 自動化操作 (MMT010系統整合)")
        print("  📝 繁體中文介面")
        print("="*80)
        print("⚠️  注意事項:")
        print("  - 首次使用前請確保已安裝Playwright瀏覽器驅動")
        print("  - 操作前請確認網路連線正常")
        print("  - 建議在正式環境操作前先進行測試")
        print("="*80)
    
    def show_main_menu(self):
        """顯示主選單"""
        print("\n" + "="*70)
        print("🎯 主選單 - 請選擇要執行的操作:")
        print("="*70)
        print("  1. 🌐 啟動瀏覽器並連線到MMT010")
        print("  2. 📊 資料管理 (新增、編輯、查看測試資料)")
        print("  3. 🤖 AI助手 (智能分析、聊天諮詢)")
        print("  4. 🔍 執行搜尋查詢")
        print("  5. 💾 執行儲存操作")
        print("  6. 🧪 測試資料表格操作")
        print("  7. 🚀 完整自動化流程")
        print("  8. 🔧 系統設定和配置")
        print("  9. 📋 查看系統狀態")
        print("  H. 📖 說明和幫助")
        print("  Q. 🚪 退出程式")
        print("="*70)
        
        # 顯示當前狀態
        browser_status = "✅ 已連線" if self.browser_manager and self.browser_manager.browser_info else "❌ 未連線"
        data_count = len(self.data_manager.current_dataset) if self.data_manager else 0
        ai_status = "✅ 可用" if self.ai_assistant else "❌ 未啟用"
        
        print(f"📊 當前狀態: 瀏覽器 {browser_status} | 資料 {data_count} 筆 | AI {ai_status}")
        print()
    
    def get_menu_choice(self) -> Optional[str]:
        """獲取選單選擇"""
        while True:
            try:
                choice = input("請輸入選項 (1-9/H/Q): ").strip().upper()
                valid_choices = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'H', 'Q']
                
                if choice in valid_choices:
                    return choice
                else:
                    print("❌ 無效選項，請重新輸入")
                    
            except KeyboardInterrupt:
                print("\n程式已中斷")
                return 'Q'
            except Exception as e:
                print(f"❌ 輸入錯誤: {e}")
    
    async def initialize_components(self):
        """初始化核心組件"""
        try:
            self.logger.info("正在初始化應用組件...")
            
            # 初始化資料管理器
            self.data_manager = DataManager()
            self.logger.info("✅ 資料管理器初始化完成")
            
            # 初始化AI助手
            if self.config.ai.zen_server_enabled:
                ai_config = AIModelConfig(
                    model_name=self.config.ai.default_model,
                    provider=self.config.ai.provider,
                    temperature=self.config.ai.temperature,
                    max_tokens=self.config.ai.max_tokens,
                    timeout=self.config.ai.timeout
                )
                self.ai_assistant = AIAssistant(ai_config)
                self.logger.info("✅ AI助手初始化完成")
            else:
                self.logger.info("⚠️ AI助手已停用")
            
            self.logger.info("🎉 所有組件初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 組件初始化失敗: {e}")
            raise
    
    async def start_browser_and_connect(self) -> bool:
        """啟動瀏覽器並連線到MMT010"""
        try:
            print("\n🌐 啟動瀏覽器並連線到MMT010...")
            
            # 如果瀏覽器已啟動，詢問是否重新啟動
            if self.browser_manager and self.browser_manager.browser_info:
                choice = input("瀏覽器已啟動，是否重新啟動？(y/N): ").strip().lower()
                if choice == 'y':
                    await self.browser_manager.close()
                    self.browser_manager = None
                    self.automation = None
                else:
                    return True
            
            # 建立瀏覽器管理器
            self.browser_manager = BrowserManager()
            
            # 顯示瀏覽器選擇選單
            self.browser_manager.selector.show_menu()
            browser_choice = self.browser_manager.selector.get_user_choice()
            
            if not browser_choice:
                print("❌ 未選擇瀏覽器")
                return False
            
            # 啟動瀏覽器
            browser_info = await self.browser_manager.start_browser(browser_choice)
            if not browser_info:
                print("❌ 瀏覽器啟動失敗")
                return False
            
            print(f"✅ 瀏覽器啟動成功: {browser_info}")
            
            # 建立自動化操作物件
            page = await self.browser_manager.get_page()
            if page:
                self.automation = MMT010Automation(page)
                
                # 導航到MMT010
                if await self.automation.navigate_to_mmt010():
                    # 等待登入
                    if await self.automation.wait_for_login():
                        print("🎉 成功連線到MMT010系統！")
                        return True
                    else:
                        print("❌ 等待登入失敗")
                        return False
                else:
                    print("❌ 導航到MMT010失敗")
                    return False
            else:
                print("❌ 無法獲取頁面物件")
                return False
                
        except Exception as e:
            self.logger.error(f"啟動瀏覽器連線失敗: {e}")
            print(f"❌ 啟動失敗: {e}")
            return False
    
    async def handle_data_management(self):
        """處理資料管理操作"""
        if not self.data_manager:
            print("❌ 資料管理器未初始化")
            return
        
        while True:
            try:
                operation_type, operation_data = self.data_manager.get_test_data_operation()
                
                if operation_type is None:
                    break
                
                # 執行相應操作
                if operation_type == "add":
                    print("✅ 已新增測試資料到本地資料集")
                    
                elif operation_type == "edit":
                    print("✅ 已編輯測試資料")
                    
                elif operation_type == "delete":
                    print("✅ 已刪除測試資料")
                    
                elif operation_type == "batch_add":
                    print(f"✅ 已批量新增 {len(operation_data)} 筆測試資料")
                    
                elif operation_type == "view":
                    # 已在get_test_data_operation中顯示
                    pass
                    
                elif operation_type in ["export", "import", "search", "validate"]:
                    if operation_data:
                        print(f"✅ {operation_type} 操作完成: {operation_data}")
                
                # 詢問是否繼續
                continue_choice = input("\n是否繼續資料管理操作？(Y/n): ").strip().lower()
                if continue_choice == 'n':
                    break
                    
            except KeyboardInterrupt:
                print("\n資料管理操作已中斷")
                break
    
    async def handle_ai_assistant(self):
        """處理AI助手操作"""
        if not self.ai_assistant:
            print("❌ AI助手未啟用或初始化失敗")
            print("   請檢查zen-mcp-server配置或在設定中啟用AI功能")
            return
        
        print("\n🤖 AI助手功能:")
        print("  1. 💬 智能聊天")
        print("  2. 📊 資料分析")
        print("  3. 🔧 錯誤診斷")
        print("  4. 💡 操作建議")
        print("  0. 返回主選單")
        
        choice = input("請選擇AI功能 (0-4): ").strip()
        
        if choice == "1":
            await self.ai_assistant.interactive_chat()
            
        elif choice == "2":
            if self.data_manager and self.data_manager.current_dataset:
                print("🔄 正在分析當前資料集...")
                result = await self.ai_assistant.smart_data_validation(
                    [data.to_dict() for data in self.data_manager.current_dataset]
                )
                
                print("\n📊 AI分析結果:")
                print(f"  總記錄數: {result['total_records']}")
                print(f"  有效記錄: {result['valid_records']}")
                print(f"  無效記錄: {result['invalid_records']}")
                
                if result['errors']:
                    print("\n❌ 發現的錯誤:")
                    for error in result['errors'][:5]:  # 顯示前5個錯誤
                        print(f"  - {error}")
                
                if result['warnings']:
                    print("\n⚠️ 警告訊息:")
                    for warning in result['warnings'][:5]:  # 顯示前5個警告
                        print(f"  - {warning}")
            else:
                print("❌ 沒有資料可以分析")
                
        elif choice == "3":
            error_msg = input("請輸入錯誤訊息: ").strip()
            if error_msg:
                print("🔄 AI正在分析錯誤...")
                suggestion = await self.ai_assistant.help_with_error(error_msg)
                print(f"\n🤖 AI建議:\n{suggestion}")
            
        elif choice == "4":
            context = {
                "browser_connected": bool(self.browser_manager and self.browser_manager.browser_info),
                "data_count": len(self.data_manager.current_dataset) if self.data_manager else 0,
                "current_time": datetime.now().isoformat()
            }
            
            print("🔄 AI正在分析當前狀況...")
            suggestion = await self.ai_assistant.suggest_next_action(context)
            print(f"\n💡 AI建議:\n{suggestion}")
    
    async def handle_automation_operations(self):
        """處理自動化操作"""
        if not self.automation:
            print("❌ 請先啟動瀏覽器並連線到MMT010")
            return
        
        print("\n🧪 測試資料表格操作:")
        print("  1. ➕ 新增測試資料")
        print("  2. ✏️ 編輯測試資料")
        print("  3. 🗑️ 刪除測試資料")
        print("  4. 📦 批量新增資料")
        print("  5. 📋 查看表格資料")
        print("  6. 🔍 除錯頁面結構")
        print("  0. 返回主選單")
        
        choice = input("請選擇操作 (0-6): ").strip()
        
        if choice == "1":
            # 新增測試資料
            if self.data_manager:
                test_data = self.data_manager.input_test_data()
                if test_data:
                    success = await self.automation.add_new_test_data(test_data)
                    if success:
                        print("✅ 成功新增測試資料到MMT010系統")
                    else:
                        print("❌ 新增測試資料失敗")
            
        elif choice == "2":
            # 編輯測試資料
            row_id = input("請輸入要編輯的行號或識別碼: ").strip()
            if row_id and self.data_manager:
                test_data = self.data_manager.input_test_data(is_edit=True)
                if test_data:
                    try:
                        row_identifier = int(row_id) if row_id.isdigit() else row_id
                        success = await self.automation.edit_test_data(row_identifier, test_data)
                        if success:
                            print("✅ 成功編輯測試資料")
                        else:
                            print("❌ 編輯測試資料失敗")
                    except ValueError:
                        print("❌ 無效的行號")
            
        elif choice == "3":
            # 刪除測試資料
            row_id = input("請輸入要刪除的行號或識別碼: ").strip()
            if row_id:
                try:
                    row_identifier = int(row_id) if row_id.isdigit() else row_id
                    confirm = input(f"確定要刪除行 '{row_identifier}' 嗎？(y/N): ").strip().lower()
                    if confirm == 'y':
                        success = await self.automation.delete_test_data(row_identifier)
                        if success:
                            print("✅ 成功刪除測試資料")
                        else:
                            print("❌ 刪除測試資料失敗")
                    else:
                        print("❌ 已取消刪除操作")
                except ValueError:
                    print("❌ 無效的行號")
            
        elif choice == "4":
            # 批量新增資料
            if self.data_manager:
                batch_data = self.data_manager.input_batch_test_data()
                if batch_data:
                    print(f"🔄 開始批量新增 {len(batch_data)} 筆資料...")
                    result = await self.automation.batch_add_test_data(batch_data)
                    
                    if result["success"]:
                        print(f"✅ 批量新增完成: {result['success_count']}/{result['total']} 成功")
                        print(f"   成功率: {result['success_rate']:.1%}")
                    else:
                        print("❌ 批量新增失敗")
                        if "error" in result:
                            print(f"   錯誤: {result['error']}")
            
        elif choice == "5":
            # 查看表格資料
            result = await self.automation.view_test_data()
            if result["success"]:
                print(f"\n📊 表格資料概覽:")
                print(f"   總行數: {result['row_count']}")
                print(f"   欄位: {', '.join(result['headers'])}")
                
                if result["data"]:
                    print("\n前幾行資料:")
                    headers = result["headers"]
                    for i, row_data in enumerate(result["data"][:5], 1):
                        print(f"   {i}. {' | '.join(str(cell)[:20] for cell in row_data)}")
                    
                    if result["row_count"] > 5:
                        print(f"   ... 還有 {result['row_count'] - 5} 行")
            else:
                print(f"❌ 查看表格資料失敗: {result.get('error', '未知錯誤')}")
        
        elif choice == "6":
            # 除錯頁面結構
            debug_info = await self.automation.debug_page_structure()
            print("\n🔍 頁面結構分析:")
            for key, value in debug_info.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"     {sub_key}: {sub_value}")
                else:
                    print(f"   {key}: {value}")
    
    async def run_complete_workflow(self):
        """執行完整自動化流程"""
        print("\n🚀 執行完整自動化流程...")
        
        # 1. 確保瀏覽器連線
        if not self.automation:
            print("🔄 步驟 1: 啟動瀏覽器並連線...")
            success = await self.start_browser_and_connect()
            if not success:
                print("❌ 瀏覽器連線失敗，無法繼續")
                return
        
        # 2. 資料準備
        print("🔄 步驟 2: 準備測試資料...")
        if self.data_manager:
            data_choice = input("使用現有資料集還是輸入新資料？(existing/new): ").strip().lower()
            
            if data_choice == "new":
                test_data = self.data_manager.input_test_data()
                if test_data:
                    self.data_manager.current_dataset = [test_data]
                else:
                    print("❌ 沒有輸入測試資料")
                    return
            elif not self.data_manager.current_dataset:
                print("❌ 沒有可用的測試資料")
                return
        
        # 3. 執行搜尋
        print("🔄 步驟 3: 執行搜尋查詢...")
        search_success = await self.automation.click_search_button()
        if search_success:
            print("✅ 搜尋查詢完成")
        else:
            print("⚠️ 搜尋查詢失敗，繼續執行...")
        
        # 4. 資料操作
        print("🔄 步驟 4: 執行資料操作...")
        if self.data_manager.current_dataset:
            operation_choice = input("選擇操作 (add/edit/view): ").strip().lower()
            
            if operation_choice == "add":
                for i, test_data in enumerate(self.data_manager.current_dataset, 1):
                    print(f"   新增第 {i}/{len(self.data_manager.current_dataset)} 筆資料...")
                    await self.automation.add_new_test_data(test_data)
                    
            elif operation_choice == "view":
                result = await self.automation.view_test_data()
                if result["success"]:
                    print(f"✅ 表格中有 {result['row_count']} 筆資料")
        
        # 5. 儲存
        save_choice = input("是否執行儲存操作？(y/N): ").strip().lower()
        if save_choice == 'y':
            print("🔄 步驟 5: 執行儲存...")
            save_success = await self.automation.click_save_all_button()
            if save_success:
                print("✅ 儲存操作完成")
            else:
                print("⚠️ 儲存操作失敗")
        
        print("🎉 完整自動化流程執行完成！")
    
    def show_help(self):
        """顯示幫助資訊"""
        print("\n" + "="*70)
        print("📖 MT151_MSEDGE 使用說明")
        print("="*70)
        print("🎯 主要功能:")
        print("  1. 瀏覽器管理: 自動啟動和管理多種瀏覽器")
        print("  2. 資料管理: 測試資料的新增、編輯、驗證、匯入匯出")
        print("  3. AI助手: 智能分析、錯誤診斷、操作建議")
        print("  4. 自動化操作: MMT010系統的完整自動化控制")
        print()
        print("🔧 操作流程:")
        print("  1. 選擇選單項目 1 啟動瀏覽器並連線到MMT010")
        print("  2. 選擇選單項目 2 準備和管理測試資料")
        print("  3. 選擇選單項目 6 執行表格操作")
        print("  4. 選擇選單項目 5 儲存變更")
        print()
        print("💡 小技巧:")
        print("  - 使用AI助手分析資料品質")
        print("  - 批量操作可提高效率")
        print("  - 定期儲存避免資料遺失")
        print("  - 使用除錯功能診斷問題")
        print()
        print("❓ 如需更多幫助，請查看專案文件或聯繫開發團隊")
        print("="*70)
    
    def show_system_status(self):
        """顯示系統狀態"""
        print("\n" + "="*70)
        print("📋 系統狀態")
        print("="*70)
        
        # 基本資訊
        print(f"應用版本: {self.config.version}")
        print(f"設定檔案: {self.config}")
        print(f"除錯模式: {'啟用' if self.config.debug_mode else '停用'}")
        
        # 瀏覽器狀態
        if self.browser_manager and self.browser_manager.browser_info:
            browser_info = self.browser_manager.browser_info
            print(f"瀏覽器: ✅ {browser_info.name} ({browser_info.mode})")
        else:
            print("瀏覽器: ❌ 未連線")
        
        # 資料管理狀態
        if self.data_manager:
            dataset_count = len(self.data_manager.current_dataset)
            print(f"資料管理: ✅ {dataset_count} 筆資料")
        else:
            print("資料管理: ❌ 未初始化")
        
        # AI助手狀態
        if self.ai_assistant:
            print(f"AI助手: ✅ 已啟用 (模型: {self.config.ai.default_model})")
        else:
            print("AI助手: ❌ 未啟用")
        
        # 自動化狀態
        if self.automation:
            print("MMT010自動化: ✅ 已就緒")
        else:
            print("MMT010自動化: ❌ 未就緒")
        
        print("="*70)
    
    async def run(self):
        """運行主程式"""
        try:
            # 初始化
            self.show_welcome()
            await self.initialize_components()
            
            self.is_running = True
            
            # 主迴圈
            while self.is_running:
                try:
                    self.show_main_menu()
                    choice = self.get_menu_choice()
                    
                    if choice == 'Q':
                        self.is_running = False
                        break
                    
                    elif choice == '1':
                        await self.start_browser_and_connect()
                    
                    elif choice == '2':
                        await self.handle_data_management()
                    
                    elif choice == '3':
                        await self.handle_ai_assistant()
                    
                    elif choice == '4':
                        if self.automation:
                            await self.automation.click_search_button()
                        else:
                            print("❌ 請先啟動瀏覽器並連線到MMT010")
                    
                    elif choice == '5':
                        if self.automation:
                            await self.automation.click_save_all_button()
                        else:
                            print("❌ 請先啟動瀏覽器並連線到MMT010")
                    
                    elif choice == '6':
                        await self.handle_automation_operations()
                    
                    elif choice == '7':
                        await self.run_complete_workflow()
                    
                    elif choice == '8':
                        print("🔧 系統設定功能開發中...")
                    
                    elif choice == '9':
                        self.show_system_status()
                    
                    elif choice == 'H':
                        self.show_help()
                    
                    # 操作後暫停
                    if choice in ['1', '2', '3', '4', '5', '6', '7']:
                        input("\n按 Enter 鍵繼續...")
                        
                except KeyboardInterrupt:
                    print("\n操作已中斷")
                    continue
                except Exception as e:
                    self.logger.error(f"操作執行錯誤: {e}")
                    print(f"❌ 操作失敗: {e}")
                    input("按 Enter 鍵繼續...")
            
        except KeyboardInterrupt:
            print("\n程式被使用者中斷")
        except Exception as e:
            self.logger.error(f"主程式執行錯誤: {e}")
            print(f"❌ 程式執行失敗: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理資源"""
        try:
            self.logger.info("正在清理資源...")
            
            if self.data_manager:
                # 自動儲存資料
                if self.config.auto_save and self.data_manager.current_dataset:
                    self.data_manager.save_data()
            
            if self.browser_manager:
                await self.browser_manager.close()
            
            print("\n👋 感謝使用 MT151_MSEDGE！")
            self.logger.info("程式正常結束")
            
        except Exception as e:
            self.logger.error(f"清理資源時發生錯誤: {e}")


async def main():
    """主程式入口"""
    app = MT151App()
    await app.run()


if __name__ == "__main__":
    # 運行主程式
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"\n程式執行失敗: {e}")
        print("請檢查日誌檔案以獲取更多資訊")
    finally:
        print("程式已退出")