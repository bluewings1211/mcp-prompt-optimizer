# Story 1.4: Intelligent Module Compilation

## Status
[Approved]

## User Story
**As a** system administrator  
**I want** DSPy modules to be compiled with the optimal optimizer for each task  
**So that** optimization performance is maximized automatically  

## Business Value
- **Primary Value**: Maximizes optimization effectiveness through intelligent compiler selection
- **User Impact**: Delivers 25%+ improvement over baseline with optimal compilation strategies
- **Success Metric**: Module compilation <30 seconds with >90% performance consistency

## Acceptance Criteria

### AC1: Automatic Optimizer Selection
- **GIVEN** a DSPy signature and set of training examples  
- **WHEN** compiling a module for optimization  
- **THEN** the system automatically selects the best optimizer (MIPRO, BootstrapFewShot, COPRO, etc.)  
- **AND** optimizer selection is based on task type, example count, and performance requirements  
- **AND** provides rationale for optimizer choice with confidence score  

### AC2: Performance and Speed Requirements
- **GIVEN** module compilation is initiated  
- **WHEN** the compilation process runs  
- **THEN** compilation completes in under 30 seconds for 95% of requests  
- **AND** compiled modules show 25%+ improvement over baseline performance  
- **AND** compilation success rate is >90% with proper error handling  

### AC3: Intelligent Caching and Reuse
- **GIVEN** similar signatures and example sets have been compiled before  
- **WHEN** a new compilation request is received  
- **THEN** system checks cache for compatible compiled modules  
- **AND** reuses cached modules when similarity score >0.8  
- **AND** updates cache with new high-performance modules  

## Detailed Tasks

### Task 1.4.1: Implement Intelligent Optimizer Selection System
**Acceptance Criteria Reference**: AC1  
**Estimated Hours**: 14  

