# BMad Error Recovery System

這個檔案定義了 BMad 自動化工作流程的錯誤恢復機制和一致性檢查。

## 狀態一致性檢查

### File System vs State Record Validation
```python
def validate_state_consistency():
    """Check if file system matches state records"""
    workflow_state = read_json('.bmad/workflow-state.json')
    issues = []
    
    # Check planning artifacts
    planning_docs = workflow_state['artifacts']['planning_docs']
    
    if planning_docs['project_brief'] and not file_exists('docs/project-brief.md'):
        issues.append({
            'type': 'missing_file',
            'file': 'docs/project-brief.md',
            'state_says': 'exists',
            'reality': 'missing'
        })
    
    if not planning_docs['project_brief'] and file_exists('docs/project-brief.md'):
        issues.append({
            'type': 'unexpected_file',
            'file': 'docs/project-brief.md',
            'state_says': 'missing',
            'reality': 'exists'
        })
    
    # Similar checks for prd.md, front-end-spec.md, fullstack-architecture.md
    
    # Check development structure
    dev_structure = workflow_state['artifacts']['development_structure']
    
    if dev_structure['prd_sharded'] and not directory_exists('docs/prd/'):
        issues.append({
            'type': 'missing_directory',
            'path': 'docs/prd/',
            'state_says': 'sharded',
            'reality': 'not_sharded'
        })
    
    return issues
```

### Timestamp Consistency Verification
```python
def check_timestamp_consistency():
    """Verify timestamps are logical and recent"""
    workflow_state = read_json('.bmad/workflow-state.json')
    handoffs = read_json('.bmad/agent-handoffs.log')
    epic_progress = read_json('.bmad/epic-progress.json')
    
    issues = []
    current_time = current_timestamp()
    
    # Check for timestamps in the future
    if workflow_state['last_updated'] > current_time:
        issues.append({
            'type': 'future_timestamp',
            'component': 'workflow_state',
            'timestamp': workflow_state['last_updated']
        })
    
    # Check handoff sequence consistency
    if len(handoffs['handoffs']) > 1:
        for i in range(1, len(handoffs['handoffs'])):
            prev_handoff = handoffs['handoffs'][i-1]
            curr_handoff = handoffs['handoffs'][i]
            
            if curr_handoff['timestamp'] < prev_handoff['timestamp']:
                issues.append({
                    'type': 'timestamp_sequence_error',
                    'component': 'handoffs',
                    'issue': f'Handoff {i} earlier than handoff {i-1}'
                })
    
    return issues
```

### Cross-File State Synchronization
```python
def synchronize_cross_file_state():
    """Ensure all state files are consistent with each other"""
    workflow_state = read_json('.bmad/workflow-state.json')
    handoffs = read_json('.bmad/agent-handoffs.log')
    epic_progress = read_json('.bmad/epic-progress.json')
    
    sync_actions = []
    
    # Sync current epic between workflow_state and epic_progress
    workflow_epic = workflow_state['phase_status']['development']['current_epic']
    
    if workflow_epic:
        # Ensure epic exists in epic_progress
        epic_found = False
        for epic in epic_progress['epics']:
            if epic['epic_id'] == workflow_epic:
                epic_found = True
                break
        
        if not epic_found:
            sync_actions.append({
                'action': 'add_missing_epic',
                'epic_id': workflow_epic,
                'target_file': 'epic-progress.json'
            })
    
    # Sync last handoff with workflow state
    if len(handoffs['handoffs']) > 0:
        last_handoff = handoffs['handoffs'][-1]
        if last_handoff['to_agent'] != workflow_state.get('active_agent'):
            sync_actions.append({
                'action': 'sync_active_agent',
                'expected': last_handoff['to_agent'],
                'current': workflow_state.get('active_agent')
            })
    
    return sync_actions
```

## 自動修復機制

### File System Auto-Sync
```python
def auto_sync_from_filesystem():
    \"\"\"Automatically sync state from actual file system\"\"\"
    workflow_state = read_json('.bmad/workflow-state.json')
    
    # Scan docs/ directory for actual files
    docs_files = scan_directory('docs/')
    
    # Update planning docs status based on file existence
    planning_docs = workflow_state['artifacts']['planning_docs']
    planning_docs['project_brief'] = 'project-brief.md' in docs_files
    planning_docs['prd'] = 'prd.md' in docs_files
    planning_docs['frontend_spec'] = 'front-end-spec.md' in docs_files
    planning_docs['architecture'] = 'fullstack-architecture.md' in docs_files
    
    # Update development structure based on directory existence
    dev_structure = workflow_state['artifacts']['development_structure']
    dev_structure['prd_sharded'] = directory_exists('docs/prd/')
    dev_structure['architecture_sharded'] = directory_exists('docs/architecture/')
    dev_structure['stories_created'] = directory_exists('docs/stories/') and len(glob('docs/stories/*.md')) > 0
    
    # Update phase based on file analysis
    if all(planning_docs.values()) and all(dev_structure.values()):
        workflow_state['current_phase'] = 'development'
    elif any(planning_docs.values()):
        workflow_state['current_phase'] = 'planning'
    else:
        workflow_state['current_phase'] = 'initialization'
    
    # Update timestamp
    workflow_state['last_updated'] = current_timestamp()
    
    write_json('.bmad/workflow-state.json', workflow_state)
    
    return workflow_state
```

