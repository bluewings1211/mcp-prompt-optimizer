# BMad State Management System

This directory contains the automated state management system for BMad Method workflow coordination.

## Files Overview

### Core State Files

#### `workflow-state.json`
**Purpose**: Main workflow state tracking
- Current phase (planning/development/completed)
- Stage within phase (business-analysis, story-implementation, etc.)
- Active agent and next actions
- Artifact completion status

#### `agent-handoffs.log` 
**Purpose**: Agent communication and handoff tracking
- Record of all agent transitions
- Deliverable handoff status
- Timing and performance metrics

#### `epic-progress.json`
**Purpose**: Development phase progress tracking  
- Epic completion status
- Story-level progress within epics
- Project completion percentage
- Development velocity metrics

#### `project-metadata.json`
**Purpose**: Project configuration and settings
- Basic project information
- Team structure and preferences
- BMad methodology configuration
- External tool integrations

## State Management Protocol

### Initialization
```bash
# State files are created when first BMad Orchestrator is invoked
# Initial state: "initialization" phase, awaiting project start
```

### Planning Phase States
1. **business_analysis** → Business Analyst creates project brief
2. **product_management** → Product Manager creates PRD  
3. **ux_strategy** → UX Strategist creates frontend specification
4. **technical_architecture** → Technical Architect creates system design
5. **product_owner_validation** → Product Owner validates and shards documents

### Development Phase States  
1. **document_sharding** → Product Owner shards planning documents
2. **story_creation** → Scrum Master creates stories from epics
3. **story_implementation** → Developer implements story requirements
4. **qa_review** → QA Reviewer validates implementation
5. **epic_completion** → Check if epic is complete, manage transitions

### State Transitions

#### Automatic Transitions
- Triggered by agent completion notifications
- Based on file system changes (docs/ directory monitoring)
- Scheduled by Orchestrator coordination logic

#### User-Confirmed Transitions
- Epic completion decisions (continue vs new epic)
- Phase transition approvals (planning → development)
- Project completion confirmation

## Integration with Sub-Agents

### Agent Completion Protocol
All sub-agents follow this completion sequence:

1. **Complete Primary Task**: Create/update assigned deliverable
2. **Update Workflow State**: Modify workflow-state.json with completion status
3. **Log Handoff**: Record transition in agent-handoffs.log  
4. **Signal Next Action**: Update next_action in workflow state
5. **Notify Orchestrator**: Trigger automatic coordination via state change

### Orchestrator Coordination
The BMad Orchestrator monitors state changes and:

1. **Detects Completions**: Reads state files for agent completion signals
2. **Determines Next Steps**: Uses decision logic to identify next agent
3. **Triggers Automation**: Automatically delegates to appropriate sub-agent
4. **Manages Quality Gates**: Ensures phase completion before transitions
5. **Handles User Interaction**: Prompts for decisions when required

## File Access Patterns

### Read Access
- **All Agents**: Can read workflow-state.json for context
- **Orchestrator**: Full read access to all state files
- **Development Agents**: Can read epic-progress.json for story context

### Write Access  
- **All Agents**: Write completion status to workflow-state.json
- **Orchestrator**: Full write access for coordination
- **Specialized Access**: Epic progress only updated by development agents

## Error Recovery

### State Consistency Checks
- File existence vs state record validation
- Timestamp consistency verification  
- Cross-file state synchronization

### Recovery Mechanisms
- Auto-sync from file system when inconsistencies detected
- Manual state reset options via Orchestrator
- Rollback to last known good state

## Usage Examples

### Check Current Status
```bash
# Orchestrator reads workflow-state.json to determine:
# - Current phase and stage
# - Next recommended action  
# - Required user input
```

### Monitor Progress
```bash
# epic-progress.json provides:
# - Completion percentage
# - Active story status
# - Remaining work estimates
```

### Debug Issues
```bash  
# agent-handoffs.log shows:
# - Last successful handoff
# - Timing of transitions
# - Potential bottlenecks
```

This state management system enables fully automated BMad Method workflow coordination while maintaining transparency and user control over the development process.