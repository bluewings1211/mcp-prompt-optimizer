# Agent Completion Protocol Templates

這個檔案包含各 sub-agent 的標準化完成協議模板。

## UX Strategist Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your frontend specification is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["planning"]["ux_strategy"] = "completed"
workflow_state["current_stage"] = "technical_architecture"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "technical-architect",
    "description": "Create system architecture and technical specifications",
    "priority": "high",
    "user_confirmation_required": false
}

# Update artifact status
workflow_state["artifacts"]["planning_docs"]["frontend_spec"] = true

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "ux-strategist",
    "to_agent": "technical-architect",
    "deliverable": "docs/front-end-spec.md",
    "status": "completed",
    "notes": "Frontend specification and UX design completed. Ready for technical architecture."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 3: Notify User and Trigger Next Phase
```markdown
✅ **Frontend Specification Complete**

**Deliverable Created:** docs/front-end-spec.md
**Next Step:** System Architecture by Technical Architect
**Status:** Automatically triggering Technical Architect for system design

The BMad Orchestrator will now coordinate the technical architecture phase.
```
```

## Technical Architect Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your system architecture is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["planning"]["technical_architecture"] = "completed"
workflow_state["current_stage"] = "product_owner_validation"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "product-owner",
    "description": "Validate all planning artifacts and prepare for development",
    "priority": "high",
    "user_confirmation_required": false
}

# Update artifact status
workflow_state["artifacts"]["planning_docs"]["architecture"] = true

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "technical-architect",
    "to_agent": "product-owner",
    "deliverable": "docs/fullstack-architecture.md",
    "status": "completed",
    "notes": "System architecture and technical specifications completed. Ready for validation and development preparation."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 3: Notify User and Trigger Next Phase
```markdown
✅ **System Architecture Complete**

**Deliverable Created:** docs/fullstack-architecture.md
**Next Step:** Document Validation by Product Owner
**Status:** Automatically triggering Product Owner for planning validation

The BMad Orchestrator will now coordinate the validation and development preparation phase.
```
```

## Product Owner Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your document validation and sharding is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["planning"]["product_owner_validation"] = "completed"
workflow_state["current_phase"] = "development"
workflow_state["current_stage"] = "story_creation"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "scrum-master",
    "description": "Create first user story from sharded epics",
    "priority": "high",
    "user_confirmation_required": false
}

# Update artifact status
workflow_state["artifacts"]["development_structure"]["prd_sharded"] = true
workflow_state["artifacts"]["development_structure"]["architecture_sharded"] = true

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "product-owner",
    "to_agent": "scrum-master",
    "deliverable": "docs/prd/ and docs/architecture/ (sharded)",
    "status": "completed",
    "notes": "Planning documents validated and sharded. Ready for development phase."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 3: Notify User and Trigger Next Phase
```markdown
✅ **Planning Phase Complete - Development Ready**

**Deliverables Created:** Sharded documents in docs/prd/ and docs/architecture/
**Next Step:** Story Creation by Scrum Master
**Status:** Automatically transitioning to Development Phase

The BMad Orchestrator will now coordinate the development phase starting with story creation.
```
```

## Scrum Master Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your story creation is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["development"]["story_status"] = "approved"
workflow_state["current_stage"] = "story_implementation"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "developer",
    "description": "Implement the approved user story",
    "priority": "high",
    "user_confirmation_required": false
}

# Update artifact status
workflow_state["artifacts"]["development_structure"]["stories_created"] = true

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "scrum-master",
    "to_agent": "developer",
    "deliverable": "docs/stories/[story-file].md",
    "status": "completed",
    "notes": "User story with complete context and dev notes created. Ready for implementation."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 3: Notify User and Trigger Next Phase
```markdown
✅ **Story Creation Complete**

**Deliverable Created:** docs/stories/[story-file].md
**Next Step:** Implementation by Developer
**Status:** Automatically triggering Developer for code implementation

The BMad Orchestrator will now coordinate the implementation phase.
```
```

## Developer Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your implementation is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["development"]["story_status"] = "review"
workflow_state["current_stage"] = "qa_review"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "qa-reviewer",
    "description": "Review implementation and validate acceptance criteria",
    "priority": "high",
    "user_confirmation_required": false
}

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "developer",
    "to_agent": "qa-reviewer",
    "deliverable": "Code implementation + updated story file",
    "status": "completed",
    "notes": "Story implementation completed with tests. Ready for QA review."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 3: Notify User and Trigger Next Phase
```markdown
✅ **Implementation Complete**

**Deliverables:** Code implementation and updated story documentation
**Next Step:** Quality Assurance by QA Reviewer
**Status:** Automatically triggering QA Reviewer for code review

The BMad Orchestrator will now coordinate the quality assurance phase.
```
```

## QA Reviewer Completion Protocol

```markdown
## Instructions - Execute on EVERY Completion

**MANDATORY COMPLETION PROTOCOL:**

When your QA review is complete, you MUST execute this protocol:

### Step 1: Update Workflow State
```python
# Read current state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["development"]["story_status"] = "done"
workflow_state["current_stage"] = "epic_management"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "orchestrator",
    "description": "Check epic completion and manage next steps",
    "priority": "high",
    "user_confirmation_required": true
}

write_json(".bmad/workflow-state.json", workflow_state)
```

### Step 2: Update Epic Progress
```python
# Update epic progress tracking
epic_progress = read_json(".bmad/epic-progress.json")
# Update story status to completed
# Check if epic is complete
# Update completion statistics

write_json(".bmad/epic-progress.json", epic_progress)
```

### Step 3: Log Agent Handoff
```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "qa-reviewer", 
    "to_agent": "orchestrator",
    "deliverable": "Validated implementation + QA report",
    "status": "completed",
    "notes": "QA review completed. Story marked as done. Epic management needed."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

### Step 4: Notify User and Check Epic Status
```markdown
✅ **QA Review Complete - Story Done**

**Deliverables:** Validated code and comprehensive QA report
**Story Status:** Marked as "Done"
**Next Step:** Epic completion check by BMad Orchestrator

The BMad Orchestrator will now determine if more stories are needed or if the epic is complete.
```
```