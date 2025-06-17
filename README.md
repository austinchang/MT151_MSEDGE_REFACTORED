# MT151_MSEDGE 重構版本

## 專案概述
MT151_MSEDGE是一個基於Playwright的web自動化項目，用於自動化操作MMT010生產線產測版本控管系統。

## 主要功能
- 🚀 自動化登入MMT010系統
- 📊 測試資料管理（新增、編輯、刪除、查看）
- 🔄 批量操作支援
- 🌐 多瀏覽器支援（Edge、Chrome、Firefox）
- 🤖 AI模型整合（XAI、Gemini、OpenAI透過zen-mcp-server）
- 📝 完整的中文操作介面

## 技術架構
- **前端自動化**: Playwright (async/await)
- **瀏覽器支援**: Chromium, Firefox, Webkit
- **AI整合**: zen-mcp-server
- **資料處理**: Python類別化設計
- **UI互動**: DevExpress表格組件處理

## 安裝要求
- Python 3.8+
- Playwright
- 相關瀏覽器驅動程式

## 快速開始
```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝Playwright瀏覽器
playwright install

# 運行主程式
python src/main.py
```

## 版本歷史
請參考 [CHANGELOG.md](CHANGELOG.md) 查看詳細的版本更新記錄。

## 貢獻
歡迎提交Issue和Pull Request來改善這個專案。

## 授權
本專案採用MIT授權條款。