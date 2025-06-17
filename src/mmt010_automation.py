"""
MMT010自動化操作模組

基於Version20程式碼重構，提供MMT010系統的完整自動化操作功能：
- 網頁導航和登入處理
- 測試資料的新增、編輯、刪除
- 批量資料操作
- DevExpress表格元件處理
- 錯誤處理和重試機制
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Page, Locator

from config import WebConfig, get_web_config
from data_manager import TestData


class MMT010Automation:
    """MMT010生產線產測版本控管系統自動化操作類別"""
    
    def __init__(self, page: Page, config: Optional[WebConfig] = None):
        self.page = page
        self.config = config or get_web_config()
        self.logger = logging.getLogger(__name__)
        
        # 欄位映射
        self.column_mapping = self.config.column_mapping
        
        # DevExpress表格選擇器
        self.grid_container = self.page.locator(self.config.selectors["grid_container"])
        self.data_rows = self.grid_container.locator(self.config.selectors["data_row"])
        self.header_row = self.grid_container.locator(self.config.selectors["header_row"])
        
        # 操作按鈕選擇器
        self.search_button = self.page.locator(self.config.selectors["search_button"])
        self.save_all_button = self.page.locator(self.config.selectors["save_all_button"])
        
        # 設置預設超時
        self.page.set_default_timeout(self.config.element_timeout)
    
    async def navigate_to_mmt010(self) -> bool:
        """導航到MMT010系統"""
        try:
            self.logger.info("正在導航到MMT010系統...")
            
            await self.page.goto(
                self.config.base_url, 
                timeout=self.config.page_load_timeout
            )
            
            # 等待頁面載入完成
            await self.page.wait_for_load_state(
                'networkidle', 
                timeout=self.config.page_load_timeout
            )
            
            self.logger.info("✅ 成功導航到MMT010系統")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 導航到MMT010失敗: {e}")
            return False
    
    async def wait_for_login(self) -> bool:
        """等待用戶登入"""
        try:
            # 檢查是否有密碼輸入框
            password_inputs = await self.page.locator(
                self.config.selectors["password_input"]
            ).count()
            
            if password_inputs > 0:
                print("⚠️  檢測到登入頁面，請手動登入後繼續...")
                
                # 等待URL變更為登入後的頁面
                await self.page.wait_for_url(
                    "**/MMT010_Index*", 
                    timeout=self.config.login_timeout
                )
                
                print("✅ 登入完成，繼續執行...")
                
                # 額外等待頁面完全載入
                await self.page.wait_for_load_state(
                    'networkidle', 
                    timeout=30000
                )
            
            self.logger.info("登入檢查完成")
            return True
            
        except Exception as e:
            self.logger.error(f"等待登入時發生錯誤: {e}")
            return False
    
    async def click_search_button(self) -> bool:
        """點擊查詢按鈕"""
        try:
            self.logger.info("🔍 正在點擊查詢按鈕...")
            
            # 等待按鈕可見
            await self.search_button.wait_for(
                state='visible', 
                timeout=self.config.element_timeout
            )
            
            # 點擊查詢按鈕
            await self.search_button.click()
            
            # 等待搜尋完成
            await asyncio.sleep(3)
            
            self.logger.info("✅ 查詢按鈕點擊成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 點擊查詢按鈕失敗: {e}")
            return False
    
    async def click_save_all_button(self) -> bool:
        """點擊儲存全部按鈕"""
        try:
            self.logger.info("💾 正在點擊儲存全部按鈕...")
            
            # 等待按鈕可見
            await self.save_all_button.wait_for(
                state='visible',
                timeout=self.config.element_timeout
            )
            
            # 點擊儲存按鈕
            await self.save_all_button.click()
            
            # 等待儲存完成
            await asyncio.sleep(3)
            
            self.logger.info("✅ 儲存全部按鈕點擊成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 點擊儲存全部按鈕失敗: {e}")
            return False
    
    async def wait_for_grid_ready(self) -> bool:
        """等待表格準備就緒"""
        try:
            self.logger.info("等待表格載入...")
            
            # 等待表格容器出現
            await self.grid_container.wait_for(
                state='visible',
                timeout=self.config.element_timeout
            )
            
            # 等待表格完全載入
            await asyncio.sleep(2)
            
            self.logger.info("✅ 表格已準備就緒")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 等待表格準備失敗: {e}")
            return False
    
    async def get_grid_info(self) -> Dict[str, Any]:
        """獲取表格資訊"""
        try:
            # 確保表格已載入
            if not await self.wait_for_grid_ready():
                return {"error": "表格未準備就緒"}
            
            # 獲取資料行數量
            row_count = await self.data_rows.count()
            
            # 獲取表頭資訊
            headers = []
            if await self.header_row.count() > 0:
                header_cells = self.header_row.locator('td')
                header_count = await header_cells.count()
                
                for i in range(min(header_count, 6)):  # 限制前6欄
                    try:
                        header_text = await header_cells.nth(i).text_content()
                        headers.append(header_text.strip() if header_text else f"欄位{i+1}")
                    except:
                        headers.append(f"欄位{i+1}")
            
            grid_info = {
                "row_count": row_count,
                "headers": headers,
                "grid_ready": True
            }
            
            self.logger.info(f"表格資訊: {row_count} 行, {len(headers)} 欄")
            return grid_info
            
        except Exception as e:
            self.logger.error(f"獲取表格資訊失敗: {e}")
            return {"error": str(e), "grid_ready": False}
    
    async def find_grid_row(self, row_identifier: Union[int, str]) -> Optional[Locator]:
        """在表格中尋找指定的行"""
        try:
            # 確保表格準備就緒
            if not await self.wait_for_grid_ready():
                return None
            
            if isinstance(row_identifier, int):
                # 按行號查找
                self.logger.info(f"正在查找第 {row_identifier} 個資料列...")
                
                # DevExpress的資料列索引從0開始
                row_locator = self.data_rows.nth(row_identifier - 1)
                
                if await row_locator.count() > 0:
                    return row_locator
                else:
                    self.logger.warning(f"第 {row_identifier} 行不存在")
                    return None
            
            else:
                # 按文字內容查找
                self.logger.info(f"正在查找包含 '{row_identifier}' 的資料列...")
                
                row_locator = self.data_rows.filter(has_text=row_identifier).first
                
                if await row_locator.count() > 0:
                    return row_locator
                else:
                    self.logger.warning(f"未找到包含 '{row_identifier}' 的行")
                    return None
                    
        except Exception as e:
            self.logger.error(f"查找行時出錯: {e}")
            return None
    
    async def fill_single_cell(self, row_locator: Locator, column_name: str, value: str) -> bool:
        """填寫單個儲存格"""
        try:
            if column_name not in self.column_mapping:
                self.logger.warning(f"未知欄位: {column_name}")
                return False
            
            col_index = self.column_mapping[column_name]
            self.logger.info(f"正在填寫欄位 '{column_name}' (第{col_index}欄): {value}")
            
            # 定位儲存格
            cell_locator = row_locator.locator(f'td:nth-child({col_index + 1})')
            
            if await cell_locator.count() == 0:
                self.logger.error(f"找不到第 {col_index + 1} 個儲存格")
                return False
            
            # 雙擊儲存格進入編輯模式
            await cell_locator.dblclick()
            await asyncio.sleep(0.5)
            
            # 尋找輸入框
            input_editor = cell_locator.locator('input[type="text"]:visible')
            
            try:
                await input_editor.wait_for(state='visible', timeout=5000)
            except:
                self.logger.error(f"儲存格 {column_name} 的輸入框未出現")
                # 嘗試點擊頁面其他地方取消編輯
                await self.page.locator('body').click()
                return False
            
            # 清空並填入新值
            await input_editor.fill(str(value))
            
            # 按Enter確認
            await input_editor.press('Enter')
            await asyncio.sleep(1)
            
            self.logger.info(f"✅ 欄位 '{column_name}' 填寫成功")
            return True
            
        except Exception as e:
            self.logger.error(f"填寫儲存格時出錯: {e}")
            return False
    
    async def add_new_test_data(self, test_data: TestData) -> bool:
        """新增測試資料到表格"""
        try:
            self.logger.info("➕ 正在新增測試資料到表格...")
            
            # 確保表格準備就緒
            if not await self.wait_for_grid_ready():
                return False
            
            # 尋找新增按鈕
            add_button_selectors = [
                '[id$="_DXCBtnNew"]',
                '[id*="New"]',
                'input[value="新增"]',
                'a[title*="新增"]'
            ]
            
            add_button = None
            for selector in add_button_selectors:
                potential_button = self.grid_container.locator(selector)
                if await potential_button.count() > 0:
                    add_button = potential_button.first
                    break
            
            if add_button:
                self.logger.info("找到新增按鈕，點擊...")
                await add_button.click()
                await asyncio.sleep(2)
            else:
                self.logger.info("未找到新增按鈕，嘗試直接在空行填寫...")
            
            # 尋找空行或新建的行進行填寫
            data_dict = test_data.to_dict()
            success_count = 0
            
            # 嘗試在最後一行填寫
            row_count = await self.data_rows.count()
            
            if row_count > 0:
                # 嘗試最後一行
                last_row = self.data_rows.nth(row_count - 1)
                await last_row.click()
                await asyncio.sleep(0.5)
            else:
                # 如果沒有行，可能需要先觸發新增
                self.logger.warning("表格中沒有資料行")
                return False
            
            # 填寫各個欄位
            for field_name, field_value in data_dict.items():
                if field_name in self.column_mapping:
                    success = await self.fill_single_cell(last_row, field_name, field_value)
                    if success:
                        success_count += 1
            
            success_rate = success_count / len(data_dict)
            
            if success_rate >= 0.8:  # 80%以上成功率視為成功
                self.logger.info(f"🎉 成功新增測試資料 ({success_count}/{len(data_dict)} 欄位)")
                return True
            else:
                self.logger.warning(f"⚠️ 部分新增成功 ({success_count}/{len(data_dict)} 欄位)")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 新增測試資料失敗: {e}")
            return False
    
    async def edit_test_data(self, row_identifier: Union[int, str], test_data: TestData) -> bool:
        """編輯測試資料"""
        try:
            self.logger.info(f"✏️ 正在編輯測試資料 (目標行: {row_identifier})...")
            
            # 找到目標行
            row_locator = await self.find_grid_row(row_identifier)
            if not row_locator:
                self.logger.error(f"找不到指定行: {row_identifier}")
                return False
            
            # 點擊選中該行
            await row_locator.click()
            await asyncio.sleep(0.5)
            
            # 填寫各個欄位
            data_dict = test_data.to_dict()
            success_count = 0
            
            for field_name, field_value in data_dict.items():
                if field_name in self.column_mapping:
                    self.logger.info(f"正在處理欄位 '{field_name}'...")
                    success = await self.fill_single_cell(row_locator, field_name, field_value)
                    if success:
                        success_count += 1
                    else:
                        self.logger.warning(f"欄位 '{field_name}' 更新失敗")
            
            # 計算成功率
            success_rate = success_count / len(data_dict)
            
            if success_rate >= 0.8:
                self.logger.info(f"🎉 成功編輯測試資料 ({success_count}/{len(data_dict)} 欄位)")
                return True
            elif success_count > 0:
                self.logger.warning(f"⚠️ 部分編輯成功 ({success_count}/{len(data_dict)} 欄位)")
                return True
            else:
                self.logger.error("❌ 未能更新任何欄位")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 編輯測試資料失敗: {e}")
            return False
    
    async def delete_test_data(self, row_identifier: Union[int, str]) -> bool:
        """刪除測試資料"""
        try:
            self.logger.info(f"🗑️ 正在刪除測試資料 (行: {row_identifier})...")
            
            # 找到目標行
            row_locator = await self.find_grid_row(row_identifier)
            if not row_locator:
                self.logger.error(f"找不到指定行: {row_identifier}")
                return False
            
            # 選中該行
            await row_locator.click()
            await asyncio.sleep(0.5)
            
            # 尋找刪除按鈕
            delete_button_selectors = [
                '[id$="_DXCBtnDelete"]',
                '[id*="Delete"]',
                'input[value="刪除"]',
                'a[title*="刪除"]'
            ]
            
            delete_button = None
            for selector in delete_button_selectors:
                potential_button = self.grid_container.locator(selector)
                if await potential_button.count() > 0:
                    delete_button = potential_button.first
                    break
            
            if delete_button:
                await delete_button.click()
                self.logger.info("✅ 已點擊刪除按鈕")
                
                # 等待可能的確認對話框
                await asyncio.sleep(2)
                
                # 檢查是否有確認對話框
                confirm_buttons = self.page.locator('button:has-text("確定"), button:has-text("OK"), button:has-text("是")')
                if await confirm_buttons.count() > 0:
                    await confirm_buttons.first.click()
                    self.logger.info("已確認刪除")
                
                return True
            else:
                self.logger.error("找不到刪除按鈕")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 刪除測試資料失敗: {e}")
            return False
    
    async def view_test_data(self) -> Dict[str, Any]:
        """查看現有測試資料"""
        try:
            self.logger.info("📋 正在查看現有測試資料...")
            
            # 獲取表格資訊
            grid_info = await self.get_grid_info()
            
            if not grid_info.get("grid_ready", False):
                return {"success": False, "error": "表格未準備就緒"}
            
            row_count = grid_info["row_count"]
            headers = grid_info["headers"]
            
            if row_count == 0:
                self.logger.info("📊 測試資料表格目前是空的")
                return {
                    "success": True,
                    "row_count": 0,
                    "headers": headers,
                    "data": []
                }
            
            # 讀取前10行資料作為預覽
            preview_data = []
            max_preview = min(row_count, 10)
            
            for i in range(max_preview):
                try:
                    row = self.data_rows.nth(i)
                    cells = row.locator('td')
                    cell_count = await cells.count()
                    
                    row_data = []
                    for j in range(min(cell_count, 6)):  # 限制前6欄
                        try:
                            cell_text = await cells.nth(j).text_content()
                            row_data.append(cell_text.strip() if cell_text else "")
                        except:
                            row_data.append("")
                    
                    preview_data.append(row_data)
                    
                except Exception as e:
                    self.logger.warning(f"讀取第 {i+1} 行資料失敗: {e}")
                    preview_data.append(["讀取失敗"] * 6)
            
            result = {
                "success": True,
                "row_count": row_count,
                "headers": headers,
                "preview_count": len(preview_data),
                "data": preview_data
            }
            
            self.logger.info(f"📊 成功讀取 {row_count} 筆測試資料")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 查看測試資料失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_add_test_data(self, test_data_list: List[TestData]) -> Dict[str, Any]:
        """批量新增測試資料"""
        try:
            self.logger.info(f"📦 開始批量新增 {len(test_data_list)} 筆測試資料...")
            
            success_count = 0
            failed_count = 0
            results = []
            
            for i, test_data in enumerate(test_data_list, 1):
                self.logger.info(f"處理第 {i}/{len(test_data_list)} 筆資料...")
                
                success = await self.add_new_test_data(test_data)
                
                if success:
                    success_count += 1
                    results.append({"index": i, "status": "success", "data": test_data.to_dict()})
                else:
                    failed_count += 1
                    results.append({"index": i, "status": "failed", "data": test_data.to_dict()})
                
                # 批量操作間的延遲
                if i < len(test_data_list):
                    await asyncio.sleep(1)
            
            batch_result = {
                "success": success_count > 0,
                "total": len(test_data_list),
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / len(test_data_list) if test_data_list else 0,
                "details": results
            }
            
            self.logger.info(f"📦 批量新增完成: {success_count}/{len(test_data_list)} 成功")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"❌ 批量新增失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "total": len(test_data_list),
                "success_count": 0,
                "failed_count": len(test_data_list)
            }
    
    async def search_and_filter(self, search_criteria: Dict[str, str]) -> bool:
        """搜尋和篩選資料"""
        try:
            self.logger.info("🔍 執行搜尋和篩選...")
            
            # 這裡需要根據實際的搜尋介面實現
            # 暫時只點擊搜尋按鈕
            return await self.click_search_button()
            
        except Exception as e:
            self.logger.error(f"❌ 搜尋篩選失敗: {e}")
            return False
    
    async def take_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """擷取當前頁面截圖"""
        try:
            if filename is None:
                timestamp = int(asyncio.get_event_loop().time())
                filename = f"logs/mmt010_screenshot_{timestamp}.png"
            
            await self.page.screenshot(path=filename, full_page=True)
            self.logger.info(f"📸 截圖已儲存: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"❌ 截圖失敗: {e}")
            return None
    
    async def debug_page_structure(self) -> Dict[str, Any]:
        """除錯模式：分析頁面結構"""
        try:
            self.logger.info("🔍 正在分析頁面結構...")
            
            # 基本頁面資訊
            page_title = await self.page.title()
            page_url = self.page.url
            
            # 表格相關元素
            grid_count = await self.grid_container.count()
            data_row_count = await self.data_rows.count()
            
            # 按鈕元素
            search_btn_count = await self.search_button.count()
            save_btn_count = await self.save_all_button.count()
            
            # 所有表格相關元素
            all_tables = await self.page.locator('table').count()
            all_grids = await self.page.locator('[id*="Grid"], [class*="grid"]').count()
            
            debug_info = {
                "page_title": page_title,
                "page_url": page_url,
                "grid_container_count": grid_count,
                "data_row_count": data_row_count,
                "search_button_count": search_btn_count,
                "save_button_count": save_btn_count,
                "all_tables_count": all_tables,
                "all_grids_count": all_grids,
                "selectors": self.config.selectors,
                "column_mapping": self.column_mapping
            }
            
            self.logger.info("🔍 頁面結構分析完成")
            return debug_info
            
        except Exception as e:
            self.logger.error(f"❌ 頁面結構分析失敗: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # 這裡可以放置測試代碼
    print("MMT010自動化操作模組已載入")
    print("此模組需要配合browser_manager和data_manager使用")