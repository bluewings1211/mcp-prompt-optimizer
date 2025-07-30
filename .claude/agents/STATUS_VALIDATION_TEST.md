# Story Status Validation Test

這個測試用來驗證 sub-agents 是否正確執行狀態驗證，拒絕在錯誤狀態下執行工作。

## 測試目的

確保 sub-agents 遵守 BMAD Method 的狀態流程：
```
Draft → Approved → InProgress → Review → Done
```
只有在正確狀態下才執行相應的工作。

## 測試設置

建立多個測試 story 檔案，每個都有不同的狀態：

### Test Story 1: Draft Status
```markdown
# docs/stories/test-draft.md

# Story 1.1: Test Draft Story

## Status
[Draft]

## Story
**As a** test user,
**I want** to test draft validation,
**so that** developers don't work on unready stories.

## Acceptance Criteria
1. This story should not be implementable by Developer
2. This story should not be reviewable by QA

## Dev Notes
This is a test story in Draft status.
```

### Test Story 2: Approved Status
```markdown
# docs/stories/test-approved.md

# Story 1.2: Test Approved Story

## Status
[Approved]

## Story
**As a** test user,
**I want** to test approved validation,
**so that** proper workflow is followed.

## Acceptance Criteria
1. This story should be implementable by Developer
2. This story should NOT be reviewable by QA

## Dev Notes
This is a test story in Approved status.
```

### Test Story 3: InProgress Status
```markdown
# docs/stories/test-inprogress.md

# Story 1.3: Test InProgress Story

## Status
[InProgress]

## Story
**As a** test user,  
**I want** to test inprogress validation,
**so that** multiple developers don't work on same story.

## Acceptance Criteria
1. This story should NOT be implementable by another Developer
2. This story should NOT be reviewable by QA

## Dev Notes
This is a test story in InProgress status.
```

### Test Story 4: Review Status
```markdown
# docs/stories/test-review.md

# Story 1.4: Test Review Story

## Status
[Review]

## Story
**As a** test user,
**I want** to test review validation,
**so that** QA can review completed work.

## Acceptance Criteria
1. This story should NOT be implementable by Developer
2. This story should be reviewable by QA

## Dev Notes
This is a test story in Review status.
```

### Test Story 5: Done Status
```markdown
# docs/stories/test-done.md

# Story 1.5: Test Done Story

## Status
[Done]

## Story
**As a** test user,
**I want** to test done validation,
**so that** completed work is not modified.

## Acceptance Criteria
1. This story should NOT be implementable by Developer
2. This story should NOT be reviewable by QA

## Dev Notes
This is a test story in Done status.
```

## 狀態驗證測試

### Test 1: Developer Status Validation

#### Test 1.1: Developer with Draft Story
**觸發指令**: "Implement the test draft story"
**預期行為**:
- Developer 讀取 test-draft.md
- 檢查狀態發現是 [Draft]
- **REFUSE** 執行實作
- 回應: "Story status is [Draft]. I can only implement stories with [Approved] status."
- 建議: "Please have Scrum Master review and approve this story first."

#### Test 1.2: Developer with Approved Story
**觸發指令**: "Implement the test approved story"
**預期行為**:
- Developer 讀取 test-approved.md
- 檢查狀態發現是 [Approved]
- **PROCEED** 執行實作
- 更新狀態 [Approved] → [InProgress]

#### Test 1.3: Developer with InProgress Story
**觸發指令**: "Implement the test inprogress story"
**預期行為**:
- Developer 讀取 test-inprogress.md
- 檢查狀態發現是 [InProgress]
- **REFUSE** 執行實作
- 回應: "Story status is [InProgress]. I can only implement stories with [Approved] status."

#### Test 1.4: Developer with Review Story
**觸發指令**: "Implement the test review story"
**預期行為**:
- Developer 讀取 test-review.md
- 檢查狀態發現是 [Review]
- **REFUSE** 執行實作
- 回應: "Story status is [Review]. I can only implement stories with [Approved] status."

#### Test 1.5: Developer with Done Story
**觸發指令**: "Implement the test done story"
**預期行為**:
- Developer 讀取 test-done.md
- 檢查狀態發現是 [Done]
- **REFUSE** 執行實作
- 回應: "Story status is [Done]. I can only implement stories with [Approved] status."

