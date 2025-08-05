# Epic Management Utilities

這個檔案包含 Epic 和 Story 自動管理的實用函數和邏輯。

## Epic Progress Tracking Functions

### Story Status Detection
```python
def get_story_status_from_file(story_file_path):
    """Extract story status from story markdown file"""
    content = read_file(story_file_path)
    lines = content.split('\n')
    
    for line in lines:
        if line.strip().startswith('## Status'):
            # Next line should contain the status
            status_line = lines[lines.index(line) + 1].strip()
            if status_line in ['Draft', 'Approved', 'InProgress', 'Review', 'Done']:
                return status_line.lower()
    
    return 'pending'  # Default if no status found
```

### Epic Completion Calculation
```python
def calculate_epic_completion(epic_id):
    """Calculate completion percentage for an epic"""
    epic_progress = read_json('.bmad/epic-progress.json')
    
    for epic in epic_progress['epics']:
        if epic['epic_id'] == epic_id:
            total_stories = len(epic['stories'])
            completed_stories = len([s for s in epic['stories'] if s['status'] == 'done'])
            
            if total_stories == 0:
                return 0
            
            return (completed_stories / total_stories) * 100
    
    return 0
```

### Epic Status Management
```python
def update_epic_progress(epic_id, story_id, new_status):
    """Update story status within an epic"""
    epic_progress = read_json('.bmad/epic-progress.json')
    
    for epic in epic_progress['epics']:
        if epic['epic_id'] == epic_id:
            for story in epic['stories']:
                if story['story_id'] == story_id:
                    story['status'] = new_status
                    if new_status == 'done':
                        story['completed_at'] = current_timestamp()
                    elif new_status == 'in_progress':
                        story['started_at'] = current_timestamp()
            
            # Recalculate completion percentage
            epic['completion_percentage'] = calculate_epic_completion(epic_id)
            
            # Check if epic is complete
            if epic['completion_percentage'] == 100:
                epic['status'] = 'completed'
                epic['completed_at'] = current_timestamp()
    
    # Update overall project statistics
    update_project_statistics(epic_progress)
    
    write_json('.bmad/epic-progress.json', epic_progress)
```

### Project Statistics Update
```python
def update_project_statistics(epic_progress):
    """Update overall project completion statistics"""
    total_epics = len(epic_progress['epics'])
    completed_epics = len([e for e in epic_progress['epics'] if e['status'] == 'completed'])
    
    epic_progress['total_epics'] = total_epics
    epic_progress['completed_epics'] = completed_epics
    
    if total_epics > 0:
        epic_progress['project_completion'] = (completed_epics / total_epics) * 100
    else:
        epic_progress['project_completion'] = 0
    
    # Update story statistics
    all_stories = []
    for epic in epic_progress['epics']:
        all_stories.extend(epic['stories'])
    
    epic_progress['story_statistics'] = {
        'total_stories': len(all_stories),
        'completed_stories': len([s for s in all_stories if s['status'] == 'done']),
        'in_progress_stories': len([s for s in all_stories if s['status'] == 'in_progress']),
        'pending_stories': len([s for s in all_stories if s['status'] in ['pending', 'approved', 'draft']])
    }
```

## Epic Transition Decision Logic

### Epic Completion Handler
```python
def handle_epic_completion(epic_id):
    """Handle epic completion and determine next actions"""
    epic_progress = read_json('.bmad/epic-progress.json')
    workflow_state = read_json('.bmad/workflow-state.json')
    
    current_epic = find_epic_by_id(epic_progress, epic_id)
    
    if current_epic and current_epic['completion_percentage'] == 100:
        # Epic is complete
        remaining_epics = [e for e in epic_progress['epics'] if e['status'] != 'completed']
        
        if len(remaining_epics) > 0:
            # More epics exist - ask user about next epic
            return {
                'action': 'user_decision_required',
                'message': 'Epic completed! Start next epic or create new stories?',
                'options': [
                    'start_next_epic',
                    'create_new_epic', 
                    'project_complete'
                ],
                'next_agent': 'orchestrator'
            }
        else:
            # No more epics - project might be complete
            return {
                'action': 'user_decision_required',
                'message': 'All epics completed! Create new epic or mark project complete?',
                'options': [
                    'create_new_epic',
                    'project_complete'
                ],
                'next_agent': 'orchestrator'
            }
    else:
        # Epic not complete - need more stories
        return {
            'action': 'auto_trigger',
            'next_agent': 'scrum-master',
            'message': 'Epic not complete. Creating next story.',
            'priority': 'high'
        }
```