### State Rollback to Last Known Good
```python
def rollback_to_last_good_state():
    \"\"\"Rollback to last known good state\"\"\"
    # Create backup of current state
    timestamp = current_timestamp().replace(':', '-').replace('.', '-')
    backup_current_state(f'.bmad/backups/state-backup-{timestamp}/')
    
    # Find last good state (look for most recent backup with consistent timestamps)
    backup_dirs = glob('.bmad/backups/state-backup-*/')
    backup_dirs.sort(reverse=True)  # Most recent first
    
    for backup_dir in backup_dirs:
        try:
            # Test if backup state is consistent
            test_workflow_state = read_json(f'{backup_dir}/workflow-state.json')
            test_handoffs = read_json(f'{backup_dir}/agent-handoffs.log')
            test_epic_progress = read_json(f'{backup_dir}/epic-progress.json')
            
            # Basic consistency checks
            if validate_backup_consistency(test_workflow_state, test_handoffs, test_epic_progress):
                # Restore from this backup
                restore_from_backup(backup_dir)
                return {
                    'success': True,
                    'restored_from': backup_dir,
                    'message': 'State restored from last known good backup'
                }
        except Exception as e:
            continue  # Try next backup
    
    return {
        'success': False,
        'message': 'No valid backup found for rollback'
    }
```

### Manual Intervention Options
```python
def provide_manual_recovery_options(issues):
    \"\"\"Provide manual recovery options for detected issues\"\"\"
    recovery_options = []
    
    for issue in issues:
        if issue['type'] == 'missing_file':
            recovery_options.append({
                'option': 'reset_planning_phase',
                'description': f\"Reset planning phase to recreate {issue['file']}\",
                'command': f\"reset_phase('planning', '{issue['file']}')\",
                'risk': 'low'
            })
            
        elif issue['type'] == 'unexpected_file':
            recovery_options.append({
                'option': 'update_state_to_match_files',
                'description': f\"Update state to acknowledge {issue['file']} exists\",
                'command': f\"sync_state_with_filesystem()\",
                'risk': 'low'
            })
            
        elif issue['type'] == 'timestamp_sequence_error':
            recovery_options.append({
                'option': 'fix_timestamp_sequence',
                'description': 'Correct handoff timestamp sequence',
                'command': 'fix_handoff_timestamps()',
                'risk': 'medium'
            })
            
        elif issue['type'] == 'missing_directory':
            recovery_options.append({
                'option': 'recreate_sharded_structure',
                'description': f\"Recreate {issue['path']} from source documents\",
                'command': f\"reshard_documents('{issue['path']}')\",
                'risk': 'medium'
            })
    
    return recovery_options
```

## 完整系統健康檢查

### Comprehensive Health Check
```python
def run_complete_health_check():
    \"\"\"Run comprehensive system health check\"\"\"
    health_report = {
        'timestamp': current_timestamp(),
        'overall_status': 'healthy',
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    try:
        # 1. State consistency checks
        consistency_issues = validate_state_consistency()
        health_report['issues'].extend(consistency_issues)
        
        # 2. Timestamp validation
        timestamp_issues = check_timestamp_consistency()
        health_report['issues'].extend(timestamp_issues)
        
        # 3. Cross-file synchronization
        sync_actions = synchronize_cross_file_state()
        if len(sync_actions) > 0:
            health_report['warnings'].extend([
                {'type': 'sync_needed', 'actions': sync_actions}
            ])
        
        # 4. File system accessibility
        file_access_issues = check_file_access()
        health_report['issues'].extend(file_access_issues)
        
        # 5. Workflow progression logic
        progression_issues = validate_workflow_progression()
        health_report['issues'].extend(progression_issues)
        
        # Determine overall status
        if len(health_report['issues']) > 0:
            health_report['overall_status'] = 'unhealthy'
        elif len(health_report['warnings']) > 0:
            health_report['overall_status'] = 'warning'
        
        # Generate recommendations
        if len(health_report['issues']) > 0:
            health_report['recommendations'] = provide_manual_recovery_options(health_report['issues'])
        
    except Exception as e:
        health_report['overall_status'] = 'error'
        health_report['issues'].append({
            'type': 'health_check_error',
            'message': str(e)
        })
    
    return health_report
```