```python
class DSPyModuleCompiler:
    def __init__(self):
        self.optimizers = {
            'mipro': dspy.MIPRO,
            'bootstrap': dspy.BootstrapFewShot,
            'copro': dspy.COPRO,
            'signature_opt': dspy.SignatureOptimizer,
            'teleprompt': dspy.teleprompt.BootstrapFewShotWithRandomSearch
        }
        self.performance_tracker = CompilerPerformanceTracker()
        self.optimizer_selector = OptimizerSelector()
        self.config_optimizer = CompilerConfigOptimizer()
    
    async def compile_optimized_module(self, signature: dspy.Signature, 
                                      examples: List[Dict], 
                                      optimize_for: str = "quality",
                                      strategy: str = 'auto') -> CompiledModuleResult:
        """Compile DSPy module with intelligent optimizer selection"""
        
        compilation_context = CompilationContext(
            signature=signature,
            examples=examples,
            optimize_for=optimize_for,
            example_count=len(examples),
            task_complexity=self._assess_task_complexity(signature, examples),
            performance_requirements=self._parse_performance_requirements(optimize_for)
        )
        
        # Phase 1: Select optimal optimizer
        if strategy == 'auto':
            optimizer_selection = await self.optimizer_selector.select_optimal_optimizer(
                compilation_context
            )
        else:
            optimizer_selection = OptimizerSelection(
                optimizer_name=strategy,
                confidence=0.8,  # Manual selection gets default confidence
                reasoning="Manual optimizer selection"
            )
        
        # Phase 2: Configure optimizer parameters
        optimizer_config = await self.config_optimizer.optimize_configuration(
            optimizer_selection.optimizer_name,
            compilation_context
        )
        
        # Phase 3: Execute compilation with monitoring
        compilation_start = time.time()
        
        try:
            compiled_module = await self._execute_compilation(
                compilation_context,
                optimizer_selection,
                optimizer_config
            )
            
            compilation_time = time.time() - compilation_start
            
            # Phase 4: Validate and benchmark compiled module
            performance_metrics = await self._validate_compiled_module(
                compiled_module, examples, compilation_context
            )
            
            # Phase 5: Create result with comprehensive metadata
            result = CompiledModuleResult(
                module=compiled_module,
                optimizer_used=optimizer_selection.optimizer_name,
                optimizer_config=optimizer_config,
                compilation_time=compilation_time,
                performance_metrics=performance_metrics,
                optimizer_selection_rationale=optimizer_selection.reasoning,
                compilation_context=compilation_context,
                cache_key=self._generate_cache_key(signature, examples)
            )
            
            # Phase 6: Performance tracking and learning
            await self.performance_tracker.record_compilation_result(result)
            
            return result
            
        except CompilationTimeoutError as e:
            return await self._handle_compilation_timeout(compilation_context, e)
        except DSPyCompilationError as e:
            return await self._handle_compilation_error(compilation_context, e)
    
    async def _execute_compilation(self, context: CompilationContext,
                                  optimizer_selection: OptimizerSelection,
                                  optimizer_config: Dict) -> dspy.Module:
        """Execute the actual DSPy module compilation"""
        
        # Create base module with signature
        if context.task_complexity == 'high':
            base_module = dspy.ChainOfThoughtWithHint(context.signature)
        elif 'reasoning' in str(context.signature).lower():
            base_module = dspy.ChainOfThought(context.signature)
        else:
            base_module = dspy.Predict(context.signature)
        
        # Initialize selected optimizer
        optimizer_class = self.optimizers[optimizer_selection.optimizer_name]
        
        if optimizer_selection.optimizer_name == 'mipro':
            optimizer = optimizer_class(
                prompt_model=dspy.OpenAI(model="gpt-4", max_tokens=1000),
                task_model=dspy.OpenAI(model="gpt-3.5-turbo"),
                metric=self._create_task_specific_metric(context),
                num_candidates=optimizer_config.get('num_candidates', 10),
                init_temperature=optimizer_config.get('init_temperature', 1.4),
                verbose=optimizer_config.get('verbose', False)
            )
        elif optimizer_selection.optimizer_name == 'bootstrap':
            optimizer = optimizer_class(
                metric=self._create_task_specific_metric(context),
                max_bootstrapped_demos=optimizer_config.get('max_demos', 8),
                max_labeled_demos=optimizer_config.get('max_labeled', 16),
                teacher_settings=optimizer_config.get('teacher_settings', {})
            )
        elif optimizer_selection.optimizer_name == 'copro':
            optimizer = optimizer_class(
                metric=self._create_task_specific_metric(context),
                breadth=optimizer_config.get('breadth', 10),
                depth=optimizer_config.get('depth', 3),
                init_temperature=optimizer_config.get('init_temperature', 1.4)
            )
        else:
            # Default configuration for other optimizers
            optimizer = optimizer_class(
                metric=self._create_task_specific_metric(context),
                **optimizer_config
            )
        
        # Prepare training and validation sets
        train_examples = context.examples[:int(len(context.examples) * 0.8)]
        val_examples = context.examples[int(len(context.examples) * 0.8):]
        
        # Execute compilation with timeout
        with timeout_context(30.0):  # 30 second timeout
            compiled_module = optimizer.compile(
                base_module,
                trainset=train_examples,
                valset=val_examples if val_examples else train_examples[:5]
            )
        
        return compiled_module
```

**Implementation Requirements**:
- Implement comprehensive optimizer selection based on task characteristics
- Create configuration optimization for each DSPy optimizer type
- Add task complexity assessment for appropriate base module selection
- Build timeout handling and error recovery for compilation failures

### Task 1.4.2: Build Optimizer Selection Intelligence
**Acceptance Criteria Reference**: AC1  
**Estimated Hours**: 12  

