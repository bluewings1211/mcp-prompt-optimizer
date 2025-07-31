# Story 1.3: Performance-Driven Example Mining

## Status
[Approved]

## User Story
**As a** technical prompt engineer  
**I want** the system to automatically find and use the best training examples  
**So that** my DSPy modules are trained on high-quality, relevant data  

## Business Value
- **Primary Value**: Ensures DSPy modules achieve maximum optimization effectiveness
- **User Impact**: Improves optimization results by 15-25% through better training data
- **Success Metric**: Example quality scores >0.8 with diversity index >0.7

## Acceptance Criteria

### AC1: Automatic High-Quality Example Discovery
- **GIVEN** the system has access to historical usage data and feedback  
- **WHEN** compiling a DSPy module for a specific task type  
- **THEN** it automatically mines examples with quality scores >0.8  
- **AND** prioritizes examples that led to positive user feedback (>0.8 satisfaction)  
- **AND** sources examples from multiple data streams (user feedback, curated sets, successful sessions)  

### AC2: Example Diversity and Relevance Optimization
- **GIVEN** a set of high-quality candidate examples  
- **WHEN** selecting final training examples for DSPy compilation  
- **THEN** ensures example diversity using embedding similarity with diversity score >0.7  
- **AND** balances diversity with relevance to specific task type  
- **AND** optimizes example set size based on compilation performance requirements  

### AC3: Continuous Example Set Improvement
- **GIVEN** new successful optimization sessions occur  
- **WHEN** users provide positive feedback on optimization results  
- **THEN** automatically adds successful examples to the training pool  
- **AND** updates example quality scores based on performance outcomes  
- **AND** removes or demotes examples that consistently lead to poor results  

## Detailed Tasks

### Task 1.3.1: Implement Core Example Mining Engine
**Acceptance Criteria Reference**: AC1, AC3  
**Estimated Hours**: 16  

