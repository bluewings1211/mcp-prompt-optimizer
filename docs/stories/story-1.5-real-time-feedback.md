# Story 1.5: Real-time Optimization Feedback

## Status
[Approved]

## User Story
**As a** content creator  
**I want** to see progress updates while optimization runs  
**So that** I understand what's happening and can adjust if needed  

## Business Value
- **Primary Value**: Improves user experience through transparency and control
- **User Impact**: Reduces perceived wait time and builds trust in optimization process
- **Success Metric**: User engagement maintained during optimization with <5% cancellation rate

## Acceptance Criteria

### AC1: Real-time Progress Updates
- **GIVEN** I start an optimization process  
- **WHEN** the system is compiling and optimizing  
- **THEN** I receive progress updates every 5 seconds with clear status information  
- **AND** progress updates include percentage completion and current phase  
- **AND** updates are delivered through MCP protocol in real-time  

### AC2: Transparent Process Explanation
- **GIVEN** optimization is running  
- **WHEN** progress updates are sent  
- **THEN** I can see which strategy is being applied and why  
- **AND** understand the reasoning behind current optimization decisions  
- **AND** receive estimates for remaining processing time  

### AC3: User Control and Cancellation
- **GIVEN** optimization is in progress  
- **WHEN** I want to modify or cancel the process  
- **THEN** I can interrupt the optimization safely  
- **AND** receive partial results if any optimization steps completed  
- **AND** system provides options to retry with different parameters  

## Detailed Tasks

### Task 1.5.1: Implement Progress Tracking Infrastructure
**Acceptance Criteria Reference**: AC1  
**Estimated Hours**: 12  