```python
class OptimizerSelector:
    def __init__(self):
        self.performance_history = PerformanceHistory()
        self.task_analyzer = TaskAnalyzer()
        self.optimizer_characteristics = {
            'mipro': {
                'best_for': ['complex_reasoning', 'multi_step_tasks'],
                'min_examples': 10,
                'max_examples': 200,
                'avg_compile_time': 25.0,
                'performance_consistency': 0.9,
                'complexity_handling': 'high'
            },
            'bootstrap': {
                'best_for': ['few_shot_learning', 'simple_classification'],
                'min_examples': 5,
                'max_examples': 50,
                'avg_compile_time': 8.0,
                'performance_consistency': 0.85,
                'complexity_handling': 'medium'
            },
            'copro': {
                'best_for': ['creative_generation', 'open_ended_tasks'],
                'min_examples': 8,
                'max_examples': 100,
                'avg_compile_time': 15.0,
                'performance_consistency': 0.8,
                'complexity_handling': 'medium'
            },
            'signature_opt': {
                'best_for': ['signature_refinement', 'prompt_structure'],
                'min_examples': 15,
                'max_examples': 75,
                'avg_compile_time': 12.0,
                'performance_consistency': 0.75,
                'complexity_handling': 'low'
            }
        }
    
    async def select_optimal_optimizer(self, context: CompilationContext) -> OptimizerSelection:
        """Select the optimal DSPy optimizer based on compilation context"""
        
        # Phase 1: Analyze task characteristics
        task_analysis = await self.task_analyzer.analyze_task(
            context.signature, context.examples
        )
        
        # Phase 2: Score each optimizer for this context
        optimizer_scores = {}
        
        for optimizer_name, characteristics in self.optimizer_characteristics.items():
            score = await self._score_optimizer_for_context(
                optimizer_name, characteristics, context, task_analysis
            )
            optimizer_scores[optimizer_name] = score
        
        # Phase 3: Consider historical performance
        historical_performance = await self.performance_history.get_optimizer_performance(
            task_type=task_analysis.task_type,
            example_count_range=(len(context.examples) - 5, len(context.examples) + 5),
            time_window=timedelta(days=90)
        )
        
        # Adjust scores based on historical performance
        for optimizer_name in optimizer_scores:
            if optimizer_name in historical_performance:
                historical_factor = historical_performance[optimizer_name]['success_rate']
                optimizer_scores[optimizer_name] *= (0.7 + 0.3 * historical_factor)
        
        # Phase 4: Select best optimizer with confidence calculation
        best_optimizer = max(optimizer_scores.items(), key=lambda x: x[1])
        
        confidence = self._calculate_selection_confidence(
            best_optimizer[1], optimizer_scores
        )
        
        reasoning = self._generate_selection_reasoning(
            best_optimizer[0], context, task_analysis, optimizer_scores
        )
        
        return OptimizerSelection(
            optimizer_name=best_optimizer[0],
            confidence=confidence,
            reasoning=reasoning,
            alternative_optimizers=self._get_alternative_recommendations(optimizer_scores),
            selection_factors=self._get_selection_factors(best_optimizer[0], context)
        )
    
    async def _score_optimizer_for_context(self, optimizer_name: str, 
                                          characteristics: Dict,
                                          context: CompilationContext,
                                          task_analysis: TaskAnalysis) -> float:
        """Score how well an optimizer fits the compilation context"""
        
        score_factors = {}
        
        # Factor 1: Task type compatibility
        task_compatibility = 0.5  # Default neutral
        if task_analysis.task_type in characteristics['best_for']:
            task_compatibility = 1.0
        elif any(task_type in task_analysis.secondary_types for task_type in characteristics['best_for']):
            task_compatibility = 0.8
        
        score_factors['task_compatibility'] = task_compatibility
        
        # Factor 2: Example count suitability
        example_count = len(context.examples)
        if characteristics['min_examples'] <= example_count <= characteristics['max_examples']:
            example_suitability = 1.0
        elif example_count < characteristics['min_examples']:
            example_suitability = max(0.3, example_count / characteristics['min_examples'])
        else:
            example_suitability = max(0.5, characteristics['max_examples'] / example_count)
        
        score_factors['example_suitability'] = example_suitability
        
        # Factor 3: Performance requirements alignment
        if context.optimize_for == 'speed':
            time_factor = 1.0 - (characteristics['avg_compile_time'] / 30.0)  # Normalize to 30s max
        elif context.optimize_for == 'quality':
            time_factor = characteristics['performance_consistency']
        else:  # balanced
            time_factor = (characteristics['performance_consistency'] + 
                          (1.0 - characteristics['avg_compile_time'] / 30.0)) / 2
        
        score_factors['performance_alignment'] = max(0.2, time_factor)
        
        # Factor 4: Complexity handling capability
        complexity_scores = {'low': 0.5, 'medium': 0.75, 'high': 1.0}
        complexity_match = complexity_scores.get(
            characteristics['complexity_handling'], 0.5
        )
        
        if context.task_complexity == 'high' and characteristics['complexity_handling'] != 'high':
            complexity_match *= 0.7
        
        score_factors['complexity_handling'] = complexity_match
        
        # Weighted composite score
        composite_score = (
            score_factors['task_compatibility'] * 0.35 +
            score_factors['example_suitability'] * 0.25 +
            score_factors['performance_alignment'] * 0.25 +
            score_factors['complexity_handling'] * 0.15
        )
        
        return composite_score
    
    def _generate_selection_reasoning(self, selected_optimizer: str,
                                    context: CompilationContext,
                                    task_analysis: TaskAnalysis,
                                    all_scores: Dict) -> str:
        """Generate human-readable reasoning for optimizer selection"""
        
        characteristics = self.optimizer_characteristics[selected_optimizer]
        
        reasoning_parts = [
            f"Selected {selected_optimizer} optimizer based on:",
            f"- Task type '{task_analysis.task_type}' matches optimizer strengths in {characteristics['best_for']}",
            f"- Example count ({len(context.examples)}) fits optimal range {characteristics['min_examples']}-{characteristics['max_examples']}",
            f"- Optimizer handles {characteristics['complexity_handling']} complexity tasks well",
            f"- Expected compilation time: ~{characteristics['avg_compile_time']:.1f}s",
            f"- Performance consistency: {characteristics['performance_consistency']:.1%}"
        ]
        
        if context.optimize_for == 'speed':
            reasoning_parts.append(f"- Prioritized for speed optimization")
        elif context.optimize_for == 'quality':
            reasoning_parts.append(f"- Prioritized for quality optimization")
        
        return "\n".join(reasoning_parts)
```

