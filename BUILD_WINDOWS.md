# 打包 Windows 可執行檔教學

本專案可以打包成 Windows 可執行檔（.exe），讓您可以在沒有安裝 Python 的 Windows 電腦上運行。

## 方法 1: 使用自動化腳本（推薦）

### 在 Windows 上執行：

1. 確保已安裝 Python 3.8 或更高版本
2. 打開命令提示字元（CMD）或 PowerShell
3. 切換到專案目錄：
   ```bash
   cd path\to\test_cycle_scammer
   ```
4. 運行打包腳本：
   ```bash
   python build_windows.py
   ```
5. 等待打包完成，可執行檔會在 `dist` 資料夾中

## 方法 2: 手動打包

### 步驟：

1. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. 運行 PyInstaller：
   ```bash
   pyinstaller TestCycleAnalyzer.spec
   ```

3. 或使用單行命令：
   ```bash
   pyinstaller --name=TestCycleAnalyzer --onefile --windowed --hidden-import=matplotlib --hidden-import=numpy --hidden-import=webview --collect-all=matplotlib app.py
   ```

## 輸出位置

打包完成後，可執行檔會在以下位置：
```
dist/TestCycleAnalyzer.exe
```

## 注意事項

1. **在 Windows 上打包**：建議在 Windows 系統上進行打包，以確保最佳兼容性
2. **檔案大小**：打包後的 .exe 檔案可能會比較大（100-200 MB），這是正常的，因為包含了 Python 解釋器和所有依賴庫
3. **防毒軟體**：某些防毒軟體可能會誤報，這是因為 PyInstaller 打包的程式特性，屬於正常現象
4. **首次啟動**：第一次啟動可能需要較長時間，請耐心等待

## 測試

在打包前，確保程式在您的環境中正常運行：
```bash
python app.py
```

## 自訂圖示（可選）

如果您想要自訂應用程式圖示：

1. 準備一個 `.ico` 檔案（建議 256x256）
2. 將其放在專案資料夾中，例如命名為 `icon.ico`
3. 修改 `TestCycleAnalyzer.spec` 檔案中的 `icon=None` 為 `icon='icon.ico'`
4. 重新打包

## 疑難排解

### 問題：打包失敗，出現 "module not found" 錯誤
**解決方案**：確保所有依賴都已安裝
```bash
pip install -r requirements.txt
```

### 問題：執行檔運行時出現錯誤
**解決方案**：使用 console 模式重新打包以查看錯誤訊息
- 修改 `TestCycleAnalyzer.spec` 中的 `console=False` 為 `console=True`
- 重新打包並查看控制台輸出

### 問題：檔案太大
**解決方案**：使用 UPX 壓縮（已在 spec 中啟用）或考慮使用 `--onedir` 模式代替 `--onefile`

## 分發

打包完成後，您可以：
1. 直接分發 `dist/TestCycleAnalyzer.exe` 檔案
2. 如果使用 `--onedir` 模式，需要分發整個 `dist` 資料夾
3. 建議壓縮成 ZIP 檔案以便分享