```python
class OptimizationProgressTracker:
    def __init__(self):
        self.progress_callbacks = []
        self.progress_store = ProgressStore()
        self.phase_estimator = PhaseTimeEstimator()
        self.mcp_notifier = MCPProgressNotifier()
    
    async def track_optimization(self, session_id: str, 
                                request: OptimizationRequest) -> OptimizationResult:
        """Track optimization with comprehensive progress updates"""
        
        # Initialize progress tracking
        progress_context = ProgressContext(
            session_id=session_id,
            total_phases=6,
            start_time=datetime.now(),
            estimated_total_time=await self.phase_estimator.estimate_total_time(request)
        )
        
        try:
            # Phase 1: Strategy Detection (10% of total process)
            await self._update_progress(progress_context, 1, "Analyzing prompt and detecting optimal strategy...")
            
            strategy_result = await self._track_phase(
                progress_context,
                phase_number=1,
                phase_name="Strategy Detection",
                phase_function=self.signature_detector.detect_optimal_strategy,
                phase_args=(request.prompt, request.context),
                expected_duration=2.0
            )
            
            # Phase 2: Example Mining (20% of total process)
            await self._update_progress(progress_context, 2, f"Mining high-quality examples for {strategy_result.task_type}...")
            
            examples = await self._track_phase(
                progress_context,
                phase_number=2,
                phase_name="Example Mining",
                phase_function=self.example_miner.get_optimal_examples,
                phase_args=(strategy_result.task_type,),
                expected_duration=4.0
            )
            
            # Phase 3: Module Compilation (40% of total process)
            await self._update_progress(progress_context, 3, f"Compiling DSPy module with {strategy_result.optimizer} optimizer...")
            
            compiled_module = await self._track_phase(
                progress_context,
                phase_number=3,
                phase_name="Module Compilation",
                phase_function=self.module_compiler.compile_optimized_module,
                phase_args=(strategy_result.signature, examples),
                expected_duration=18.0,
                allow_cancellation=True
            )
            
            # Phase 4: Optimization Execution (20% of total process)
            await self._update_progress(progress_context, 4, "Executing prompt optimization...")
            
            optimization_result = await self._track_phase(
                progress_context,
                phase_number=4,
                phase_name="Optimization Execution",
                phase_function=compiled_module.optimize_prompt,
                phase_args=(request.prompt,),
                expected_duration=4.0
            )
            
            # Phase 5: Results Analysis (5% of total process)
            await self._update_progress(progress_context, 5, "Analyzing optimization results...")
            
            analysis_result = await self._track_phase(
                progress_context,
                phase_number=5,
                phase_name="Results Analysis",
                phase_function=self._analyze_optimization_results,
                phase_args=(request.prompt, optimization_result),
                expected_duration=1.0
            )
            
            # Phase 6: Finalization (5% of total process)
            await self._update_progress(progress_context, 6, "Finalizing optimization and preparing results...")
            
            final_result = await self._finalize_optimization(
                progress_context, request, strategy_result, optimization_result, analysis_result
            )
            
            await self._update_progress(progress_context, 6, "Optimization complete!", completion_percentage=100)
            
            return final_result
            
        except OptimizationCancelledException as e:
            return await self._handle_cancellation(progress_context, e)
        except Exception as e:
            return await self._handle_optimization_error(progress_context, e)
    
    async def _track_phase(self, progress_context: ProgressContext,
                          phase_number: int, phase_name: str,
                          phase_function: Callable, phase_args: tuple,
                          expected_duration: float,
                          allow_cancellation: bool = False) -> Any:
        """Track a single optimization phase with progress updates"""
        
        phase_start = time.time()
        
        # Create phase-specific progress tracker
        phase_tracker = PhaseProgressTracker(
            progress_context, phase_number, phase_name, expected_duration
        )
        
        # Start periodic progress updates
        progress_task = asyncio.create_task(
            self._periodic_phase_updates(phase_tracker, allow_cancellation)
        )
        
        try:
            # Execute the phase function
            if asyncio.iscoroutinefunction(phase_function):
                result = await phase_function(*phase_args)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, phase_function, *phase_args)
            
            # Cancel periodic updates
            progress_task.cancel()
            
            # Record actual phase duration
            actual_duration = time.time() - phase_start
            await self.phase_estimator.update_phase_duration(
                phase_name, actual_duration
            )
            
            return result
            
        except asyncio.CancelledError:
            progress_task.cancel()
            raise OptimizationCancelledException(f"Phase {phase_name} was cancelled")
        except Exception as e:
            progress_task.cancel()
            raise OptimizationPhaseError(f"Phase {phase_name} failed: {str(e)}")
    
    async def _periodic_phase_updates(self, phase_tracker: PhaseProgressTracker,
                                     allow_cancellation: bool):
        """Send periodic progress updates during phase execution"""
        
        update_interval = 2.0  # Update every 2 seconds
        
        while True:
            try:
                await asyncio.sleep(update_interval)
                
                # Check for cancellation requests
                if allow_cancellation:
                    cancellation_requested = await self.progress_store.check_cancellation_request(
                        phase_tracker.progress_context.session_id
                    )
                    if cancellation_requested:
                        raise OptimizationCancelledException("User requested cancellation")
                
                # Calculate phase progress
                elapsed_time = time.time() - phase_tracker.phase_start_time
                estimated_progress = min(
                    95,  # Cap at 95% to avoid showing 100% before completion
                    (elapsed_time / phase_tracker.expected_duration) * 100
                )
                
                # Send progress update
                await self._update_progress(
                    phase_tracker.progress_context,
                    phase_tracker.phase_number,
                    f"{phase_tracker.phase_name} in progress... ({estimated_progress:.0f}%)",
                    phase_progress=estimated_progress
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue updates
                logger.warning(f"Progress update error: {e}")
```

**Implementation Requirements**:
- Implement comprehensive progress tracking with phase-level granularity
- Create async progress update system with cancellation support
- Add time estimation and remaining time calculation
- Build MCP-compatible progress notification system

### Task 1.5.2: Build Real-time MCP Communication System
**Acceptance Criteria Reference**: AC1, AC2  
**Estimated Hours**: 10  

