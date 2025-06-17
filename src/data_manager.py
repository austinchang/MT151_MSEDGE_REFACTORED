"""
資料管理模組

管理測試資料的載入、儲存、驗證和操作，包括：
- 預設資料管理
- 自訂資料輸入
- 批量資料處理
- 資料驗證
- 檔案匯入/匯出
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from config import DataConfig, get_data_config


class TestData(BaseModel):
    """測試資料模型"""
    料號: str = Field(..., description="產品料號")
    站位: str = Field(..., description="測試站位")
    版本: str = Field(..., description="軟體版本")
    描述: str = Field(..., description="產品描述")
    MFGID群組: str = Field(default="DEFAULT", description="製造群組")
    
    # 元資料
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    source: str = Field(default="manual", description="資料來源")
    
    @validator('料號')
    def validate_part_number(cls, v):
        if not v or len(v) < 3:
            raise ValueError('料號不能為空且至少3個字符')
        return v.strip().upper()
    
    @validator('站位')
    def validate_station(cls, v):
        allowed_stations = ["B/I", "FT", "PT", "SHIP", "BI"]
        if v not in allowed_stations:
            raise ValueError(f'站位必須為 {allowed_stations} 之一')
        return v
    
    @validator('版本')
    def validate_version(cls, v):
        if not v or len(v) < 5:
            raise ValueError('版本號不能為空且至少5個字符')
        return v.strip()
    
    @validator('描述')
    def validate_description(cls, v):
        if not v or len(v) < 3:
            raise ValueError('描述不能為空且至少3個字符')
        return v.strip()
    
    def to_dict(self) -> Dict[str, str]:
        """轉換為字典（僅包含主要欄位）"""
        return {
            "料號": self.料號,
            "站位": self.站位,
            "版本": self.版本,
            "描述": self.描述,
            "MFGID群組": self.MFGID群組
        }


class ValidationResult(BaseModel):
    """驗證結果模型"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0, description="資料品質分數 0-100")