### Test 2: QA Reviewer Status Validation

#### Test 2.1: QA with Draft Story
**觸發指令**: "Review the test draft story"
**預期行為**:
- QA Reviewer 讀取 test-draft.md
- 檢查狀態發現是 [Draft]
- **REFUSE** 執行審查
- 回應: "Story status is [Draft]. I can only review stories with [Review] status."
- 建議: "Please have Scrum Master approve this story first"

#### Test 2.2: QA with Approved Story
**觸發指令**: "Review the test approved story"
**預期行為**:
- QA Reviewer 讀取 test-approved.md
- 檢查狀態發現是 [Approved]
- **REFUSE** 執行審查
- 回應: "Story status is [Approved]. I can only review stories with [Review] status."
- 建議: "Please have Developer implement this story first"

#### Test 2.3: QA with InProgress Story
**觸發指令**: "Review the test inprogress story"
**預期行為**:
- QA Reviewer 讀取 test-inprogress.md
- 檢查狀態發現是 [InProgress]
- **REFUSE** 執行審查
- 回應: "Story status is [InProgress]. I can only review stories with [Review] status."
- 建議: "Please wait for Developer to complete implementation"

#### Test 2.4: QA with Review Story
**觸發指令**: "Review the test review story"
**預期行為**:
- QA Reviewer 讀取 test-review.md
- 檢查狀態發現是 [Review]
- **PROCEED** 執行審查
- 進行代碼審查流程

#### Test 2.5: QA with Done Story
**觸發指令**: "Review the test done story"
**預期行為**:
- QA Reviewer 讀取 test-done.md
- 檢查狀態發現是 [Done]
- **REFUSE** 執行審查
- 回應: "Story status is [Done]. I can only review stories with [Review] status."
- 建議: "This story has already been reviewed and completed"

### Test 3: Scrum Master Validation

#### Test 3.1: Scrum Master with Missing Planning Docs
**觸發指令**: "Create a story for user authentication"
**預期行為** (如果缺少 docs/prd.md 或 docs/architecture.md):
- Scrum Master 檢查規劃階段文件
- 發現文件缺失
- **HALT IMMEDIATELY**
- 回應: "Planning phase incomplete. Missing: [list of missing files]"
- 建議: "Please complete planning phase first"

## 驗證檢查清單

### Developer Status Validation
- [ ] ✅ 只接受 [Approved] 狀態的 story
- [ ] ❌ 拒絕 [Draft] 狀態的 story
- [ ] ❌ 拒絕 [InProgress] 狀態的 story
- [ ] ❌ 拒絕 [Review] 狀態的 story
- [ ] ❌ 拒絕 [Done] 狀態的 story
- [ ] 💬 提供清楚的拒絕理由和建議

### QA Reviewer Status Validation
- [ ] ❌ 拒絕 [Draft] 狀態的 story
- [ ] ❌ 拒絕 [Approved] 狀態的 story
- [ ] ❌ 拒絕 [InProgress] 狀態的 story
- [ ] ✅ 只接受 [Review] 狀態的 story
- [ ] ❌ 拒絕 [Done] 狀態的 story
- [ ] 💬 提供清楚的拒絕理由和建議

### Scrum Master Planning Validation
- [ ] ❌ 拒絕在規劃階段不完整時建立 story
- [ ] ✅ 驗證必要的規劃文件存在
- [ ] 💬 清楚說明缺少的文件和步驟

## 測試失敗情況

如果測試失敗（agents 沒有正確拒絕錯誤狀態），檢查：

1. **狀態讀取** - Agent 是否正確讀取並解析狀態
2. **驗證邏輯** - Agent 是否執行狀態驗證檢查
3. **拒絕機制** - Agent 是否在錯誤狀態時停止執行
4. **用戶溝通** - Agent 是否提供清楚的錯誤消息和建議

## 成功標準

測試通過條件：
1. 所有 agents 在錯誤狀態時都拒絕執行工作
2. 所有 agents 在正確狀態時都正常執行工作
3. 拒絕時提供清楚的理由和下一步建議
4. 狀態驗證發生在任何工作開始之前
5. 完全遵守 BMAD Method 的狀態流程

這確保了 sub-agents 完全遵循 BMAD 的品質閥門機制！