```python
class MCPProgressNotifier:
    def __init__(self):
        self.active_sessions = {}
        self.notification_queue = asyncio.Queue()
        self.mcp_server = None  # Injected MCP server instance
    
    async def initialize(self, mcp_server):
        """Initialize with MCP server for real-time notifications"""
        self.mcp_server = mcp_server
        
        # Start notification processing task
        asyncio.create_task(self._process_notifications())
    
    async def send_progress_update(self, session_id: str, progress_data: Dict):
        """Send real-time progress update through MCP"""
        
        # Format progress data for MCP transmission
        mcp_progress = {
            "type": "optimization_progress",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "progress": {
                "percentage": progress_data.get("completion_percentage", 0),
                "current_phase": progress_data.get("current_phase", "Unknown"),
                "phase_number": progress_data.get("phase_number", 0),
                "total_phases": progress_data.get("total_phases", 6),
                "status_message": progress_data.get("status_message", "Processing..."),
                "estimated_remaining_time": progress_data.get("estimated_remaining_time", "Unknown")
            },
            "details": {
                "strategy_being_applied": progress_data.get("strategy_name", ""),
                "strategy_reasoning": progress_data.get("strategy_reasoning", ""),
                "current_optimizer": progress_data.get("current_optimizer", ""),
                "examples_count": progress_data.get("examples_count", 0),
                "performance_indicators": progress_data.get("performance_indicators", {})
            },
            "user_actions": {
                "can_cancel": progress_data.get("can_cancel", True),
                "can_modify": progress_data.get("can_modify", False),
                "cancel_url": f"/cancel/{session_id}" if progress_data.get("can_cancel") else None
            }
        }
        
        # Queue notification for processing
        await self.notification_queue.put(mcp_progress)
    
    async def _process_notifications(self):
        """Process queued notifications and send through MCP"""
        
        while True:
            try:
                # Get next notification from queue
                notification = await self.notification_queue.get()
                
                # Send through MCP server (implementation depends on MCP server capabilities)
                await self._send_mcp_notification(notification)
                
                # Mark task as done
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Failed to process MCP notification: {e}")
    
    async def _send_mcp_notification(self, notification: Dict):
        """Send notification through MCP protocol"""
        
        # Format as MCP resource update or streaming response
        if hasattr(self.mcp_server, 'send_resource_update'):
            # Use MCP resource update if available
            await self.mcp_server.send_resource_update(
                uri=f"optimization://progress/{notification['session_id']}",
                content=json.dumps(notification, indent=2)
            )
        else:
            # Fallback: Store in progress resource for client polling
            await self._store_progress_resource(notification)
    
    async def _store_progress_resource(self, notification: Dict):
        """Store progress as MCP resource for client access"""
        
        session_id = notification['session_id']
        
        # Store in progress store for MCP resource access
        await self.progress_store.update_session_progress(session_id, notification)
        
        # Update active sessions tracking
        self.active_sessions[session_id] = {
            "last_update": datetime.now(),
            "current_status": notification['progress']['status_message'],
            "progress_percentage": notification['progress']['percentage']
        }

# MCP Resource handlers for progress access
@app.list_resources()
async def list_resources() -> List[Resource]:
    """Include progress resources in MCP resource list"""
    
    resources = []
    
    # Add active optimization progress resources
    active_sessions = await progress_notifier.get_active_sessions()
    
    for session_id, session_info in active_sessions.items():
        resources.append(Resource(
            uri=f"optimization://progress/{session_id}",
            name=f"Optimization Progress: {session_id[:8]}...",
            description=f"Real-time progress for optimization session ({session_info['progress_percentage']:.0f}% complete)",
            mimeType="application/json"
        ))
    
    return resources

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Provide access to optimization progress resources"""
    
    if uri.startswith("optimization://progress/"):
        session_id = uri.split("/")[-1]
        
        progress_data = await progress_notifier.get_session_progress(session_id)
        
        if progress_data:
            return json.dumps(progress_data, indent=2)
        else:
            raise ValueError(f"No progress data found for session: {session_id}")
    
    raise ValueError(f"Unknown resource URI: {uri}")
```

**Implementation Requirements**:
- Implement MCP-compatible real-time notification system
- Create progress resource management for client access
- Add session tracking and cleanup for completed optimizations
- Build fallback mechanisms for MCP servers without streaming support

### Task 1.5.3: Create User Control and Cancellation System
**Acceptance Criteria Reference**: AC3  
**Estimated Hours**: 8  

