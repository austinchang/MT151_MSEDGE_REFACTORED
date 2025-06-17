"""
AI整合模組 - 透過zen-mcp-server整合XAI、Gemini、OpenAI模型

此模組提供與zen-mcp-server的整合，允許MT151_MSEDGE使用多種AI模型來：
- 智能分析測試資料
- 自動化決策建議
- 錯誤診斷和修復建議
- 自然語言處理用戶輸入
"""

import asyncio
import json
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import BaseModel


class AIModelConfig(BaseModel):
    """AI模型配置"""
    model_name: str = "auto"
    provider: str = "auto"  # auto, xai, gemini, openai
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class AIResponse(BaseModel):
    """AI回應結構"""
    success: bool
    content: str
    model_used: str
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class ZenMCPClient:
    """Zen MCP Server客戶端"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.zen_server_path = None
        self._find_zen_server()
    
    def _find_zen_server(self):
        """尋找zen-mcp-server的路徑"""
        potential_paths = [
            Path(__file__).parent.parent.parent / "zen-mcp-server",
            Path.home() / "projects" / "MCP" / "zen-mcp-server",
            Path("/home/tengjung_chang/projects/MCP/zen-mcp-server")
        ]
        
        for path in potential_paths:
            if path.exists() and (path / "server.py").exists():
                self.zen_server_path = path
                self.logger.info(f"找到zen-mcp-server: {path}")
                return
        
        self.logger.warning("未找到zen-mcp-server，部分AI功能可能無法使用")
    
    async def analyze_test_data(self, test_data: Dict[str, Any]) -> AIResponse:
        """使用AI分析測試資料"""
        prompt = f"""
        請分析以下測試資料的合理性和完整性：
        
        測試資料：
        {json.dumps(test_data, ensure_ascii=False, indent=2)}
        
        請檢查：
        1. 料號格式是否正確
        2. 站位配置是否合理
        3. 版本號格式是否符合規範
        4. 描述是否清晰明確
        5. 是否有潛在的配置衝突
        
        請提供分析結果和改善建議。
        """
        
        return await self._call_ai_tool("analyze", {
            "content": prompt,
            "focus": "data_validation"
        })
    
    async def suggest_automation_improvements(self, error_log: str) -> AIResponse:
        """根據錯誤日誌建議自動化改善"""
        prompt = f"""
        基於以下錯誤日誌，請提供自動化改善建議：
        
        錯誤日誌：
        {error_log}
        
        請分析：
        1. 錯誤的根本原因
        2. 可能的解決方案
        3. 預防性措施
        4. 自動化改善建議
        
        請提供具體的實施步驟。
        """
        
        return await self._call_ai_tool("debug", {
            "issue": prompt,
            "context": "web_automation"
        })
    
    async def generate_test_scenarios(self, base_data: Dict[str, Any]) -> AIResponse:
        """基於基礎資料生成測試場景"""
        prompt = f"""
        基於以下基礎測試資料，請生成多個測試場景：
        
        基礎資料：
        {json.dumps(base_data, ensure_ascii=False, indent=2)}
        
        請生成：
        1. 正常流程測試場景
        2. 邊界條件測試場景
        3. 異常情況測試場景
        4. 負載測試場景
        
        每個場景請包含具體的測試資料和預期結果。
        """
        
        return await self._call_ai_tool("testgen", {
            "code": json.dumps(base_data, ensure_ascii=False),
            "focus": "automation_scenarios"
        })
    
    async def chat_with_ai(self, user_message: str, context: Optional[str] = None) -> AIResponse:
        """與AI進行對話"""
        full_message = user_message
        if context:
            full_message = f"上下文：{context}\n\n用戶問題：{user_message}"
        
        return await self._call_ai_tool("chat", {
            "message": full_message
        })
    
    async def _call_ai_tool(self, tool_name: str, params: Dict[str, Any]) -> AIResponse:
        """調用AI工具"""
        if not self.zen_server_path:
            return AIResponse(
                success=False,
                content="",
                model_used="none",
                error="zen-mcp-server未找到"
            )
        
        try:
            # 準備調用zen-mcp-server
            tool_request = {
                "tool": tool_name,
                "parameters": params,
                "model": self.config.model_name,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            # 使用subprocess調用zen-mcp-server
            result = await self._execute_zen_tool(tool_request)
            
            return AIResponse(
                success=True,
                content=result.get("content", ""),
                model_used=result.get("model", "unknown"),
                token_usage=result.get("token_usage")
            )
            
        except Exception as e:
            self.logger.error(f"AI工具調用失敗: {e}")
            return AIResponse(
                success=False,
                content="",
                model_used="unknown",
                error=str(e)
            )
    
    async def _execute_zen_tool(self, tool_request: Dict[str, Any]) -> Dict[str, Any]:
        """執行zen工具"""
        # 這裡需要實現與zen-mcp-server的實際通信
        # 暫時返回模擬結果
        await asyncio.sleep(0.1)  # 模擬AI處理時間
        
        return {
            "content": f"AI分析結果：已處理{tool_request['tool']}請求",
            "model": self.config.model_name,
            "token_usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }


class AIAssistant:
    """AI助手主類"""
    
    def __init__(self, config: Optional[AIModelConfig] = None):
        self.config = config or AIModelConfig()
        self.client = ZenMCPClient(self.config)
        self.logger = logging.getLogger(__name__)
        
        # 設置日誌
        self._setup_logging()
    
    def _setup_logging(self):
        """設置日誌記錄"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def smart_data_validation(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """智能資料驗證"""
        self.logger.info(f"開始智能驗證 {len(test_data)} 筆測試資料")
        
        validation_results = {
            "total_records": len(test_data),
            "valid_records": 0,
            "invalid_records": 0,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        for i, data in enumerate(test_data):
            try:
                result = await self.client.analyze_test_data(data)
                
                if result.success:
                    # 解析AI分析結果
                    if "錯誤" in result.content or "無效" in result.content:
                        validation_results["invalid_records"] += 1
                        validation_results["errors"].append(f"記錄 {i+1}: {result.content}")
                    elif "警告" in result.content or "建議" in result.content:
                        validation_results["valid_records"] += 1
                        validation_results["warnings"].append(f"記錄 {i+1}: {result.content}")
                    else:
                        validation_results["valid_records"] += 1
                else:
                    validation_results["invalid_records"] += 1
                    validation_results["errors"].append(f"記錄 {i+1}: AI分析失敗 - {result.error}")
                    
            except Exception as e:
                validation_results["invalid_records"] += 1
                validation_results["errors"].append(f"記錄 {i+1}: 驗證異常 - {str(e)}")
        
        return validation_results
    
    async def suggest_next_action(self, current_context: Dict[str, Any]) -> str:
        """根據當前上下文建議下一步動作"""
        context_str = json.dumps(current_context, ensure_ascii=False, indent=2)
        
        result = await self.client.chat_with_ai(
            "根據當前的操作狀態，建議我下一步應該做什麼？",
            context_str
        )
        
        if result.success:
            return result.content
        else:
            return "AI建議服務暫時不可用，請手動選擇下一步操作。"
    
    async def help_with_error(self, error_message: str, context: Optional[str] = None) -> str:
        """協助處理錯誤"""
        result = await self.client.suggest_automation_improvements(
            f"錯誤訊息: {error_message}\n上下文: {context or '無'}"
        )
        
        if result.success:
            return result.content
        else:
            return f"無法獲取AI協助，原始錯誤：{error_message}"
    
    async def interactive_chat(self):
        """互動式聊天"""
        print("🤖 AI助手已準備就緒！輸入 'quit' 退出聊天。")
        
        while True:
            try:
                user_input = input("\n您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("🤖 AI助手: 再見！")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 AI助手: 思考中...")
                result = await self.client.chat_with_ai(user_input)
                
                if result.success:
                    print(f"🤖 AI助手: {result.content}")
                    if result.model_used != "unknown":
                        print(f"   (使用模型: {result.model_used})")
                else:
                    print(f"🤖 AI助手: 抱歉，發生錯誤: {result.error}")
                    
            except KeyboardInterrupt:
                print("\n🤖 AI助手: 聊天已中斷，再見！")
                break
            except Exception as e:
                print(f"🤖 AI助手: 發生異常: {e}")


# 便利函數
async def quick_analyze(data: Dict[str, Any]) -> str:
    """快速分析資料"""
    assistant = AIAssistant()
    result = await assistant.client.analyze_test_data(data)
    return result.content if result.success else f"分析失敗: {result.error}"


async def quick_chat(message: str) -> str:
    """快速聊天"""
    assistant = AIAssistant()
    result = await assistant.client.chat_with_ai(message)
    return result.content if result.success else f"聊天失敗: {result.error}"


if __name__ == "__main__":
    # 測試AI整合功能
    async def test_ai_integration():
        assistant = AIAssistant()
        
        # 測試資料分析
        test_data = {
            "料號": "C08GL0DIG017A",
            "站位": "B/I",
            "版本": "V3.3.5.9_1.16.0.1E3.12-1",
            "描述": "EN0DIGOA1-0322-GL_HL-325L B/I"
        }
        
        print("測試AI資料分析...")
        validation_result = await assistant.smart_data_validation([test_data])
        print(f"驗證結果: {validation_result}")
        
        # 測試聊天功能
        print("\n測試AI聊天功能...")
        chat_result = await quick_chat("請介紹一下MT151_MSEDGE專案的功能")
        print(f"AI回應: {chat_result}")
    
    # 運行測試
    asyncio.run(test_ai_integration())