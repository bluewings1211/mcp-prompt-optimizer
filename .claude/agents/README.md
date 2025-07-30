# BMad Method Sub-Agents

This directory contains Claude Code sub-agents that implement the complete BMad Method workflow through specialized, autonomous agents using the official Claude Code sub-agent format.

## Official Sub-Agent Format

All sub-agents follow Claude Code's official format with YAML frontmatter:

```markdown
---
name: agent-name
description: Description of when this sub agent should be invoked
tools: tool1, tool2, tool3  # Optional - inherits all tools if omitted
---

[Agent system prompt and instructions]
```

## Overview

The BMad Method's **Two-Phase Innovation** approach has been transformed into a series of Claude Code sub-agents that provide seamless integration with IDE environments while maintaining the methodology's core principles.

### Phase 1: Planning (Web UI/IDE)
- **business-analyst.md** → Market research, competitive analysis, project briefs
- **product-manager.md** → PRD creation, user stories, product strategy
- **ux-strategist.md** → Frontend specification, user experience design
- **technical-architect.md** → System architecture, technical specifications
- **product-owner.md** → Document validation, sharding, development preparation

### Phase 2: Development (IDE)
- **scrum-master.md** → Story creation, epic breakdown, development planning
- **developer.md** → Code implementation, feature development
- **qa-reviewer.md** → Code review, quality assurance, testing validation

### Orchestration
- **orchestrator.md** → Workflow coordination, agent management, process guidance

## Agent Tool Permissions

### Planning Phase Agents

#### Business Analyst
```yaml
tools: [Read, Write, WebSearch, WebFetch]
access:
  docs/: read-write (planning artifacts)
  project/: read-only (context gathering)
purpose: External research and business analysis
```

#### Product Manager  
```yaml
tools: [Read, Write]
access:
  docs/: read-write (PRD and product docs)
  project/: read-only (context understanding)
purpose: Internal planning and requirements management
```

#### UX Strategist
```yaml
tools: [Read, Write, WebSearch]
access:
  docs/: read-write (UX specifications)
  project/: read-only (technical context)
purpose: User experience design and frontend planning
```

#### Technical Architect
```yaml
tools: [Read, Write, Glob, Grep]
access:
  docs/: read-write (architecture docs)
  project/: full-read (system analysis)
purpose: Technical design and architecture planning
```

#### Product Owner
```yaml
tools: [Read, Write, Glob]
access:
  docs/: full-access (document management)
  project/: read-only (validation context)
purpose: Quality gates and document management
```

### Development Phase Agents

#### Scrum Master
```yaml
tools: [Read, Write, Glob]
access:
  docs/prd/: read-only (epic sources)
  docs/architecture/: read-only (technical context)
  docs/stories/: read-write (story management)
purpose: Story creation and development planning
```

#### Developer
```yaml
tools: [All development tools]
access:
  docs/stories/: read-write (story updates)
  docs/architecture/: read-only (devLoadAlwaysFiles)
  project/: full-access (implementation)
  docs/planning/: read-only (reference only)
purpose: Code implementation and development
```

#### QA Reviewer
```yaml
tools: [Read, Bash, Grep, Glob, limited Write]
access:
  docs/stories/: read-write (review documentation)
  project/: read-write (code and tests)
  tests/: full-write (test improvements)
purpose: Quality assurance and code review
```

### Orchestration Agent

#### BMad Orchestrator
```yaml
tools: [Read, Glob]
access:
  all-files: read-only (state assessment)
  no-write: coordination only
purpose: Workflow guidance and agent coordination
```

## Automatic Delegation Triggers

Claude Code will automatically delegate to appropriate agents based on these keywords:

### Planning Triggers
- **"market research"**, **"competitive analysis"** → Business Analyst
- **"PRD"**, **"requirements"**, **"user stories"** → Product Manager
- **"UI/UX"**, **"user experience"**, **"frontend spec"** → UX Strategist
- **"architecture"**, **"technical design"**, **"system design"** → Technical Architect
- **"document validation"**, **"shard documents"** → Product Owner

### Development Triggers
- **"create story"**, **"story planning"**, **"epic breakdown"** → Scrum Master
- **"implement"**, **"code"**, **"develop"**, **"build feature"** → Developer
- **"review code"**, **"QA"**, **"test"**, **"quality check"** → QA Reviewer

### Orchestration Triggers
- **"start project"**, **"bmad workflow"**, **"help"**, **"guidance"** → BMad Orchestrator

## Integration with Existing BMad Workflow

### File Structure Compatibility
The sub-agents maintain full compatibility with existing BMad file structures:

```
docs/
├── project-brief.md        # Business Analyst output
├── prd.md                  # Product Manager output  
├── front-end-spec.md       # UX Strategist output
├── fullstack-architecture.md # Technical Architect output
├── prd/                    # Sharded epics (Product Owner)
│   ├── epic-1-auth.md
│   └── epic-2-dashboard.md
├── architecture/           # Sharded architecture (Product Owner)
│   ├── coding-standards.md # Developer devLoadAlwaysFiles
│   ├── tech-stack.md       # Developer devLoadAlwaysFiles
│   └── source-tree.md      # Developer devLoadAlwaysFiles
└── stories/                # Story files (Scrum Master)
    ├── 1.1.user-registration.md
    └── 1.2.user-login.md
```

### Core Config Integration
Sub-agents respect existing `bmad-core/core-config.yaml` settings:

```yaml
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md  
  - docs/architecture/source-tree.md
devStoryLocation: docs/stories
```

## Usage Examples

### Starting a New Project
```
User: "I want to build a new web application"
→ BMad Orchestrator provides workflow guidance
→ Automatically delegates to Business Analyst for project brief
```

### During Development
```
User: "Implement user authentication feature"
→ Automatically delegates to Developer
→ Developer reads story file and devLoadAlwaysFiles
→ Implements feature following BMad methodology
```

### Quality Assurance
```
User: "Review the authentication implementation"
→ Automatically delegates to QA Reviewer
→ QA performs comprehensive code review
→ Updates story with review findings
```

## Migration from Traditional BMad

### For Existing BMad Users
1. **No workflow changes required** - sub-agents follow identical BMad methodology
2. **File structure preserved** - all existing documentation locations maintained  
3. **Enhanced integration** - seamless IDE integration with full tool access
4. **Automatic delegation** - no more manual agent switching with `@agent` commands

### For New BMad Adopters
1. **Start with BMad Orchestrator** - provides complete workflow guidance
2. **Follow natural conversation flow** - agents activate automatically based on context
3. **Maintain quality gates** - sub-agents enforce BMad quality standards
4. **Scale to team usage** - methodology supports both solo and team development

## Success Metrics

### Planning Phase
- [ ] Complete planning artifacts created (project-brief, PRD, frontend-spec, architecture)
- [ ] Documents validated and sharded for development
- [ ] Clear handoff to development phase

### Development Phase  
- [ ] Stories created with complete context from sharded docs
- [ ] Code implemented following architectural guidelines
- [ ] Quality assurance completed with comprehensive review

### Overall Workflow
- [ ] Smooth transitions between phases and agents
- [ ] Minimal context loss between agent handoffs
- [ ] High-quality deliverables meeting BMad standards
- [ ] Efficient development velocity with autonomous team operation

## Support and Troubleshooting

If you need guidance on BMad Method workflow or sub-agent usage, start with the **BMad Orchestrator** agent. It provides comprehensive workflow guidance and can direct you to appropriate specialized agents based on your current needs.

For questions about specific agents or workflow phases, refer to the individual agent documentation files in this directory.