```python
class OptimizationControlSystem:
    def __init__(self):
        self.cancellation_requests = {}
        self.active_optimizations = {}
        self.partial_results_store = PartialResultsStore()
        self.control_interface = ControlInterface()
    
    async def register_cancellable_optimization(self, session_id: str, 
                                               optimization_task: asyncio.Task):
        """Register optimization for user control"""
        
        control_metadata = {
            "session_id": session_id,
            "task": optimization_task,
            "start_time": datetime.now(),
            "cancellable_phases": ["module_compilation", "optimization_execution"],
            "partial_results": {},
            "status": "running"
        }
        
        self.active_optimizations[session_id] = control_metadata
        
        # Set up cancellation monitoring
        asyncio.create_task(self._monitor_cancellation_requests(session_id))
    
    async def request_cancellation(self, session_id: str, 
                                  reason: str = "user_request") -> Dict:
        """Handle user cancellation request"""
        
        if session_id not in self.active_optimizations:
            return {
                "success": False,
                "error": "Optimization session not found or already completed",
                "session_id": session_id
            }
        
        optimization_info = self.active_optimizations[session_id]
        
        # Check if optimization is in a cancellable phase
        current_phase = optimization_info.get("current_phase", "unknown")
        
        if current_phase not in optimization_info["cancellable_phases"]:
            return {
                "success": False,
                "error": f"Cannot cancel during {current_phase} phase",
                "reason": "Phase not safely cancellable",
                "estimated_completion": optimization_info.get("estimated_completion"),
                "session_id": session_id
            }
        
        # Set cancellation request
        self.cancellation_requests[session_id] = {
            "requested_at": datetime.now(),
            "reason": reason,
            "requester": "user"
        }
        
        # Cancel the optimization task
        optimization_task = optimization_info["task"]
        optimization_task.cancel()
        
        # Prepare partial results if available
        partial_results = await self._prepare_partial_results(session_id)
        
        return {
            "success": True,
            "message": "Optimization cancellation requested",
            "session_id": session_id,
            "partial_results_available": len(partial_results) > 0,
            "partial_results": partial_results,
            "cancellation_time": datetime.now().isoformat(),
            "retry_options": await self._generate_retry_options(session_id)
        }
    
    async def _prepare_partial_results(self, session_id: str) -> Dict:
        """Prepare partial results from cancelled optimization"""
        
        optimization_info = self.active_optimizations.get(session_id, {})
        partial_results = optimization_info.get("partial_results", {})
        
        # Compile available partial results
        compiled_results = {}
        
        if "strategy_detection" in partial_results:
            compiled_results["detected_strategy"] = {
                "strategy_name": partial_results["strategy_detection"]["strategy_name"],
                "confidence": partial_results["strategy_detection"]["confidence"],
                "reasoning": partial_results["strategy_detection"]["reasoning"],
                "task_type": partial_results["strategy_detection"]["task_type"]
            }
        
        if "example_mining" in partial_results:
            compiled_results["mined_examples"] = {
                "count": len(partial_results["example_mining"]["examples"]),
                "average_quality": partial_results["example_mining"]["average_quality"],
                "diversity_score": partial_results["example_mining"]["diversity_score"]
            }
        
        if "partial_optimization" in partial_results:
            compiled_results["partial_optimization"] = {
                "intermediate_result": partial_results["partial_optimization"]["result"],
                "completion_percentage": partial_results["partial_optimization"]["completion"],
                "quality_indicators": partial_results["partial_optimization"]["quality_metrics"]
            }
        
        return compiled_results
    
    async def _generate_retry_options(self, session_id: str) -> List[Dict]:
        """Generate retry options based on cancellation context"""
        
        optimization_info = self.active_optimizations.get(session_id, {})
        partial_results = optimization_info.get("partial_results", {})
        
        retry_options = []
        
        # Option 1: Resume with faster strategy
        if "strategy_detection" in partial_results:
            retry_options.append({
                "option": "fast_retry",
                "description": "Retry with faster optimization strategy",
                "estimated_time": "10-15 seconds",
                "strategy_changes": "Use BootstrapFewShot instead of MIPRO",
                "expected_quality": "Good (may be slightly lower than original strategy)"
            })
        
        # Option 2: Retry with cached components
        if "example_mining" in partial_results:
            retry_options.append({
                "option": "cached_retry",
                "description": "Retry using already mined examples",
                "estimated_time": "15-20 seconds",
                "strategy_changes": "Skip example mining phase",
                "expected_quality": "Same as intended original optimization"
            })
        
        # Option 3: Basic optimization fallback
        retry_options.append({
            "option": "basic_optimization",
            "description": "Use basic optimization without DSPy compilation",
            "estimated_time": "3-5 seconds",
            "strategy_changes": "Use traditional optimization strategies",
            "expected_quality": "Moderate (faster but less sophisticated)"
        })
        
        return retry_options
    
    async def _monitor_cancellation_requests(self, session_id: str):
        """Monitor for cancellation requests during optimization"""
        
        while session_id in self.active_optimizations:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                # Check if cancellation was requested
                if session_id in self.cancellation_requests:
                    cancellation_info = self.cancellation_requests[session_id]
                    
                    # Log cancellation
                    logger.info(f"Cancellation requested for session {session_id}: {cancellation_info['reason']}")
                    
                    # Clean up
                    await self._cleanup_cancelled_session(session_id)
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring cancellation for {session_id}: {e}")
    
    async def _cleanup_cancelled_session(self, session_id: str):
        """Clean up resources for cancelled optimization session"""
        
        # Store partial results for potential retry
        if session_id in self.active_optimizations:
            optimization_info = self.active_optimizations[session_id]
            
            if optimization_info.get("partial_results"):
                await self.partial_results_store.store_partial_results(
                    session_id, optimization_info["partial_results"]
                )
        
        # Clean up tracking
        self.active_optimizations.pop(session_id, None)
        self.cancellation_requests.pop(session_id, None)
        
        # Notify progress system of cancellation
        await self.progress_notifier.send_cancellation_notification(session_id)

# MCP tool for cancellation requests
Tool(
    name="cancel_optimization",
    description="Cancel a running optimization and get partial results",
    inputSchema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "ID of the optimization session to cancel"
            },
            "reason": {
                "type": "string",
                "optional": True,
                "description": "Reason for cancellation"
            }
        },
        "required": ["session_id"]
    }
)

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle cancellation tool calls"""
    
    if name == "cancel_optimization":
        session_id = arguments["session_id"]
        reason = arguments.get("reason", "User requested cancellation")
        
        result = await control_system.request_cancellation(session_id, reason)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
```