```python
class DSPyExampleMiner:
    def __init__(self):
        self.example_repository = ExampleRepository()
        self.quality_evaluator = ExampleQualityEvaluator()
        self.similarity_engine = EmbeddingSimilarityEngine()
        self.feedback_processor = FeedbackProcessor()
        self.performance_analyzer = PerformanceAnalyzer()
    
    async def mine_examples(self, task_type: str, min_quality: float = 0.8, 
                           max_examples: int = 50) -> List[ExampleWithMetrics]:
        """Mine high-quality examples for specific task type"""
        
        # Phase 1: Multi-source example collection
        example_sources = await asyncio.gather(
            self._mine_from_user_feedback(task_type, min_quality),
            self._mine_from_successful_sessions(task_type, min_quality),
            self._mine_from_curated_datasets(task_type, min_quality),
            self._mine_from_domain_templates(task_type, min_quality)
        )
        
        # Combine and deduplicate examples
        all_candidates = []
        for source_examples in example_sources:
            all_candidates.extend(source_examples)
        
        deduplicated_candidates = self._deduplicate_examples(all_candidates)
        
        # Phase 2: Quality assessment and scoring
        quality_scored_examples = []
        for example in deduplicated_candidates:
            quality_metrics = await self.quality_evaluator.comprehensive_evaluation(example)
            
            if quality_metrics.overall_score >= min_quality:
                enhanced_example = ExampleWithMetrics(
                    input_text=example['input'],
                    output_text=example['output'],
                    task_type=task_type,
                    quality_score=quality_metrics.overall_score,
                    relevance_score=quality_metrics.relevance_score,
                    clarity_score=quality_metrics.clarity_score,
                    effectiveness_score=quality_metrics.effectiveness_score,
                    user_feedback_score=example.get('user_feedback', 0.0),
                    source=example['source'],
                    metadata=example.get('metadata', {}),
                    performance_history=await self._get_performance_history(example)
                )
                quality_scored_examples.append(enhanced_example)
        
        # Phase 3: Performance-based ranking
        performance_ranked = await self._rank_by_performance_potential(
            quality_scored_examples, task_type
        )
        
        # Phase 4: Diversity optimization
        final_examples = self._optimize_for_diversity(
            performance_ranked, max_examples, target_diversity=0.7
        )
        
        # Phase 5: Continuous learning integration
        await self._update_example_performance_tracking(final_examples, task_type)
        
        return final_examples
    
    async def _mine_from_user_feedback(self, task_type: str, min_quality: float) -> List[Dict]:
        """Mine examples from user feedback sessions with high satisfaction scores"""
        
        high_satisfaction_sessions = await self.example_repository.get_sessions_by_criteria(
            task_type=task_type,
            user_satisfaction_threshold=0.8,
            improvement_threshold=0.2,
            time_window=timedelta(days=90)
        )
        
        feedback_examples = []
        for session in high_satisfaction_sessions:
            if session.user_feedback >= 0.8:
                example = {
                    'input': session.original_prompt,
                    'output': session.optimized_prompt,
                    'quality_indicator': session.user_feedback,
                    'performance_data': session.performance_metrics,
                    'source': 'user_feedback',
                    'metadata': {
                        'session_id': session.id,
                        'improvement_score': session.improvement_score,
                        'strategy_used': session.strategy_used,
                        'timestamp': session.created_at
                    }
                }
                feedback_examples.append(example)
        
        return feedback_examples
    
    async def _mine_from_successful_sessions(self, task_type: str, min_quality: float) -> List[Dict]:
        """Mine examples from optimization sessions with high performance metrics"""
        
        successful_sessions = await self.example_repository.get_high_performance_sessions(
            task_type=task_type,
            min_improvement_score=0.3,
            min_confidence_score=0.8,
            time_window=timedelta(days=60)
        )
        
        session_examples = []
        for session in successful_sessions:
            # Extract successful patterns from session
            example = {
                'input': session.original_prompt,
                'output': session.optimized_prompt,
                'quality_indicator': session.confidence_score,
                'performance_data': session.performance_metrics,
                'source': 'successful_session',
                'metadata': {
                    'session_id': session.id,
                    'improvement_score': session.improvement_score,
                    'processing_time': session.processing_time,
                    'strategy_effectiveness': session.strategy_effectiveness
                }
            }
            session_examples.append(example)
        
        return session_examples
```

**Implementation Requirements**:
- Implement multi-source example mining with comprehensive quality assessment
- Create performance-based ranking system for example selection
- Add metadata tracking for continuous improvement
- Build deduplication algorithm to handle overlapping examples from different sources

### Task 1.3.2: Build Advanced Quality Assessment System
**Acceptance Criteria Reference**: AC1, AC2  
**Estimated Hours**: 12  