### Workflow Progression Validation
```python
def validate_workflow_progression():
    \"\"\"Validate that workflow progression is logical\"\"\"
    workflow_state = read_json('.bmad/workflow-state.json')
    issues = []
    
    current_phase = workflow_state['current_phase']
    current_stage = workflow_state['current_stage']
    phase_status = workflow_state['phase_status']
    
    # Check planning phase progression
    if current_phase == 'planning':
        planning_status = phase_status['planning']
        
        # Business analysis should come first
        if planning_status['product_management'] == 'completed' and planning_status['business_analysis'] != 'completed':
            issues.append({
                'type': 'invalid_progression',
                'message': 'Product management completed before business analysis'
            })
        
        # UX should come after PRD
        if planning_status['ux_strategy'] == 'completed' and planning_status['product_management'] != 'completed':
            issues.append({
                'type': 'invalid_progression',
                'message': 'UX strategy completed before product management'
            })
    
    # Check development phase progression
    elif current_phase == 'development':
        dev_status = phase_status['development']
        
        # Should not be in development without completed planning
        planning_complete = all(status == 'completed' for status in phase_status['planning'].values())
        if not planning_complete:
            issues.append({
                'type': 'invalid_progression',
                'message': 'Development phase started before planning completion'
            })
    
    return issues
```

## 初始化和恢復函數

### Initialize Clean State
```python
def initialize_clean_state():
    \"\"\"Initialize BMad state management from scratch\"\"\"
    # Create clean state files
    clean_workflow_state = {
        \"project_id\": \"\",
        \"project_name\": \"\",
        \"current_phase\": \"initialization\",
        \"current_stage\": \"awaiting_project_start\",
        \"active_agent\": None,
        \"last_updated\": current_timestamp(),
        \"phase_status\": {
            \"planning\": {
                \"business_analysis\": \"pending\",
                \"product_management\": \"pending\", 
                \"ux_strategy\": \"pending\",
                \"technical_architecture\": \"pending\",
                \"product_owner_validation\": \"pending\"
            },
            \"development\": {
                \"document_sharding\": \"pending\",
                \"current_epic\": None,
                \"current_story\": None,
                \"story_status\": \"pending\"
            }
        },
        \"next_action\": {
            \"agent\": None,
            \"description\": \"Awaiting project initialization\",
            \"priority\": \"high\",
            \"user_confirmation_required\": False
        },
        \"artifacts\": {
            \"planning_docs\": {
                \"project_brief\": False,
                \"prd\": False,
                \"frontend_spec\": False,
                \"architecture\": False
            },
            \"development_structure\": {
                \"prd_sharded\": False,
                \"architecture_sharded\": False,
                \"stories_created\": False
            }
        }
    }
    
    write_json('.bmad/workflow-state.json', clean_workflow_state)
    
    # Create clean handoffs log
    clean_handoffs = {
        \"handoffs\": [],
        \"last_updated\": current_timestamp(),
        \"total_handoffs\": 0,
        \"active_handoff\": None
    }
    
    write_json('.bmad/agent-handoffs.log', clean_handoffs)
    
    # Create clean epic progress
    clean_epic_progress = {
        \"epics\": [],
        \"completed_epics\": 0,
        \"total_epics\": 0,
        \"project_completion\": 0,
        \"current_epic\": None,
        \"last_updated\": current_timestamp(),
        \"story_statistics\": {
            \"total_stories\": 0,
            \"completed_stories\": 0,
            \"in_progress_stories\": 0,
            \"pending_stories\": 0
        }
    }
    
    write_json('.bmad/epic-progress.json', clean_epic_progress)
    
    return {
        'success': True,
        'message': 'BMad state management initialized with clean state'
    }
```

## Orchestrator 集成

### Error Recovery Integration in Orchestrator
```python
def orchestrator_error_recovery_check():
    \"\"\"Integrate error recovery into orchestrator workflow\"\"\"
    
    # Run health check
    health_report = run_complete_health_check()
    
    if health_report['overall_status'] == 'unhealthy':
        # Critical issues detected
        return {
            'action': 'error_recovery_required',
            'health_report': health_report,
            'recommendation': 'Run error recovery before proceeding'
        }
    
    elif health_report['overall_status'] == 'warning':
        # Minor issues - auto-fix if possible
        sync_actions = health_report.get('warnings', [])
        for warning in sync_actions:
            if warning['type'] == 'sync_needed':
                # Auto-apply sync actions
                apply_sync_actions(warning['actions'])
        
        return {
            'action': 'continue_with_fixes',
            'message': 'Minor issues auto-fixed, continuing workflow'
        }
    
    else:
        # System healthy
        return {
            'action': 'continue_normal',
            'message': 'System healthy, proceeding with normal workflow'
        }
```

這個錯誤恢復系統提供了：
1. **自動一致性檢查** - 定期驗證狀態檔案與檔案系統的一致性
2. **智能修復** - 自動修復常見的不一致問題
3. **安全回滾** - 在嚴重錯誤時回滾到已知良好狀態
4. **手動介入選項** - 為複雜問題提供清晰的修復選項
5. **完整健康檢查** - 全面的系統狀態評估

這確保了 BMad 自動化工作流程的穩定性和可靠性。