**Implementation Requirements**:
- Implement safe cancellation system with phase awareness
- Create partial results collection and storage
- Add retry option generation based on cancellation context
- Build user-friendly cancellation interface through MCP tools

### Task 1.5.4: Create Process Explanation and Transparency System
**Acceptance Criteria Reference**: AC2  
**Estimated Hours**: 6  

```python
class OptimizationTransparencySystem:
    def __init__(self):
        self.explanation_generator = ExplanationGenerator()
        self.strategy_explainer = StrategyExplainer()
        self.time_estimator = TimeEstimator()
        self.decision_tracker = DecisionTracker()
    
    async def generate_progress_explanation(self, progress_context: ProgressContext,
                                           phase_info: Dict) -> Dict:
        """Generate transparent explanation of current optimization phase"""
        
        explanation = {
            "current_activity": {
                "phase_name": phase_info["phase_name"],
                "phase_description": await self._get_phase_description(phase_info["phase_name"]),
                "why_necessary": await self._explain_phase_necessity(phase_info),
                "technical_details": await self._get_technical_details(phase_info),
                "user_friendly_summary": await self._generate_user_summary(phase_info)
            },
            "strategy_context": {
                "selected_strategy": phase_info.get("strategy_name", ""),
                "strategy_reasoning": phase_info.get("strategy_reasoning", ""),
                "why_this_strategy": await self._explain_strategy_choice(phase_info),
                "alternative_strategies": phase_info.get("alternative_strategies", []),
                "expected_benefits": await self._describe_strategy_benefits(phase_info)
            },
            "time_estimates": {
                "current_phase_remaining": await self._estimate_phase_remaining_time(phase_info),
                "total_remaining": await self._estimate_total_remaining_time(progress_context),
                "confidence_level": await self._get_time_estimate_confidence(progress_context),
                "factors_affecting_time": await self._get_time_factors(phase_info)
            },
            "decision_rationale": {
                "key_decisions": await self._get_key_decisions(progress_context),
                "decision_reasoning": await self._explain_decisions(progress_context),
                "quality_tradeoffs": await self._explain_quality_tradeoffs(phase_info),
                "user_impact": await self._describe_user_impact(phase_info)
            }
        }
        
        return explanation
    
    async def _get_phase_description(self, phase_name: str) -> str:
        """Get user-friendly description of optimization phase"""
        
        phase_descriptions = {
            "Strategy Detection": "Analyzing your prompt to determine the best optimization approach. This involves understanding the type of task, complexity level, and most suitable DSPy techniques.",
            
            "Example Mining": "Finding high-quality examples from successful past optimizations to train the AI model. This ensures your optimization benefits from proven patterns.",
            
            "Module Compilation": "Building a custom AI model specifically optimized for your type of prompt. This is the most time-intensive but crucial step for maximum improvement.",
            
            "Optimization Execution": "Running your prompt through the compiled model to generate the optimized version. The AI applies learned patterns to improve your prompt.",
            
            "Results Analysis": "Evaluating the optimization quality and preparing insights about the improvements made to your prompt.",
            
            "Finalization": "Packaging the results and preparing recommendations for using your optimized prompt effectively."
        }
        
        return phase_descriptions.get(phase_name, f"Processing {phase_name}...")
    
    async def _explain_strategy_choice(self, phase_info: Dict) -> str:
        """Explain why a particular strategy was chosen"""
        
        strategy_name = phase_info.get("strategy_name", "")
        
        if not strategy_name:
            return "Strategy selection in progress..."
        
        # Generate explanation based on strategy characteristics
        strategy_explanations = {
            "reasoning": "Your prompt requires step-by-step thinking and logical analysis. The reasoning strategy excels at creating prompts that guide AI through complex problem-solving processes.",
            
            "classification": "Your prompt involves categorizing or labeling content. The classification strategy optimizes prompts to improve accuracy and consistency in categorization tasks.",
            
            "generation": "Your prompt focuses on creating new content. The generation strategy enhances creativity while maintaining coherence and relevance to your requirements.",
            
            "analysis": "Your prompt involves examining and interpreting information. The analysis strategy optimizes prompts to produce more thorough and insightful analytical outputs."
        }
        
        base_explanation = strategy_explanations.get(
            strategy_name, 
            f"The {strategy_name} strategy was selected based on your prompt's characteristics."
        )
        
        # Add context-specific details
        if "confidence" in phase_info:
            confidence = phase_info["confidence"]
            if confidence > 0.9:
                base_explanation += f" This choice has very high confidence ({confidence:.1%}) based on clear indicators in your prompt."
            elif confidence > 0.7:
                base_explanation += f" This choice has good confidence ({confidence:.1%}) based on prompt analysis."
            else:
                base_explanation += f" This choice has moderate confidence ({confidence:.1%}). Alternative strategies were also considered."
        
        return base_explanation
    
    async def _estimate_phase_remaining_time(self, phase_info: Dict) -> str:
        """Estimate remaining time for current phase"""
        
        phase_name = phase_info.get("phase_name", "")
        elapsed_time = phase_info.get("elapsed_time", 0)
        expected_duration = phase_info.get("expected_duration", 0)
        
        if expected_duration <= 0:
            return "Calculating..."
        
        remaining_time = max(0, expected_duration - elapsed_time)
        
        if remaining_time < 2:
            return "Almost complete"
        elif remaining_time < 10:
            return f"~{remaining_time:.0f} seconds"
        elif remaining_time < 60:
            return f"~{remaining_time:.0f} seconds"
        else:
            return f"~{remaining_time/60:.1f} minutes"
    
    async def _get_key_decisions(self, progress_context: ProgressContext) -> List[Dict]:
        """Get key decisions made during optimization"""
        
        decisions = []
        
        # Strategy selection decision
        if hasattr(progress_context, 'strategy_selection'):
            decisions.append({
                "decision": "Strategy Selection",
                "choice": progress_context.strategy_selection.get("strategy_name", ""),
                "reasoning": progress_context.strategy_selection.get("reasoning", ""),
                "alternatives_considered": progress_context.strategy_selection.get("alternatives", [])
            })
        
        # Optimizer selection decision
        if hasattr(progress_context, 'optimizer_selection'):
            decisions.append({
                "decision": "Optimizer Selection",
                "choice": progress_context.optimizer_selection.get("optimizer_name", ""),
                "reasoning": progress_context.optimizer_selection.get("reasoning", ""),
                "expected_performance": progress_context.optimizer_selection.get("expected_performance", "")
            })
        
        # Example selection decision
        if hasattr(progress_context, 'example_selection'):
            decisions.append({
                "decision": "Training Examples",
                "choice": f"{progress_context.example_selection.get('count', 0)} high-quality examples",
                "reasoning": progress_context.example_selection.get("selection_criteria", ""),
                "quality_metrics": progress_context.example_selection.get("quality_metrics", {})
            })
        
        return decisions
    
    async def _describe_user_impact(self, phase_info: Dict) -> str:
        """Describe how current phase will impact the final result"""
        
        phase_name = phase_info.get("phase_name", "")
        
        impact_descriptions = {
            "Strategy Detection": "Ensures your optimized prompt uses the most effective approach for your specific use case, leading to better results.",
            
            "Example Mining": "Provides the AI with proven successful patterns, significantly improving the quality and reliability of your optimization.",
            
            "Module Compilation": "Creates a specialized AI model tailored to your needs, maximizing the improvement potential for your prompt.",
            
            "Optimization Execution": "Applies all the learned optimizations to transform your prompt into a more effective version.",
            
            "Results Analysis": "Provides insights into what was improved and how to best use your optimized prompt.",
            
            "Finalization": "Ensures you receive complete, actionable results with clear guidance for implementation."
        }
        
        return impact_descriptions.get(
            phase_name,
            "This phase contributes to the overall optimization quality and effectiveness."
        )
```