```python
class ExampleQualityEvaluator:
    def __init__(self):
        self.language_model = self._initialize_quality_assessment_model()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.quality_metrics = QualityMetricsCalculator()
        self.domain_analyzer = DomainSpecificAnalyzer()
    
    async def comprehensive_evaluation(self, example: Dict) -> QualityMetrics:
        """Perform comprehensive quality evaluation of training example"""
        
        input_text = example['input']
        output_text = example['output']
        
        # Multi-dimensional quality assessment
        quality_dimensions = await asyncio.gather(
            self._assess_clarity_and_coherence(input_text, output_text),
            self._assess_task_relevance(input_text, output_text, example.get('task_type')),
            self._assess_output_quality(output_text, input_text),
            self._assess_learning_potential(example),
            self._assess_diversity_value(example),
            self._assess_domain_specificity(example)
        )
        
        clarity_score, relevance_score, output_quality, learning_potential, diversity_value, domain_score = quality_dimensions
        
        # Weighted composite score calculation
        composite_score = (
            clarity_score * 0.25 +
            relevance_score * 0.20 +
            output_quality * 0.20 +
            learning_potential * 0.15 +
            diversity_value * 0.10 +
            domain_score * 0.10
        )
        
        return QualityMetrics(
            overall_score=composite_score,
            clarity_score=clarity_score,
            relevance_score=relevance_score,
            output_quality_score=output_quality,
            learning_potential_score=learning_potential,
            diversity_value_score=diversity_value,
            domain_specificity_score=domain_score,
            assessment_confidence=self._calculate_assessment_confidence(quality_dimensions)
        )
    
    async def _assess_clarity_and_coherence(self, input_text: str, output_text: str) -> float:
        """Assess clarity and coherence of example input-output pair"""
        
        # Use language model to assess clarity
        clarity_prompt = f"""
        Assess the clarity and coherence of this input-output pair on a scale of 0-1:
        
        Input: {input_text}
        Output: {output_text}
        
        Consider:
        - Is the input clear and unambiguous?
        - Is the output coherent and well-structured?
        - Is the relationship between input and output logical?
        
        Return only a numeric score between 0 and 1.
        """
        
        with dspy.context(lm=self.language_model):
            clarity_assessment = dspy.Predict("assessment_prompt -> clarity_score")(
                assessment_prompt=clarity_prompt
            )
        
        try:
            return float(clarity_assessment.clarity_score)
        except (ValueError, AttributeError):
            # Fallback to heuristic assessment
            return self._heuristic_clarity_assessment(input_text, output_text)
    
    async def _assess_task_relevance(self, input_text: str, output_text: str, task_type: str) -> float:
        """Assess how relevant the example is to the specified task type"""
        
        if not task_type:
            return 0.5  # Neutral score if task type unknown
        
        # Embedding-based similarity to task type exemplars
        task_exemplars = await self._get_task_type_exemplars(task_type)
        
        example_embedding = self.embedding_model.encode(f"{input_text} -> {output_text}")
        
        relevance_scores = []
        for exemplar in task_exemplars:
            exemplar_embedding = self.embedding_model.encode(exemplar)
            similarity = cosine_similarity([example_embedding], [exemplar_embedding])[0][0]
            relevance_scores.append(similarity)
        
        return np.mean(relevance_scores) if relevance_scores else 0.5
    
    async def _assess_learning_potential(self, example: Dict) -> float:
        """Assess how much learning potential this example provides"""
        
        # Factors that indicate high learning potential:
        # 1. Demonstrates effective techniques
        # 2. Shows clear improvement patterns
        # 3. Has successful performance history
        # 4. Represents diverse problem-solving approaches
        
        learning_indicators = {
            'performance_history': self._score_performance_history(example),
            'technique_demonstration': self._score_technique_demonstration(example),
            'improvement_clarity': self._score_improvement_clarity(example),
            'pattern_diversity': self._score_pattern_diversity(example)
        }
        
        # Weighted average of learning indicators
        learning_potential = (
            learning_indicators['performance_history'] * 0.3 +
            learning_indicators['technique_demonstration'] * 0.3 +
            learning_indicators['improvement_clarity'] * 0.2 +
            learning_indicators['pattern_diversity'] * 0.2
        )
        
        return learning_potential
```

**Implementation Requirements**:
- Implement multi-dimensional quality assessment using language models
- Create embedding-based relevance scoring system
- Add domain-specific quality metrics
- Build learning potential assessment based on performance history

### Task 1.3.3: Implement Diversity Optimization Algorithm
**Acceptance Criteria Reference**: AC2  
**Estimated Hours**: 10  