### Story Creation Decision
```python
def determine_next_story_action(current_epic_id):
    """Determine if we need to create next story or handle epic completion"""
    epic_progress = read_json('.bmad/epic-progress.json')
    
    current_epic = find_epic_by_id(epic_progress, current_epic_id)
    
    if not current_epic:
        return {
            'action': 'error',
            'message': 'Current epic not found'
        }
    
    # Check for pending/draft stories in current epic
    pending_stories = [s for s in current_epic['stories'] 
                      if s['status'] in ['pending', 'draft', 'approved']]
    
    if len(pending_stories) > 0:
        # There are pending stories, work on next one
        next_story = pending_stories[0]
        return {
            'action': 'auto_trigger',
            'next_agent': 'developer' if next_story['status'] == 'approved' else 'scrum-master',
            'message': f'Continuing with story: {next_story["story_id"]}',
            'story_id': next_story['story_id']
        }
    else:
        # No pending stories, check epic completion
        return handle_epic_completion(current_epic_id)
```

## File System Integration

### Story File Scanning
```python
def scan_story_files_for_status():
    """Scan docs/stories/ directory and sync with epic progress"""
    story_files = glob('docs/stories/*.md')
    epic_progress = read_json('.bmad/epic-progress.json')
    
    for story_file in story_files:
        # Extract story ID from filename (e.g., "1.1.user-registration.md")
        filename = os.path.basename(story_file)
        story_id = filename.replace('.md', '')
        
        # Get status from file content
        file_status = get_story_status_from_file(story_file)
        
        # Update epic progress if status changed
        epic_id = extract_epic_id_from_story_id(story_id)  # "1.1.xxx" -> "epic-1"
        update_epic_progress(epic_id, story_id, file_status)
```

### Epic Auto-Discovery
```python
def discover_epics_from_prd_shards():
    """Auto-discover epics from sharded PRD files"""
    prd_files = glob('docs/prd/epic-*.md')
    epic_progress = read_json('.bmad/epic-progress.json')
    
    for prd_file in prd_files:
        epic_id = extract_epic_id_from_filename(prd_file)
        
        # Check if epic already tracked
        if not find_epic_by_id(epic_progress, epic_id):
            # Add new epic to tracking
            epic_title = extract_epic_title_from_file(prd_file)
            new_epic = {
                'epic_id': epic_id,
                'title': epic_title,
                'status': 'pending',
                'stories': [],
                'completion_percentage': 0,
                'created_at': current_timestamp()
            }
            epic_progress['epics'].append(new_epic)
    
    write_json('.bmad/epic-progress.json', epic_progress)
```

## Integration with Orchestrator

### Orchestrator Epic Management Commands
```python
def orchestrator_epic_management():
    """Main epic management logic for orchestrator"""
    
    # 1. Sync file system with epic progress
    scan_story_files_for_status()
    discover_epics_from_prd_shards()
    
    # 2. Get current workflow state
    workflow_state = read_json('.bmad/workflow-state.json')
    current_epic = workflow_state['phase_status']['development']['current_epic']
    
    # 3. Determine next action
    if current_epic:
        next_action = determine_next_story_action(current_epic)
    else:
        # No current epic, start first epic
        epic_progress = read_json('.bmad/epic-progress.json')
        if len(epic_progress['epics']) > 0:
            first_epic = epic_progress['epics'][0]
            next_action = {
                'action': 'auto_trigger',
                'next_agent': 'scrum-master',
                'message': f'Starting epic: {first_epic["title"]}',
                'epic_id': first_epic['epic_id']
            }
        else:
            next_action = {
                'action': 'user_decision_required',
                'message': 'No epics found. Create epics from PRD or start new epic?'
            }
    
    return next_action
```

## Usage Examples

### QA Reviewer Integration
When QA Reviewer completes review, it should:
1. Update story status in epic progress
2. Check epic completion
3. Trigger next action based on epic status

### Scrum Master Integration  
When Scrum Master creates new story:
1. Add story to current epic in epic progress
2. Set story status to 'approved'
3. Update epic statistics

### Orchestrator Integration
When user asks "what's next?":
1. Run epic management logic
2. Determine appropriate next action
3. Either auto-trigger agent or ask for user decision