**Implementation Requirements**:
- Implement multi-factor scoring system for optimizer selection
- Create task analysis system for understanding compilation requirements
- Add historical performance tracking and integration
- Build comprehensive reasoning generation for transparency

### Task 1.4.3: Implement Intelligent Caching System
**Acceptance Criteria Reference**: AC3  
**Estimated Hours**: 10  

```python
class IntelligentModuleCache:
    def __init__(self):
        self.redis_cache = RedisCache()
        self.similarity_calculator = ModuleSimilarityCalculator()
        self.cache_performance_tracker = CachePerformanceTracker()
        self.cache_policies = CachePolicies()
    
    async def get_cached_module(self, signature: dspy.Signature, 
                               examples: List[Dict],
                               context: CompilationContext) -> Optional[CachedModuleResult]:
        """Retrieve compatible cached module if available"""
        
        # Generate cache key for exact match first
        exact_cache_key = self._generate_exact_cache_key(signature, examples)
        exact_match = await self.redis_cache.get(exact_cache_key)
        
        if exact_match:
            await self.cache_performance_tracker.record_cache_hit('exact', exact_cache_key)
            return CachedModuleResult(
                module=exact_match['module'],
                match_type='exact',
                similarity_score=1.0,
                cache_metadata=exact_match['metadata']
            )
        
        # Look for similar cached modules
        similar_matches = await self._find_similar_cached_modules(
            signature, examples, context
        )
        
        if similar_matches:
            # Select best similar match
            best_match = max(similar_matches, key=lambda x: x['similarity_score'])
            
            if best_match['similarity_score'] >= 0.8:  # High similarity threshold
                await self.cache_performance_tracker.record_cache_hit('similar', best_match['cache_key'])
                return CachedModuleResult(
                    module=best_match['module'],
                    match_type='similar',
                    similarity_score=best_match['similarity_score'],
                    cache_metadata=best_match['metadata'],
                    adaptation_required=best_match['similarity_score'] < 0.95
                )
        
        # No suitable cached module found
        await self.cache_performance_tracker.record_cache_miss(exact_cache_key)
        return None
    
    async def cache_compiled_module(self, compiled_result: CompiledModuleResult):
        """Cache compiled module with intelligent metadata"""
        
        cache_entry = {
            'module': compiled_result.module,
            'signature_hash': self._hash_signature(compiled_result.compilation_context.signature),
            'examples_hash': self._hash_examples(compiled_result.compilation_context.examples),
            'optimizer_used': compiled_result.optimizer_used,
            'performance_metrics': compiled_result.performance_metrics,
            'compilation_time': compiled_result.compilation_time,
            'task_characteristics': self._extract_task_characteristics(compiled_result),
            'cache_timestamp': datetime.now(),
            'usage_count': 0,
            'success_rate': 1.0  # Initialize with optimistic success rate
        }
        
        # Determine cache TTL based on performance and characteristics
        cache_ttl = self._calculate_cache_ttl(compiled_result)
        
        # Store in cache
        await self.redis_cache.setex(
            compiled_result.cache_key,
            cache_ttl,
            cache_entry
        )
        
        # Update cache index for similarity searches
        await self._update_cache_index(compiled_result.cache_key, cache_entry)
    
    async def _find_similar_cached_modules(self, signature: dspy.Signature,
                                          examples: List[Dict],
                                          context: CompilationContext) -> List[Dict]:
        """Find cached modules with similar characteristics"""
        
        # Get candidate modules from cache index
        candidate_cache_keys = await self._get_candidate_cache_keys(context)
        
        similar_matches = []
        
        for cache_key in candidate_cache_keys:
            cached_entry = await self.redis_cache.get(cache_key)
            if not cached_entry:
                continue
            
            # Calculate similarity score
            similarity_score = await self.similarity_calculator.calculate_module_similarity(
                target_signature=signature,
                target_examples=examples,
                target_context=context,
                cached_signature_hash=cached_entry['signature_hash'],
                cached_examples_hash=cached_entry['examples_hash'],
                cached_characteristics=cached_entry['task_characteristics']
            )
            
            if similarity_score >= 0.6:  # Minimum similarity threshold
                similar_matches.append({
                    'cache_key': cache_key,
                    'module': cached_entry['module'],
                    'similarity_score': similarity_score,
                    'metadata': cached_entry,
                    'performance_history': cached_entry.get('success_rate', 0.8)
                })
        
        return similar_matches
    
    def _calculate_cache_ttl(self, compiled_result: CompiledModuleResult) -> timedelta:
        """Calculate appropriate TTL for cached module based on performance"""
        
        base_ttl = timedelta(hours=24)  # Default 24 hours
        
        # Extend TTL for high-performing modules
        if compiled_result.performance_metrics.get('improvement_score', 0) > 0.4:
            base_ttl *= 2  # 48 hours for high-performing modules
        
        # Extend TTL for expensive compilations
        if compiled_result.compilation_time > 20.0:
            base_ttl *= 1.5  # 36 hours for expensive compilations
        
        # Reduce TTL for experimental or uncertain optimizers
        if compiled_result.optimizer_selection_rationale and 'experimental' in compiled_result.optimizer_selection_rationale.lower():
            base_ttl *= 0.5  # 12 hours for experimental modules
        
        return base_ttl
```