**Implementation Requirements**:
- Implement comprehensive explanation generation for all optimization phases
- Create user-friendly descriptions that explain technical processes clearly
- Add decision rationale tracking and explanation
- Build time estimation with confidence levels and affecting factors

## Dev Notes

### Technical Implementation Context

**MCP Protocol Integration**:
- Implements progress updates through MCP resource system
- Uses MCP tool interface for cancellation requests
- Maintains compatibility with Claude Desktop's UI capabilities
- Provides fallback for MCP servers without streaming support

**Real-time Communication Architecture**:
- Async queue-based notification system for non-blocking progress updates
- WebSocket-style communication pattern adapted for MCP protocol
- Resource-based progress tracking with automatic cleanup
- Session management for concurrent optimization tracking

**User Experience Design**:
- Progress updates every 2-5 seconds to maintain engagement
- Clear, jargon-free explanations of technical processes
- Actionable cancellation with partial results recovery
- Retry options based on optimization context and partial completion

**Performance Considerations**:
- Minimal overhead for progress tracking (<5% of total processing time)
- Efficient resource cleanup for completed sessions
- Async processing to avoid blocking optimization pipeline
- Caching of explanations and time estimates

**Error Handling Strategy**:
- Graceful handling of progress tracking failures without affecting optimization
- Safe cancellation with resource cleanup and partial results preservation
- Comprehensive logging for debugging progress system issues
- Fallback to basic completion notifications if detailed progress fails

**Testing Strategy**:
- Unit tests for progress calculation and explanation generation
- Integration tests with actual optimization pipeline
- User experience testing for progress clarity and usefulness
- Performance tests ensuring minimal impact on optimization speed

## Definition of Done

**Story 1.5 is complete when:**
- ✅ Real-time progress updates are sent every 5 seconds during optimization
- ✅ Progress updates include clear explanations of current activities and reasoning
- ✅ Users can safely cancel optimization and receive partial results
- ✅ Time estimates are accurate and updated based on actual performance
- ✅ All progress information is accessible through MCP protocol
- ✅ Cancellation system provides retry options with different strategies
- ✅ Transparency system explains strategy choices and technical decisions
- ✅ All acceptance criteria validated through comprehensive testing
- ✅ Integration with MCP server maintains protocol compliance
- ✅ User experience testing confirms progress updates improve perceived performance
- ✅ Error handling maintains system stability during progress tracking
- ✅ Code review completed and quality gates passed
- ✅ Documentation includes progress system architecture and usage patterns

**Ready for Story 1.6: Strategy Performance Analytics**