---
description: "Activates the STATUS_UPDATE_TEST agent persona."
tools: ['changes', 'codebase', 'fetch', 'findTestFiles', 'githubRepo', 'problems', 'usages', 'editFiles', 'runCommands', 'runTasks', 'runTests', 'search', 'searchResults', 'terminalLastCommand', 'terminalSelection', 'testFailure']
---

# Story Status Update Test

這個測試用來驗證 sub-agents 是否正確更新 story 檔案中的 Status。

## 測試用 Story 範例

建立測試 story 檔案：`docs/stories/test-story.md`

```markdown
# Story 1.1: User Registration

## Status
[Draft]

## Story
**As a** new user,
**I want** to register an account,
**so that** I can access the application.

## Acceptance Criteria
1. User can enter email and password
2. System validates email format
3. Password meets security requirements
4. Account is created successfully
5. User receives confirmation email

## Tasks / Subtasks
- [ ] Create registration form UI (AC: #1)
  - [ ] Email input field
  - [ ] Password input field
  - [ ] Submit button
- [ ] Implement form validation (AC: #2, #3)
  - [ ] Email format validation
  - [ ] Password strength validation
- [ ] Create user account (AC: #4)
  - [ ] Database user model
  - [ ] Registration API endpoint
- [ ] Send confirmation email (AC: #5)
  - [ ] Email service integration
  - [ ] Email template

## Dev Notes
- Use existing UI component library for form elements
- Password requirements: min 8 chars, 1 uppercase, 1 number
- Database: users table with email (unique), password_hash, created_at
- Email service: configured SMTP settings in environment
- Follow coding standards in docs/architecture/coding-standards.md

## Testing
- Unit tests for validation functions
- Integration tests for registration flow
- Email sending mock tests

## Change Log
- Story created by Scrum Master

## Dev Agent Record
### Checkboxes
- [ ] All tasks to be updated as completed

### Debug Log
- Implementation notes and decisions to be added here

### Completion Notes
- Summary of implementation approach to be added

### Change Log
- Code changes and file modifications to be documented
```

## Status 更新測試步驟

### 1. Scrum Master 測試
**觸發指令**: "Review and approve this test story"
**預期行為**: 
- 讀取 story 檔案
- 驗證 story 完整性
- 更新 Status: [Draft] → [Approved]

### 2. Developer 測試
**觸發指令**: "Implement the user registration story"
**預期行為**:
- 讀取 story 檔案
- 更新 Status: [Approved] → [InProgress] (開始時)
- 實作功能
- 更新任務 checkboxes
- 更新 Status: [InProgress] → [Review] (完成時)

### 3. QA Reviewer 測試
**觸發指令**: "Review the user registration implementation"
**預期行為**:
- 讀取 story 檔案和實作代碼
- 進行品質審查
- 更新 Status: [Review] → [Done] (通過) 或 [Review] → [InProgress] (需修改)

## 驗證檢查清單

### Scrum Master Status Update
- [ ] 讀取 story 檔案
- [ ] 使用 Edit tool 更新 Status section
- [ ] Status 正確從 [Draft] 變更為 [Approved]
- [ ] 其他內容保持不變

### Developer Status Updates
- [ ] 開始實作時更新 [Approved] → [InProgress]
- [ ] 更新任務 checkboxes 顯示進度
- [ ] 在 Dev Agent Record 部分記錄實作筆記
- [ ] 完成實作時更新 [InProgress] → [Review]

### QA Reviewer Status Decision
- [ ] 進行全面代碼審查
- [ ] 驗證所有 acceptance criteria
- [ ] 根據品質決定更新 Status:
  - 通過: [Review] → [Done]
  - 需修改: [Review] → [InProgress]
- [ ] 提供詳細回饋和改進建議

## 常見問題排除

### 如果 Status 沒有更新
1. **檢查 agent 是否正確啟動** - 確認觸發關鍵詞正確
2. **檢查檔案路徑** - 確認 story 檔案路徑正確
3. **檢查工具權限** - 確認 agent 有寫入權限
4. **檢查 Edit 指令** - 確認使用正確的 Edit tool 語法

### Status 更新語法範例

**正確的 Edit 語法**:
```
Edit tool:
- file_path: docs/stories/test-story.md
- old_string: ## Status
[Draft]
- new_string: ## Status
[Approved]
```

**錯誤的常見問題**:
- 忘記包含完整的 section header
- 空行或格式不一致
- 使用錯誤的狀態名稱

## 成功標準

測試通過條件：
1. 所有三個 agents 都能正確識別和讀取 story 檔案
2. 每個 agent 在適當時機自動使用 Edit tool 更新 Status
3. Status 轉換遵循正確的流程: Draft → Approved → InProgress → Review → Done
4. Story 檔案的其他內容在更新過程中保持完整
5. 每個 agent 提供適當的實作/審查回饋

如果測試失敗，回到相應的 sub-agent 配置檔案檢查 "Story Status Updates (Critical)" 部分的指示是否清楚明確。