**Implementation Requirements**:
- Implement exact and similarity-based cache matching
- Create module similarity calculation using signature and example analysis
- Add intelligent TTL calculation based on module performance
- Build cache index for efficient similarity searches

### Task 1.4.4: Create Compilation Performance Monitoring
**Acceptance Criteria Reference**: AC2  
**Estimated Hours**: 8  

```python
class CompilerPerformanceTracker:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.performance_database = PerformanceDatabase()
        self.alerting_system = AlertingSystem()
        self.analytics_engine = AnalyticsEngine()
    
    async def record_compilation_result(self, result: CompiledModuleResult):
        """Record compilation performance for monitoring and analysis"""
        
        performance_record = {
            'compilation_id': str(uuid.uuid4()),
            'timestamp': datetime.now(),
            'optimizer_used': result.optimizer_used,
            'compilation_time': result.compilation_time,
            'example_count': len(result.compilation_context.examples),
            'task_type': result.compilation_context.signature,
            'task_complexity': result.compilation_context.task_complexity,
            'performance_metrics': result.performance_metrics,
            'success': result.performance_metrics.get('compilation_success', True),
            'improvement_score': result.performance_metrics.get('improvement_score', 0),
            'validation_score': result.performance_metrics.get('validation_score', 0),
            'cache_hit': result.performance_metrics.get('from_cache', False),
            'optimizer_config': result.optimizer_config
        }
        
        # Store performance record
        await self.performance_database.save_compilation_record(performance_record)
        
        # Update real-time metrics
        await self._update_real_time_metrics(performance_record)
        
        # Check for performance anomalies
        await self._check_performance_anomalies(performance_record)
        
        # Update optimizer performance statistics
        await self._update_optimizer_statistics(result)
    
    async def _update_real_time_metrics(self, record: Dict):
        """Update Prometheus metrics for real-time monitoring"""
        
        # Compilation time distribution
        compilation_time_histogram.observe(record['compilation_time'])
        
        # Success rate by optimizer
        if record['success']:
            compilation_success_counter.labels(
                optimizer=record['optimizer_used']
            ).inc()
        else:
            compilation_failure_counter.labels(
                optimizer=record['optimizer_used'],
                task_type=record['task_type']
            ).inc()
        
        # Performance improvement distribution
        if 'improvement_score' in record:
            improvement_score_histogram.observe(record['improvement_score'])
        
        # Cache hit rate
        if record['cache_hit']:
            cache_hit_counter.inc()
        else:
            cache_miss_counter.inc()
    
    async def _check_performance_anomalies(self, record: Dict):
        """Check for performance anomalies and trigger alerts"""
        
        anomaly_checks = [
            ('compilation_timeout', record['compilation_time'] > 30.0),
            ('low_improvement', record.get('improvement_score', 0) < 0.1),
            ('validation_failure', record.get('validation_score', 1.0) < 0.5),
            ('compilation_failure', not record['success'])
        ]
        
        for anomaly_type, is_anomaly in anomaly_checks:
            if is_anomaly:
                await self.alerting_system.trigger_anomaly_alert(
                    anomaly_type=anomaly_type,
                    record=record,
                    severity='medium' if anomaly_type != 'compilation_failure' else 'high'
                )
    
    async def generate_performance_report(self, time_window: timedelta = timedelta(days=7)) -> Dict:
        """Generate comprehensive performance report"""
        
        records = await self.performance_database.get_records_in_window(time_window)
        
        if not records:
            return {'error': 'No compilation records found in time window'}
        
        # Overall statistics
        total_compilations = len(records)
        successful_compilations = len([r for r in records if r['success']])
        success_rate = successful_compilations / total_compilations
        
        avg_compilation_time = np.mean([r['compilation_time'] for r in records])
        avg_improvement_score = np.mean([
            r.get('improvement_score', 0) for r in records if r['success']
        ])
        
        # Optimizer performance breakdown
        optimizer_stats = {}
        for record in records:
            optimizer = record['optimizer_used']
            if optimizer not in optimizer_stats:
                optimizer_stats[optimizer] = {
                    'total_uses': 0,
                    'successes': 0,
                    'total_time': 0,
                    'total_improvement': 0
                }
            
            stats = optimizer_stats[optimizer]
            stats['total_uses'] += 1
            stats['total_time'] += record['compilation_time']
            
            if record['success']:
                stats['successes'] += 1
                stats['total_improvement'] += record.get('improvement_score', 0)
        
        # Calculate derived metrics for each optimizer
        for optimizer, stats in optimizer_stats.items():
            stats['success_rate'] = stats['successes'] / stats['total_uses']
            stats['avg_time'] = stats['total_time'] / stats['total_uses']
            stats['avg_improvement'] = (
                stats['total_improvement'] / stats['successes'] 
                if stats['successes'] > 0 else 0
            )
        
        # Performance trends
        trends = await self.analytics_engine.calculate_performance_trends(records)
        
        return {
            'summary': {
                'total_compilations': total_compilations,
                'success_rate': f"{success_rate:.1%}",
                'avg_compilation_time': f"{avg_compilation_time:.2f}s",
                'avg_improvement_score': f"{avg_improvement_score:.1%}",
                'time_window': str(time_window)
            },
            'optimizer_performance': optimizer_stats,
            'performance_trends': trends,
            'recommendations': await self._generate_performance_recommendations(
                optimizer_stats, trends
            )
        }
```

