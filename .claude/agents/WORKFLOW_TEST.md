# BMad Sub-Agent Workflow Test

This document provides test scenarios to validate the complete BMad Method sub-agent integration.

## Test Scenario: New Web Application Project

### Objective
Validate the complete workflow from initial project idea through implementation using Claude Code sub-agents.

### Prerequisites
- BMad sub-agents configured in `.claude/agents/`
- Clean project directory for testing
- Claude Code with sub-agent functionality enabled

## Test Phase 1: Planning Phase

### Test 1.1: Initial Project Coordination
**Trigger**: "I want to build a new task management web application"

**Expected Behavior**:
1. BMad Orchestrator should activate automatically
2. Provide workflow guidance and next steps
3. Recommend starting with Business Analyst for project brief

**Validation**:
- [ ] BMad Orchestrator activates and provides guidance
- [ ] Clear next steps provided for planning phase
- [ ] Business Analyst recommended for market research

### Test 1.2: Business Analysis
**Trigger**: "I need market research for my task management app"

**Expected Behavior**:
1. Business Analyst should activate automatically
2. Conduct web-based market research
3. Create `docs/project-brief.md` with comprehensive analysis

**Validation**:
- [ ] Business Analyst activates for market research
- [ ] Web search capabilities used for competitive analysis
- [ ] `docs/project-brief.md` created with market insights
- [ ] Document follows BMad project brief template

### Test 1.3: Product Requirements
**Trigger**: "Create PRD from the project brief"

**Expected Behavior**:
1. Product Manager should activate automatically
2. Read existing `docs/project-brief.md`
3. Create comprehensive `docs/prd.md` with user stories

**Validation**:
- [ ] Product Manager activates for PRD creation
- [ ] Reads and incorporates project brief content
- [ ] `docs/prd.md` created with detailed user stories
- [ ] Acceptance criteria clearly defined for each story

### Test 1.4: UX Specification
**Trigger**: "Design the user experience for this task management app"

**Expected Behavior**:
1. UX Strategist should activate automatically
2. Read existing `docs/prd.md` for requirements
3. Create `docs/front-end-spec.md` with UI/UX specifications

**Validation**:
- [ ] UX Strategist activates for frontend design
- [ ] Incorporates PRD requirements into UX design
- [ ] `docs/front-end-spec.md` created with comprehensive UI specs
- [ ] Responsive design and accessibility considered

### Test 1.5: Technical Architecture
**Trigger**: "Create system architecture for the task management application"

**Expected Behavior**:
1. Technical Architect should activate automatically
2. Read PRD and frontend specifications
3. Create `docs/fullstack-architecture.md` with technical design

**Validation**:
- [ ] Technical Architect activates for system design
- [ ] Analyzes existing requirements and UX specifications
- [ ] `docs/fullstack-architecture.md` created with detailed architecture
- [ ] Technology stack, database design, and API architecture defined

### Test 1.6: Planning Validation
**Trigger**: "Validate all planning documents and prepare for development"

**Expected Behavior**:
1. Product Owner should activate automatically
2. Review all planning artifacts for consistency
3. Shard documents into development-ready structure

**Validation**:
- [ ] Product Owner activates for document validation
- [ ] All planning documents reviewed for consistency
- [ ] Documents sharded into `docs/prd/` and `docs/architecture/`
- [ ] Development readiness confirmed

## Test Phase 2: Development Phase

### Test 2.1: Story Creation
**Trigger**: "Create the first user story from the sharded epics"

**Expected Behavior**:
1. Scrum Master should activate automatically
2. Read sharded epic documents from `docs/prd/`
3. Create detailed story in `docs/stories/`

**Validation**:
- [ ] Scrum Master activates for story creation
- [ ] Reads sharded epic documents appropriately
- [ ] Story created with complete context and dev notes
- [ ] Tasks and acceptance criteria clearly defined
- [ ] **Story starts with "Draft" status**
- [ ] **Story updated to "Approved" status after validation**

### Test 2.2: Story Implementation
**Trigger**: "Implement the user registration story"

**Expected Behavior**:
1. Developer should activate automatically
2. Read story file and devLoadAlwaysFiles
3. Implement functionality according to story requirements