```python
class ExampleDiversityOptimizer:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.clustering_algorithm = KMeansClusterer()
        self.similarity_calculator = SimilarityCalculator()
    
    def optimize_for_diversity(self, examples: List[ExampleWithMetrics], 
                              max_examples: int, target_diversity: float = 0.7) -> List[ExampleWithMetrics]:
        """Optimize example selection for maximum diversity while maintaining quality"""
        
        if len(examples) <= max_examples:
            return examples
        
        # Phase 1: Embedding generation
        example_embeddings = self._generate_embeddings(examples)
        
        # Phase 2: Diversity-aware selection using multiple algorithms
        selection_strategies = {
            'mmr': self._maximal_marginal_relevance_selection,
            'clustering': self._cluster_based_selection,
            'greedy_diversity': self._greedy_diversity_selection
        }
        
        # Try multiple strategies and select best diversity outcome
        best_selection = None
        best_diversity_score = 0
        
        for strategy_name, strategy_func in selection_strategies.items():
            candidate_selection = strategy_func(
                examples, example_embeddings, max_examples
            )
            
            diversity_score = self._calculate_diversity_score(candidate_selection)
            
            if diversity_score > best_diversity_score and diversity_score >= target_diversity:
                best_selection = candidate_selection
                best_diversity_score = diversity_score
        
        # Fallback to highest quality examples if diversity target not met
        if best_selection is None or best_diversity_score < target_diversity:
            best_selection = self._quality_based_fallback_selection(examples, max_examples)
        
        return best_selection
    
    def _maximal_marginal_relevance_selection(self, examples: List[ExampleWithMetrics], 
                                            embeddings: np.ndarray, max_examples: int) -> List[ExampleWithMetrics]:
        """Select examples using Maximal Marginal Relevance algorithm"""
        
        selected_examples = []
        selected_embeddings = []
        remaining_indices = list(range(len(examples)))
        
        # Start with highest quality example
        best_quality_idx = np.argmax([ex.quality_score for ex in examples])
        selected_examples.append(examples[best_quality_idx])
        selected_embeddings.append(embeddings[best_quality_idx])
        remaining_indices.remove(best_quality_idx)
        
        # Iteratively select examples balancing quality and diversity
        while len(selected_examples) < max_examples and remaining_indices:
            mmr_scores = []
            
            for idx in remaining_indices:
                candidate = examples[idx]
                candidate_embedding = embeddings[idx]
                
                # Calculate relevance (quality score)
                relevance = candidate.quality_score
                
                # Calculate maximum similarity to already selected examples
                if selected_embeddings:
                    similarities = [
                        cosine_similarity([candidate_embedding], [sel_emb])[0][0]
                        for sel_emb in selected_embeddings
                    ]
                    max_similarity = max(similarities)
                else:
                    max_similarity = 0
                
                # MMR score: balance relevance and diversity
                mmr_score = 0.7 * relevance - 0.3 * max_similarity
                mmr_scores.append((mmr_score, idx))
            
            # Select candidate with highest MMR score
            best_mmr_score, best_idx = max(mmr_scores, key=lambda x: x[0])
            selected_examples.append(examples[best_idx])
            selected_embeddings.append(embeddings[best_idx])
            remaining_indices.remove(best_idx)
        
        return selected_examples
    
    def _cluster_based_selection(self, examples: List[ExampleWithMetrics], 
                               embeddings: np.ndarray, max_examples: int) -> List[ExampleWithMetrics]:
        """Select examples using clustering to ensure diversity across example space"""
        
        # Determine optimal number of clusters
        n_clusters = min(max_examples, max(2, len(examples) // 3))
        
        # Cluster examples based on embeddings
        cluster_labels = self.clustering_algorithm.fit_predict(embeddings, n_clusters=n_clusters)
        
        # Select best examples from each cluster
        selected_examples = []
        cluster_selections = defaultdict(list)
        
        # Group examples by cluster
        for idx, cluster_id in enumerate(cluster_labels):
            cluster_selections[cluster_id].append((examples[idx], idx))
        
        # Select from each cluster proportionally
        examples_per_cluster = max_examples // n_clusters
        remaining_selections = max_examples % n_clusters
        
        for cluster_id, cluster_examples in cluster_selections.items():
            # Sort cluster examples by quality
            cluster_examples.sort(key=lambda x: x[0].quality_score, reverse=True)
            
            # Select top examples from this cluster
            n_from_cluster = examples_per_cluster
            if remaining_selections > 0:
                n_from_cluster += 1
                remaining_selections -= 1
            
            selected_from_cluster = cluster_examples[:n_from_cluster]
            selected_examples.extend([ex[0] for ex in selected_from_cluster])
        
        return selected_examples[:max_examples]
    
    def _calculate_diversity_score(self, examples: List[ExampleWithMetrics]) -> float:
        """Calculate overall diversity score for a set of examples"""
        
        if len(examples) < 2:
            return 1.0
        
        # Generate embeddings for diversity calculation
        embeddings = self._generate_embeddings(examples)
        
        # Calculate pairwise similarities
        pairwise_similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                pairwise_similarities.append(similarity)
        
        # Diversity score is inverse of average similarity
        average_similarity = np.mean(pairwise_similarities)
        diversity_score = 1.0 - average_similarity
        
        return max(0.0, min(1.0, diversity_score))
```