**Implementation Requirements**:
- Implement comprehensive performance metrics collection
- Create real-time monitoring with Prometheus metrics
- Add anomaly detection and alerting system
- Build performance analytics and trend analysis

## Dev Notes

### Technical Implementation Context

**DSPy Framework Deep Integration**:
- Uses all major DSPy optimizers: MIPRO, BootstrapFewShot, COPRO, SignatureOptimizer
- Integrates with DSPy's metric system for performance evaluation
- Leverages DSPy's compilation pipeline with custom configurations
- Implements DSPy module serialization for caching

**Performance Architecture**:
- Redis-based caching for compiled modules with intelligent TTL
- Async compilation with timeout handling and resource management
- Parallel processing for multiple compilation strategies
- Connection pooling for database operations

**Database Schema Requirements**:
```sql
-- Compiled modules storage and metadata
CREATE TABLE dspy_modules (
    id UUID PRIMARY KEY,
    signature_id UUID REFERENCES dspy_signatures(id),
    module_data BYTEA NOT NULL,           -- Serialized compiled module
    optimizer_used VARCHAR(100) NOT NULL,
    optimizer_config JSONB,
    compilation_timestamp TIMESTAMP DEFAULT NOW(),
    compilation_time FLOAT,
    performance_metrics JSONB,
    validation_score FLOAT,
    cache_key VARCHAR(255) UNIQUE,
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 1.0,
    
    INDEX idx_optimizer (optimizer_used),
    INDEX idx_performance (validation_score DESC NULLS LAST),
    INDEX idx_cache_key (cache_key),
    INDEX idx_timestamp (compilation_timestamp DESC)
);

-- Compilation performance tracking
CREATE TABLE compilation_performance_logs (
    id UUID PRIMARY KEY,
    compilation_id UUID NOT NULL,
    optimizer_used VARCHAR(100),
    compilation_time FLOAT,
    example_count INTEGER,
    task_complexity VARCHAR(50),
    success BOOLEAN,
    improvement_score FLOAT,
    validation_score FLOAT,
    cache_hit BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_optimizer (optimizer_used),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_success (success)
);
```