class DataManager:
    """資料管理類別"""
    
    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or get_data_config()
        self.data_file_path = Path(self.config.data_file_path)
        self.backup_path = Path(self.config.backup_data_path)
        
        # 確保目錄存在
        self._ensure_directories()
        
        # 載入預設資料
        self.default_data = TestData(**self.config.default_test_data)
        
        # 當前資料集
        self.current_dataset: List[TestData] = []
        
        # 載入已存在的資料
        self.load_data()
    
    def _ensure_directories(self):
        """確保必要目錄存在"""
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    def show_data_menu(self):
        """顯示資料選項選單"""
        print("\n" + "="*70)
        print("📋 請選擇資料填寫方式:")
        print("="*70)
        print("  1. 📄 使用預設資料")
        print("  2. ✏️  手動輸入新資料") 
        print("  3. 🔧 修改部分預設資料")
        print("  4. 📁 從檔案載入資料")
        print("  5. 📊 查看當前資料集")
        print("  6. 🧹 清空當前資料集")
        print("  0. ⏭️  跳過資料填寫")
        print("="*70)
        
        # 顯示當前預設資料
        print("\n📄 當前預設資料:")
        default_dict = self.default_data.to_dict()
        for key, value in default_dict.items():
            print(f"  {key}: {value}")
        
        # 顯示當前資料集統計
        print(f"\n📊 當前資料集: {len(self.current_dataset)} 筆資料")
        print()
    
    def show_test_data_menu(self):
        """顯示測試資料操作選單"""
        print("\n" + "="*70)
        print("🧪 請選擇測試資料操作:")
        print("="*70)
        print("  1. ➕ 新增單筆測試資料")
        print("  2. ✏️  編輯現有測試資料")
        print("  3. 🗑️  刪除測試資料")
        print("  4. 🔧 批量新增測試資料")
        print("  5. 📋 查看現有測試資料")
        print("  6. 💾 匯出測試資料") 
        print("  7. 📁 匯入測試資料")
        print("  8. 🔍 搜尋測試資料")
        print("  9. ✅ 驗證資料品質")
        print("  0. ⏭️  跳過測試資料操作")
        print("="*70)
        print(f"\n📊 當前資料集: {len(self.current_dataset)} 筆測試資料")
        print()
    
    def get_data_choice(self) -> Optional[str]:
        """獲取資料選擇"""
        while True:
            try:
                choice = input("請輸入選項 (0-6): ").strip()
                if choice in ["0", "1", "2", "3", "4", "5", "6"]:
                    return choice
                else:
                    print("❌ 無效選項，請重新輸入")
            except KeyboardInterrupt:
                print("\n程式已取消")
                return None
    
    def get_test_data_choice(self) -> Optional[str]:
        """獲取測試資料操作選擇"""
        while True:
            try:
                choice = input("請輸入選項 (0-9): ").strip()
                if choice in [str(i) for i in range(10)]:
                    return choice
                else:
                    print("❌ 無效選項，請重新輸入")
            except KeyboardInterrupt:
                print("\n程式已取消")
                return None
    
    def get_fill_data(self) -> Optional[TestData]:
        """根據用戶選擇獲取要填寫的資料"""
        self.show_data_menu()
        choice = self.get_data_choice()
        
        if choice is None or choice == "0":
            return None
        elif choice == "1":
            print("✅ 使用預設資料")
            return self.default_data.copy()
        elif choice == "2":
            return self.input_custom_data()
        elif choice == "3":
            return self.modify_default_data()
        elif choice == "4":
            return self.load_data_from_file()
        elif choice == "5":
            self.show_current_dataset()
            return self.get_fill_data()  # 遞迴重新顯示選單
        elif choice == "6":
            self.clear_current_dataset()
            return self.get_fill_data()  # 遞迴重新顯示選單
        
        return None
    
    def get_test_data_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """獲取測試資料操作選擇"""
        self.show_test_data_menu()
        choice = self.get_test_data_choice()
        
        if choice is None or choice == "0":
            return None, None
        elif choice == "1":
            # 新增單筆測試資料
            test_data = self.input_test_data()
            if test_data:
                self.current_dataset.append(test_data)
                return "add", test_data
            return None, None
        elif choice == "2":
            # 編輯現有測試資料
            return self._handle_edit_operation()
        elif choice == "3":
            # 刪除測試資料
            return self._handle_delete_operation()
        elif choice == "4":
            # 批量新增測試資料
            batch_data = self.input_batch_test_data()
            if batch_data:
                self.current_dataset.extend(batch_data)
                return "batch_add", batch_data
            return None, None
        elif choice == "5":
            # 查看現有測試資料
            self.show_current_dataset()
            return "view", None
        elif choice == "6":
            # 匯出測試資料
            return self._handle_export_operation()
        elif choice == "7":
            # 匯入測試資料
            return self._handle_import_operation()
        elif choice == "8":
            # 搜尋測試資料
            return self._handle_search_operation()
        elif choice == "9":
            # 驗證資料品質
            return self._handle_validation_operation()
        
        return None, None
    
    def input_test_data(self, is_edit: bool = False, existing_data: Optional[TestData] = None) -> Optional[TestData]:
        """讓用戶輸入測試資料"""
        operation = "編輯" if is_edit else "新增"
        print(f"\n🧪 請輸入{operation}的測試資料 (按 Enter 跳過該欄位):")
        print("📋 可填寫的欄位: 料號, 站位, 版本, 描述, MFGID群組")
        print("-" * 50)
        
        # 準備預設值
        defaults = existing_data.to_dict() if existing_data else self.default_data.to_dict()
        
        # 收集用戶輸入
        data_input = {}
        fields = ["料號", "站位", "版本", "描述", "MFGID群組"]
        
        for field in fields:
            try:
                current_value = defaults.get(field, "")
                
                if current_value and not is_edit:
                    prompt = f"{field} (預設: {current_value}): "
                else:
                    prompt = f"{field}: "
                
                value = input(prompt).strip()
                
                if value:
                    data_input[field] = value
                    print(f"  ✅ 已設定 {field}: {value}")
                elif current_value and not is_edit:
                    data_input[field] = current_value
                    print(f"  📄 使用預設 {field}: {current_value}")
                else:
                    if is_edit:
                        print(f"  ⏭️  跳過 {field} (不修改)")
                    else:
                        print(f"  ⏭️  跳過 {field}")
                        
            except KeyboardInterrupt:
                print("\n輸入已取消")
                return None
        
        if not data_input:
            print("⚠️  沒有輸入任何資料")
            return None
        
        try:
            # 如果是編輯模式，合併現有資料
            if is_edit and existing_data:
                merged_data = existing_data.to_dict()
                merged_data.update(data_input)
                data_input = merged_data
            
            # 建立TestData物件
            test_data = TestData(**data_input)
            test_data.source = "manual_edit" if is_edit else "manual"
            test_data.updated_at = datetime.now()
            
            print(f"\n🧪 您輸入的{operation}資料:")
            for key, value in test_data.to_dict().items():
                print(f"  {key}: {value}")
            
            return test_data
            
        except Exception as e:
            print(f"❌ 資料驗證失敗: {e}")
            return None
    
    def input_batch_test_data(self) -> Optional[List[TestData]]:
        """讓用戶輸入批量測試資料"""
        print("\n📦 批量新增測試資料:")
        print("請輸入要新增的資料筆數")
        print("-" * 40)
        
        try:
            count_input = input("要新增幾筆資料? (預設: 1): ").strip()
            count = int(count_input) if count_input.isdigit() else 1
            
            if count <= 0 or count > 50:
                print("❌ 無效的數量，請輸入1-50之間的數字")
                return None
            
            batch_data = []
            for i in range(count):
                print(f"\n--- 第 {i+1} 筆資料 ---")
                test_data = self.input_test_data()
                
                if test_data:
                    batch_data.append(test_data)
                    print(f"✅ 第 {i+1} 筆資料已準備")
                else:
                    print(f"⏭️  跳過第 {i+1} 筆資料")
            
            print(f"\n📦 批量資料準備完成，共 {len(batch_data)} 筆")
            return batch_data if batch_data else None
            
        except KeyboardInterrupt:
            print("\n批量輸入已取消")
            return None
        except ValueError:
            print("❌ 無效的數量，使用預設值 1")
            return [self.input_test_data()] if self.input_test_data() else None
    
    def input_custom_data(self) -> Optional[TestData]:
        """讓用戶手動輸入資料"""
        print("\n✏️  請輸入新的搜尋資料 (按 Enter 跳過該欄位):")
        print("-" * 40)
        
        return self.input_test_data()
    
    def modify_default_data(self) -> Optional[TestData]:
        """讓用戶修改部分預設資料"""
        print("\n🔧 修改預設資料 (按 Enter 保持原值):")
        print("-" * 40)
        
        return self.input_test_data(is_edit=True, existing_data=self.default_data)
    
    def validate_data(self, data: TestData) -> ValidationResult:
        """驗證單筆資料"""
        result = ValidationResult(is_valid=True)
        
        try:
            # 基本驗證（已在TestData模型中完成）
            result.score += 40
            
            # 進階驗證規則
            validation_rules = self.config.validation_rules
            
            # 料號驗證
            if "料號" in validation_rules:
                rule = validation_rules["料號"]
                if "pattern" in rule:
                    if not re.match(rule["pattern"], data.料號):
                        result.errors.append(f"料號格式不符合規則: {rule['description']}")
                        result.is_valid = False
                    else:
                        result.score += 15
            
            # 站位驗證
            if "站位" in validation_rules:
                rule = validation_rules["站位"]
                if "allowed_values" in rule:
                    if data.站位 not in rule["allowed_values"]:
                        result.errors.append(f"站位必須為 {rule['allowed_values']} 之一")
                        result.is_valid = False
                    else:
                        result.score += 15
            
            # 版本號驗證
            if "版本" in validation_rules:
                rule = validation_rules["版本"]
                if "pattern" in rule:
                    if not re.match(rule["pattern"], data.版本):
                        result.warnings.append(f"版本號格式可能不標準: {rule['description']}")
                    else:
                        result.score += 15
            
            # 描述長度驗證
            if "描述" in validation_rules:
                rule = validation_rules["描述"]
                if "min_length" in rule:
                    if len(data.描述) < rule["min_length"]:
                        result.warnings.append(f"描述過短，建議至少 {rule['min_length']} 個字符")
                    else:
                        result.score += 15
            
            # 重複性檢查
            duplicates = self.find_duplicates(data)
            if duplicates:
                result.warnings.append(f"發現 {len(duplicates)} 筆相似資料")
            
            # 品質建議
            if result.score >= 90:
                result.suggestions.append("資料品質優良")
            elif result.score >= 70:
                result.suggestions.append("資料品質良好，可考慮完善某些欄位")
            else:
                result.suggestions.append("建議檢查和完善資料內容")
                
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"驗證過程發生錯誤: {e}")
            result.score = 0
        
        return result
    
    def find_duplicates(self, target_data: TestData, threshold: float = 0.8) -> List[TestData]:
        """尋找重複或相似的資料"""
        duplicates = []
        
        for data in self.current_dataset:
            similarity = self._calculate_similarity(target_data, data)
            if similarity >= threshold:
                duplicates.append(data)
        
        return duplicates
    
    def _calculate_similarity(self, data1: TestData, data2: TestData) -> float:
        """計算兩筆資料的相似度"""
        if data1.料號 == data2.料號 and data1.站位 == data2.站位:
            return 1.0  # 完全重複
        
        # 簡單的相似度計算
        matches = 0
        total = 5
        
        if data1.料號 == data2.料號: matches += 1
        if data1.站位 == data2.站位: matches += 1
        if data1.版本 == data2.版本: matches += 1
        if data1.描述 == data2.描述: matches += 1
        if data1.MFGID群組 == data2.MFGID群組: matches += 1
        
        return matches / total
    
    def show_current_dataset(self):
        """顯示當前資料集"""
        if not self.current_dataset:
            print("📊 當前資料集為空")
            return
        
        print(f"\n📊 當前資料集 ({len(self.current_dataset)} 筆):")
        print("="*80)
        print(f"{'#':<3} | {'料號':<15} | {'站位':<5} | {'版本':<25} | {'描述':<20}")
        print("-"*80)
        
        for i, data in enumerate(self.current_dataset[:20], 1):  # 限制顯示20筆
            print(f"{i:<3} | {data.料號:<15} | {data.站位:<5} | {data.版本:<25} | {data.描述[:20]:<20}")
        
        if len(self.current_dataset) > 20:
            print(f"... 還有 {len(self.current_dataset) - 20} 筆資料")
        
        print("="*80)
    
    def clear_current_dataset(self):
        """清空當前資料集"""
        if self.current_dataset:
            confirm = input(f"確定要清空 {len(self.current_dataset)} 筆資料？(y/N): ").strip().lower()
            if confirm == 'y':
                self.current_dataset.clear()
                print("✅ 資料集已清空")
            else:
                print("❌ 已取消清空操作")
        else:
            print("📊 資料集已經是空的")
    
    def save_data(self, backup: bool = True) -> bool:
        """儲存資料到檔案"""
        try:
            if backup and self.data_file_path.exists():
                # 建立備份
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_path / f"data_backup_{timestamp}.json"
                backup_file.write_text(self.data_file_path.read_text(), encoding='utf-8')
                print(f"📁 已建立備份: {backup_file}")
            
            # 準備儲存資料
            save_data = {
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "total_records": len(self.current_dataset),
                    "version": "2.0.0"
                },
                "data": [data.dict() for data in self.current_dataset]
            }
            
            # 儲存到檔案
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ 已儲存 {len(self.current_dataset)} 筆資料到 {self.data_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 儲存資料失敗: {e}")
            return False
    
    def load_data(self) -> bool:
        """從檔案載入資料"""
        if not self.data_file_path.exists():
            print("📝 資料檔案不存在，開始使用空資料集")
            return True
        
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # 載入資料記錄
            if "data" in loaded_data:
                self.current_dataset.clear()
                for item in loaded_data["data"]:
                    try:
                        test_data = TestData(**item)
                        self.current_dataset.append(test_data)
                    except Exception as e:
                        print(f"⚠️  跳過無效資料: {e}")
            
            print(f"✅ 已載入 {len(self.current_dataset)} 筆資料")
            return True
            
        except Exception as e:
            print(f"❌ 載入資料失敗: {e}")
            return False
    
    def load_data_from_file(self) -> Optional[TestData]:
        """從檔案載入資料（用於填寫）"""
        self.load_data()
        if self.current_dataset:
            print(f"✅ 已載入 {len(self.current_dataset)} 筆資料")
            return self.current_dataset[0] if self.current_dataset else None
        return None
    
    def _handle_edit_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理編輯操作"""
        if not self.current_dataset:
            print("❌ 沒有資料可以編輯")
            return None, None
        
        self.show_current_dataset()
        
        try:
            index_input = input("請輸入要編輯的資料編號: ").strip()
            index = int(index_input) - 1
            
            if 0 <= index < len(self.current_dataset):
                existing_data = self.current_dataset[index]
                print(f"\n編輯第 {index + 1} 筆資料:")
                
                new_data = self.input_test_data(is_edit=True, existing_data=existing_data)
                if new_data:
                    self.current_dataset[index] = new_data
                    return "edit", {"index": index, "data": new_data}
            else:
                print("❌ 無效的編號")
                
        except ValueError:
            print("❌ 請輸入有效的數字")
        except KeyboardInterrupt:
            print("\n編輯已取消")
        
        return None, None
    
    def _handle_delete_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理刪除操作"""
        if not self.current_dataset:
            print("❌ 沒有資料可以刪除")
            return None, None
        
        self.show_current_dataset()
        
        try:
            index_input = input("請輸入要刪除的資料編號: ").strip()
            index = int(index_input) - 1
            
            if 0 <= index < len(self.current_dataset):
                data_to_delete = self.current_dataset[index]
                print(f"\n要刪除的資料:")
                for key, value in data_to_delete.to_dict().items():
                    print(f"  {key}: {value}")
                
                confirm = input("\n確定要刪除這筆資料？(y/N): ").strip().lower()
                if confirm == 'y':
                    deleted_data = self.current_dataset.pop(index)
                    return "delete", {"index": index, "data": deleted_data}
                else:
                    print("❌ 已取消刪除")
            else:
                print("❌ 無效的編號")
                
        except ValueError:
            print("❌ 請輸入有效的數字")
        except KeyboardInterrupt:
            print("\n刪除已取消")
        
        return None, None
    
    def _handle_export_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理匯出操作"""
        if not self.current_dataset:
            print("❌ 沒有資料可以匯出")
            return None, None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = self.backup_path / f"export_{timestamp}.json"
            
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(self.current_dataset),
                "data": [data.dict() for data in self.current_dataset]
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ 已匯出 {len(self.current_dataset)} 筆資料到 {export_file}")
            return "export", {"file": str(export_file), "count": len(self.current_dataset)}
            
        except Exception as e:
            print(f"❌ 匯出失敗: {e}")
            return None, None
    
    def _handle_import_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理匯入操作"""
        print("📁 匯入資料功能")
        file_path = input("請輸入要匯入的檔案路徑: ").strip()
        
        if not file_path:
            print("❌ 未指定檔案路徑")
            return None, None
        
        try:
            import_path = Path(file_path)
            if not import_path.exists():
                print(f"❌ 檔案不存在: {file_path}")
                return None, None
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_count = 0
            if "data" in import_data:
                for item in import_data["data"]:
                    try:
                        test_data = TestData(**item)
                        self.current_dataset.append(test_data)
                        imported_count += 1
                    except Exception as e:
                        print(f"⚠️  跳過無效資料: {e}")
            
            print(f"✅ 已匯入 {imported_count} 筆資料")
            return "import", {"file": file_path, "count": imported_count}
            
        except Exception as e:
            print(f"❌ 匯入失敗: {e}")
            return None, None
    
    def _handle_search_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理搜尋操作"""
        if not self.current_dataset:
            print("❌ 沒有資料可以搜尋")
            return None, None
        
        search_term = input("請輸入搜尋關鍵字: ").strip()
        if not search_term:
            print("❌ 未輸入搜尋關鍵字")
            return None, None
        
        results = []
        for i, data in enumerate(self.current_dataset):
            data_dict = data.to_dict()
            for value in data_dict.values():
                if search_term.lower() in str(value).lower():
                    results.append((i, data))
                    break
        
        if results:
            print(f"\n🔍 搜尋結果 ({len(results)} 筆):")
            print("-" * 60)
            for i, (index, data) in enumerate(results[:10], 1):
                print(f"{i}. (#{index+1}) {data.料號} - {data.站位} - {data.描述[:30]}")
            
            if len(results) > 10:
                print(f"... 還有 {len(results) - 10} 筆結果")
        else:
            print("🔍 沒有找到符合的資料")
        
        return "search", {"term": search_term, "results": results}
    
    def _handle_validation_operation(self) -> tuple[Optional[str], Optional[Any]]:
        """處理驗證操作"""
        if not self.current_dataset:
            print("❌ 沒有資料可以驗證")
            return None, None
        
        print("🔄 正在驗證資料品質...")
        
        total_score = 0
        error_count = 0
        warning_count = 0
        
        for i, data in enumerate(self.current_dataset):
            result = self.validate_data(data)
            total_score += result.score
            error_count += len(result.errors)
            warning_count += len(result.warnings)
            
            if not result.is_valid:
                print(f"❌ 第 {i+1} 筆資料有錯誤:")
                for error in result.errors:
                    print(f"   - {error}")
        
        avg_score = total_score / len(self.current_dataset) if self.current_dataset else 0
        
        print(f"\n✅ 驗證完成:")
        print(f"   總資料: {len(self.current_dataset)} 筆")
        print(f"   平均品質分數: {avg_score:.1f}/100")
        print(f"   錯誤總數: {error_count}")
        print(f"   警告總數: {warning_count}")
        
        return "validate", {
            "total": len(self.current_dataset),
            "avg_score": avg_score,
            "errors": error_count,
            "warnings": warning_count
        }


if __name__ == "__main__":
    # 測試資料管理器
    print("🧪 測試資料管理器...")
    
    manager = DataManager()
    
    # 測試基本功能
    print(f"預設資料: {manager.default_data.to_dict()}")
    print(f"當前資料集: {len(manager.current_dataset)} 筆")
    
    # 測試資料驗證
    test_data = TestData(
        料號="C08GL0DIG017A",
        站位="B/I",
        版本="V3.3.5.9_1.16.0.1E3.12-1",
        描述="EN0DIGOA1-0322-GL_HL-325L B/I"
    )
    
    validation_result = manager.validate_data(test_data)
    print(f"驗證結果: 有效={validation_result.is_valid}, 分數={validation_result.score}")
    
    print("\n✅ 資料管理器測試完成")