**Implementation Requirements**:
- Implement multiple diversity selection algorithms (MMR, clustering, greedy)
- Create embedding-based similarity calculation system
- Add diversity scoring and validation mechanisms
- Build fallback strategies for cases where diversity targets can't be met

### Task 1.3.4: Create Continuous Learning and Example Update System
**Acceptance Criteria Reference**: AC3  
**Estimated Hours**: 8  

```python
class ContinuousExampleLearning:
    def __init__(self):
        self.example_repository = ExampleRepository()
        self.performance_tracker = PerformanceTracker()
        self.feedback_processor = FeedbackProcessor()
        self.quality_updater = QualityUpdater()
    
    async def process_new_optimization_session(self, session: OptimizationSession):
        """Process new optimization session for example mining opportunities"""
        
        # Only process sessions with positive outcomes
        if session.user_feedback >= 0.8 and session.improvement_score >= 0.2:
            
            # Create candidate example from successful session
            candidate_example = {
                'input': session.original_prompt,
                'output': session.optimized_prompt,
                'task_type': session.task_type,
                'performance_data': session.performance_metrics,
                'user_feedback': session.user_feedback,
                'source': 'continuous_learning',
                'metadata': {
                    'session_id': session.id,
                    'strategy_used': session.strategy_used,
                    'improvement_score': session.improvement_score,
                    'confidence_score': session.confidence_score
                }
            }
            
            # Quality assessment for new example
            quality_metrics = await self.quality_evaluator.comprehensive_evaluation(candidate_example)
            
            if quality_metrics.overall_score >= 0.8:
                # Add to example repository
                await self.example_repository.add_example(
                    ExampleWithMetrics.from_session(session, quality_metrics)
                )
                
                # Update task type statistics
                await self._update_task_type_statistics(session.task_type, quality_metrics)
                
                # Trigger example set rebalancing if needed
                await self._check_and_rebalance_examples(session.task_type)
    
    async def update_example_performance_scores(self):
        """Periodically update example performance scores based on usage outcomes"""
        
        # Get examples used in recent optimizations
        recent_example_usage = await self.performance_tracker.get_recent_example_usage(
            time_window=timedelta(days=30)
        )
        
        for example_id, usage_data in recent_example_usage.items():
            # Calculate new performance score based on outcomes
            performance_metrics = {
                'usage_count': len(usage_data),
                'average_improvement': np.mean([u['improvement_score'] for u in usage_data]),
                'average_user_satisfaction': np.mean([u['user_feedback'] for u in usage_data if u['user_feedback']]),
                'success_rate': len([u for u in usage_data if u['user_feedback'] >= 0.7]) / len(usage_data)
            }
            
            # Update example quality score based on performance
            new_quality_score = self._calculate_updated_quality_score(
                example_id, performance_metrics
            )
            
            await self.example_repository.update_example_quality_score(
                example_id, new_quality_score
            )
    
    async def prune_underperforming_examples(self):
        """Remove or demote examples that consistently lead to poor results"""
        
        # Identify examples with poor performance history
        underperforming_examples = await self.performance_tracker.get_underperforming_examples(
            min_usage_count=10,
            max_success_rate=0.3,
            time_window=timedelta(days=60)
        )
        
        for example_id in underperforming_examples:
            example = await self.example_repository.get_example(example_id)
            
            # Demote example quality score
            demoted_score = max(0.1, example.quality_score * 0.7)
            await self.example_repository.update_example_quality_score(
                example_id, demoted_score
            )
            
            # Archive if quality drops too low
            if demoted_score < 0.3:
                await self.example_repository.archive_example(example_id)
    
    async def _check_and_rebalance_examples(self, task_type: str):
        """Check if example set needs rebalancing for optimal diversity and quality"""
        
        current_examples = await self.example_repository.get_examples_by_task_type(task_type)
        
        if len(current_examples) > 100:  # Trigger rebalancing if too many examples
            # Re-optimize example selection
            diversity_optimizer = ExampleDiversityOptimizer()
            optimized_examples = diversity_optimizer.optimize_for_diversity(
                current_examples, max_examples=50, target_diversity=0.7
            )
            
            # Update repository with optimized selection
            await self.example_repository.update_task_type_examples(
                task_type, optimized_examples
            )
```

