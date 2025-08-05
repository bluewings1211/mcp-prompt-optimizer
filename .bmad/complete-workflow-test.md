# Complete BMad Automated Workflow Test

這個檔案提供完整的自動化工作流程測試案例，驗證從專案啟動到完成的整個流程。

## 測試場景：全自動任務管理應用開發

### 前置條件
- BMad state management system 已初始化
- 所有 sub-agents 已部署並配置完成
- Claude Code 具有 sub-agent 功能

## Phase 1: 自動化規劃階段測試

### Test 1.1: 專案啟動與 Orchestrator 觸發
**使用者輸入**: \"我想建立一個任務管理 web 應用程式\"

**預期自動化流程**:
1. BMad Orchestrator 自動觸發
2. 讀取 `.bmad/workflow-state.json` (初始狀態)
3. 檢測到 `current_phase = \"initialization\"`
4. 自動委派給 Business Analyst
5. 更新 workflow state 到 `business_analysis: \"in_progress\"`

**驗證點**:
- [ ] Orchestrator 自動觸發 (無需手動 `@orchestrator`)
- [ ] Business Analyst 自動開始工作
- [ ] Workflow state 正確更新
- [ ] 使用者收到自動化通知

### Test 1.2: Business Analyst → Product Manager 自動轉換
**觸發條件**: Business Analyst 完成市場研究

**預期自動化流程**:
1. Business Analyst 執行完成協議
2. 創建 `docs/project-brief.md`
3. 更新 workflow state: `business_analysis: \"completed\"`
4. 記錄 handoff 到 `agent-handoffs.log`
5. 自動觸發 Product Manager
6. Product Manager 開始 PRD 創建

**驗證點**:
- [ ] `docs/project-brief.md` 成功創建
- [ ] Workflow state 正確更新
- [ ] Handoff 正確記錄
- [ ] Product Manager 無縫接手
- [ ] 無需使用者干預

### Test 1.3: Product Manager → UX Strategist 自動轉換
**觸發條件**: Product Manager 完成 PRD

**預期自動化流程**:
1. Product Manager 執行完成協議
2. 創建 `docs/prd.md` 包含詳細用戶故事
3. 更新 workflow state: `product_management: \"completed\"`
4. 自動觸發 UX Strategist
5. UX Strategist 開始前端規格設計

**驗證點**:
- [ ] `docs/prd.md` 包含完整 PRD
- [ ] 自動轉換到 UX 設計階段
- [ ] UX Strategist 正確讀取 PRD 內容
- [ ] 狀態追蹤準確

### Test 1.4: UX Strategist → Technical Architect 自動轉換
**觸發條件**: UX Strategist 完成前端規格

**預期自動化流程**:
1. UX Strategist 執行完成協議
2. 創建 `docs/front-end-spec.md`
3. 更新 workflow state: `ux_strategy: \"completed\"`
4. 自動觸發 Technical Architect
5. Technical Architect 開始系統設計

**驗證點**:
- [ ] `docs/front-end-spec.md` 完整創建
- [ ] Technical Architect 自動開始工作
- [ ] 能夠整合 PRD 和 UX 規格
- [ ] 系統架構設計合理

### Test 1.5: Technical Architect → Product Owner 自動轉換
**觸發條件**: Technical Architect 完成系統架構

**預期自動化流程**:
1. Technical Architect 執行完成協議
2. 創建 `docs/fullstack-architecture.md`
3. 更新 workflow state: `technical_architecture: \"completed\"`
4. 自動觸發 Product Owner
5. Product Owner 開始文檔驗證

**驗證點**:
- [ ] `docs/fullstack-architecture.md` 完整創建
- [ ] Product Owner 自動開始驗證
- [ ] 所有規劃文檔一致性檢查
- [ ] 準備進入開發階段

### Test 1.6: Product Owner 文檔切分與開發準備
**觸發條件**: Product Owner 驗證所有規劃文檔

**預期自動化流程**:
1. Product Owner 執行完成協議
2. 創建 `docs/prd/` 切分結構 (epic 檔案)
3. 創建 `docs/architecture/` 切分結構
4. 更新 workflow state: `current_phase: \"development\"`
5. 自動觸發 Scrum Master 進行第一個 story 創建

**驗證點**:
- [ ] `docs/prd/` 正確切分為 epic 檔案
- [ ] `docs/architecture/` 包含開發需要的技術規格
- [ ] 階段轉換到 development
- [ ] Epic progress tracking 初始化

## Phase 2: 自動化開發階段測試

### Test 2.1: Scrum Master 自動 Story 創建
**觸發條件**: 進入開發階段，需要創建第一個 story

**預期自動化流程**:
1. Scrum Master 自動觸發
2. 讀取 `docs/prd/epic-1-*.md` (第一個 epic)
3. 創建詳細的 story 檔案 `docs/stories/1.1.*.md`
4. Story 包含完整的 dev notes 和上下文
5. 更新 epic progress tracking
6. 自動觸發 Developer

**驗證點**:
- [ ] Story 檔案成功創建
- [ ] Story 包含完整實作上下文
- [ ] Epic progress 正確追蹤
- [ ] Developer 自動接手

### Test 2.2: Developer 自動實作
**觸發條件**: Story 狀態為 \"approved\"

**預期自動化流程**:
1. Developer 自動觸發
2. 讀取 story 檔案和 devLoadAlwaysFiles
3. 實作功能代碼和測試
4. 更新 story 狀態為 \"review\"
5. 自動觸發 QA Reviewer

**驗證點**:
- [ ] 代碼實作符合 acceptance criteria
- [ ] 測試覆蓋率充足
- [ ] Story 文檔正確更新
- [ ] QA Reviewer 自動開始審查