**Error Handling Strategy**:
- Timeout handling for long-running compilations
- Graceful fallback to simpler optimizers if primary selection fails
- Comprehensive logging for debugging compilation failures
- Cache invalidation strategies for failed compilations

**Security Considerations**:
- Module serialization security to prevent code injection
- Resource limits for compilation processes to prevent DoS
- Access controls for cached modules
- Audit logging for compilation requests and results

**Testing Strategy**:
- Unit tests for optimizer selection logic
- Integration tests with actual DSPy compilation pipeline
- Performance tests ensuring compilation time requirements
- Load testing for concurrent compilation requests
- Cache effectiveness testing

## Definition of Done

**Story 1.4 is complete when:**
- ✅ Intelligent optimizer selection system chooses optimal DSPy optimizers automatically
- ✅ Module compilation completes in <30 seconds for 95% of requests
- ✅ Compiled modules consistently show 25%+ improvement over baseline
- ✅ Caching system reduces compilation time through intelligent module reuse
- ✅ Performance monitoring tracks compilation metrics and optimizer effectiveness
- ✅ Error handling provides graceful fallbacks and comprehensive logging
- ✅ All acceptance criteria validated through comprehensive testing
- ✅ Integration with DSPy framework maintains full compatibility
- ✅ Database schema supports all required operations with proper indexing
- ✅ Cache management optimizes storage and retrieval performance
- ✅ Code review completed and quality gates passed
- ✅ Documentation includes optimizer selection algorithms and caching strategies

**Ready for Story 1.5: Real-time Optimization Feedback**