**Implementation Requirements**:
- Implement automatic example addition from successful optimization sessions
- Create performance-based scoring updates for existing examples
- Add example pruning and archival system for underperforming examples
- Build example set rebalancing to maintain optimal diversity and quality

## Dev Notes

### Technical Implementation Context

**DSPy Framework Integration**:
- Integrates with DSPy's example format and training pipeline
- Uses DSPy signatures for task type classification
- Leverages DSPy metrics for performance assessment
- Connects to DSPy compilation process for example validation

**Database Schema Requirements**:
```sql
-- Enhanced examples table with performance tracking
CREATE TABLE dspy_examples (
    id UUID PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    quality_score FLOAT NOT NULL CHECK (quality_score >= 0 AND quality_score <= 1),
    relevance_score FLOAT,
    clarity_score FLOAT,
    effectiveness_score FLOAT,
    diversity_value FLOAT,
    source VARCHAR(100) DEFAULT 'user_feedback',
    metadata JSONB,
    performance_history JSONB,
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_task_type_quality (task_type, quality_score DESC),
    INDEX idx_quality_desc (quality_score DESC),
    INDEX idx_source (source),
    INDEX idx_last_used (last_used DESC)
);

-- Example performance tracking
CREATE TABLE example_performance_logs (
    id UUID PRIMARY KEY,
    example_id UUID REFERENCES dspy_examples(id),
    session_id UUID REFERENCES optimization_sessions(id),
    usage_outcome VARCHAR(50), -- 'success', 'failure', 'neutral'
    improvement_contribution FLOAT,
    user_feedback_score FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_example_id (example_id),
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp DESC)
);
```

**Performance Architecture**:
- Async processing for all example mining operations
- Batch processing for quality assessment to improve efficiency
- Caching of embeddings and similarity calculations
- Parallel processing of multi-source example collection

**Machine Learning Components**:
- Sentence transformers for embedding generation
- K-means clustering for diversity optimization
- Cosine similarity for relevance assessment
- Quality assessment using language models

**Error Handling Strategy**:
- Graceful degradation when example sources are unavailable
- Fallback to baseline examples if mining fails
- Comprehensive logging for debugging quality assessment issues
- Validation of example format and content before storage

**Testing Strategy**:
- Unit tests for each quality assessment component
- Integration tests with actual DSPy compilation pipeline
- Performance tests for example mining speed and efficiency
- Quality validation tests ensuring mined examples improve optimization results

## Definition of Done

**Story 1.3 is complete when:**
- ✅ Example mining system discovers high-quality examples with >0.8 quality scores
- ✅ Diversity optimization achieves >0.7 diversity index while maintaining quality
- ✅ Continuous learning system automatically updates example repository
- ✅ Multi-source example collection integrates user feedback, sessions, and curated data
- ✅ Quality assessment system provides reliable, multi-dimensional evaluation
- ✅ Performance tracking system monitors and improves example effectiveness
- ✅ All acceptance criteria validated through comprehensive testing
- ✅ Integration with DSPy compilation pipeline successful
- ✅ Database schema supports all required operations with proper indexing
- ✅ Error handling provides graceful fallbacks and maintains system stability
- ✅ Code review completed and quality gates passed
- ✅ Documentation includes example mining algorithms and usage patterns

**Ready for Story 1.4: Intelligent Module Compilation**