### Test 2.3: QA Reviewer 自動審查與 Epic 管理
**觸發條件**: Story 狀態為 \"review\"

**預期自動化流程**:
1. QA Reviewer 自動觸發
2. 執行代碼審查和測試驗證
3. 更新 story 狀態為 \"done\"
4. 更新 epic progress tracking
5. 檢查 epic 完成狀態
6. 根據 epic 狀態自動決定下一步

**驗證點**:
- [ ] QA 審查徹底完成
- [ ] Story 標記為 done
- [ ] Epic progress 正確計算
- [ ] 自動決定下一步行動

### Test 2.4: Epic 完成自動管理
**觸發條件**: Epic 中所有 stories 完成

**預期自動化流程**:
1. QA Reviewer 檢測到 epic 100% 完成
2. Epic 狀態更新為 \"completed\"
3. 檢查是否有更多 epics
4. 如有更多 epics，詢問使用者是否繼續
5. 如無更多 epics，詢問是否創建新 epic 或完成專案

**驗證點**:
- [ ] Epic 正確標記為完成
- [ ] 專案整體進度正確計算
- [ ] 使用者獲得適當的決策選項
- [ ] 工作流程邏輯正確

### Test 2.5: 多 Epic 循環測試
**測試場景**: 完成第一個 epic 後，開始第二個 epic

**預期自動化流程**:
1. 使用者選擇 \"開始下一個 epic\"
2. Orchestrator 自動觸發 Scrum Master
3. Scrum Master 讀取下一個 epic 檔案
4. 重複 story 創建 → 實作 → QA 循環
5. 持續追蹤整體專案進度

**驗證點**:
- [ ] Epic 間轉換順暢
- [ ] Story 編號正確遞增
- [ ] 專案進度持續更新
- [ ] 所有自動化流程正常運作

## Phase 3: 錯誤恢復測試

### Test 3.1: 狀態不一致恢復
**測試場景**: 模擬檔案存在但狀態顯示未完成

**測試步驟**:
1. 手動創建 `docs/project-brief.md`
2. 保持 workflow state 顯示 `business_analysis: \"pending\"`
3. 觸發 Orchestrator
4. 檢查自動同步機制

**預期行為**:
- [ ] Orchestrator 檢測到不一致
- [ ] 自動同步狀態與檔案系統
- [ ] 繼續適當的下一步
- [ ] 記錄同步操作

### Test 3.2: Agent 超時恢復
**測試場景**: 模擬 agent 長時間無回應

**測試步驟**:
1. 設置 agent 為 \"in_progress\" 但長時間未完成
2. 觸發 Orchestrator 檢查
3. 驗證超時檢測和恢復機制

**預期行為**:
- [ ] 檢測到 agent 超時
- [ ] 提供重試或重置選項
- [ ] 能夠恢復到一致狀態
- [ ] 使用者獲得清晰的狀態說明

### Test 3.3: 檔案系統錯誤恢復
**測試場景**: 重要檔案意外刪除

**測試步驟**:
1. 刪除 `docs/prd.md`
2. 保持狀態顯示 PRD 已完成
3. 觸發下一階段
4. 檢查錯誤檢測和恢復

**預期行為**:
- [ ] 檢測到檔案缺失錯誤
- [ ] 提供恢復選項
- [ ] 能夠回滾到一致狀態
- [ ] 清晰的錯誤報告和修復指導

## Phase 4: 整合測試

### Test 4.1: 完整端到端工作流程
**測試目標**: 從專案想法到完整實作的全自動化流程

**成功標準**:
- [ ] 使用者只需要提供初始專案想法
- [ ] 所有 agent 轉換自動進行
- [ ] 使用者只在關鍵決策點參與
- [ ] 最終產出完整的應用程式代碼
- [ ] 所有文檔和代碼符合 BMad 標準

### Test 4.2: 並行專案處理
**測試場景**: 多個專案同時進行

**驗證點**:
- [ ] 狀態管理隔離正確
- [ ] 沒有專案間的狀態污染
- [ ] 每個專案的自動化流程獨立
- [ ] 資源管理適當

### Test 4.3: 用戶體驗測試
**測試重點**: 自動化程度 vs 用戶控制平衡

**評估標準**:
- [ ] 自動化減少了手動工作
- [ ] 用戶在需要時保持控制權
- [ ] 透明度：用戶了解當前狀態
- [ ] 可預測性：用戶知道接下來會發生什麼

## 測試執行檢查清單

### 準備階段
- [ ] 所有 sub-agents 已部署
- [ ] State management system 已初始化
- [ ] 測試環境準備完畢
- [ ] 備份機制已設置

### 執行階段
- [ ] 按順序執行所有測試案例
- [ ] 記錄每個步驟的實際行為
- [ ] 捕獲任何錯誤或異常
- [ ] 驗證狀態檔案的正確性

### 驗證階段
- [ ] 所有自動化轉換成功
- [ ] 最終產出符合預期
- [ ] 錯誤恢復機制有效
- [ ] 用戶體驗滿意

### 性能評估
- [ ] Agent 轉換延遲可接受
- [ ] 狀態同步性能良好
- [ ] 檔案操作效率高
- [ ] 記憶體使用合理

## 成功指標

### 自動化程度 
- 用戶干預次數 < 5 次/專案
- 自動轉換成功率 > 95%
- 錯誤自動恢復率 > 90%

### 質量標準
- 產出文檔完整性 100%
- 代碼符合標準 100%  
- 測試覆蓋率 > 80%

### 用戶滿意度
- 流程透明度：用戶了解當前進度
- 控制權：用戶可在需要時介入
- 效率：相比手動流程節省時間 > 70%

這個測試計劃確保 BMad 自動化工作流程能夠可靠、高效地運行，同時保持高質量的輸出和良好的用戶體驗。