**Validation**:
- [ ] Developer activates for implementation
- [ ] Reads story file and architectural guidelines
- [ ] **Updates story status "Approved" → "InProgress" when starting**
- [ ] Code implemented following established patterns
- [ ] Story progress updated throughout implementation
- [ ] **Updates story status "InProgress" → "Review" when complete**

### Test 2.3: Quality Assurance
**Trigger**: "Review the user registration implementation"

**Expected Behavior**:
1. QA Reviewer should activate automatically
2. Review implemented code for quality and standards
3. Validate acceptance criteria satisfaction

**Validation**:
- [ ] QA Reviewer activates for code review
- [ ] Comprehensive code quality assessment performed
- [ ] Acceptance criteria validated
- [ ] **Story status decision made based on quality assessment**
- [ ] **"Review" → "Done" if quality standards met**
- [ ] **"Review" → "InProgress" if issues found requiring developer attention**

## Test Phase 3: Workflow Integration

### Test 3.1: Agent Handoffs
**Validation Points**:
- [ ] Smooth transitions between planning phase agents
- [ ] Information preserved across agent handoffs
- [ ] Each agent has appropriate context from previous work
- [ ] No duplication of effort or missed requirements

### Test 3.2: File Access Permissions
**Validation Points**:
- [ ] Planning agents can write to docs/ appropriately
- [ ] Development agents have proper project access
- [ ] No unauthorized file modifications
- [ ] Tool permissions respected by each agent

### Test 3.3: Automatic Delegation
**Validation Points**:
- [ ] Appropriate agents activate based on user requests
- [ ] No manual agent switching required
- [ ] Context-aware delegation decisions
- [ ] Fallback to BMad Orchestrator when unclear

### Test 3.4: Quality Standards
**Validation Points**:
- [ ] All documents follow BMad template standards
- [ ] Code follows established coding standards
- [ ] Acceptance criteria properly validated
- [ ] Quality gates enforced at phase transitions

## Test Completion Criteria

### Planning Phase Success
- [ ] Complete planning artifacts created
- [ ] Documents validated and consistent
- [ ] Proper sharding for development phase
- [ ] Clear development roadmap established

### Development Phase Success
- [ ] Stories created with complete context
- [ ] Code implemented according to specifications
- [ ] Quality assurance completed successfully
- [ ] Implementation meets acceptance criteria

### Overall Workflow Success
- [ ] Seamless agent transitions
- [ ] Minimal context loss between phases
- [ ] High-quality deliverables throughout
- [ ] Efficient development velocity

## Known Issues and Limitations

### Current Limitations
- Sub-agent tool permissions may need refinement based on testing
- Automatic delegation triggers may require tuning
- Complex project scenarios may need additional coordination

### Future Improvements
- Enhanced agent communication protocols
- More sophisticated delegation algorithms
- Integration with external development tools
- Support for advanced BMad workflows

## Test Results Log

### Test Execution Date: ___________
### Tester: ___________
### Environment: ___________

#### Planning Phase Results
- [ ] Business Analyst: Pass/Fail - Notes: ___________
- [ ] Product Manager: Pass/Fail - Notes: ___________
- [ ] UX Strategist: Pass/Fail - Notes: ___________
- [ ] Technical Architect: Pass/Fail - Notes: ___________
- [ ] Product Owner: Pass/Fail - Notes: ___________

#### Development Phase Results
- [ ] Scrum Master: Pass/Fail - Notes: ___________
- [ ] Developer: Pass/Fail - Notes: ___________
- [ ] QA Reviewer: Pass/Fail - Notes: ___________

#### Integration Results
- [ ] Agent Handoffs: Pass/Fail - Notes: ___________
- [ ] File Permissions: Pass/Fail - Notes: ___________
- [ ] Automatic Delegation: Pass/Fail - Notes: ___________
- [ ] Quality Standards: Pass/Fail - Notes: ___________

#### Overall Assessment
- [ ] Workflow Complete: Pass/Fail
- [ ] Quality Satisfactory: Pass/Fail
- [ ] Performance Acceptable: Pass/Fail
- [ ] Ready for Production Use: Pass/Fail

### Additional Notes:
___________________________________________________________
___________________________________________________________
___________________________________________________________