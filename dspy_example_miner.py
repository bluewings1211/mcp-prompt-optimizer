#!/usr/bin/env python3
"""
DSPy Example Mining System - Task 2.1.1 Implementation
Performance-Driven Example Mining for DSPy Compilation Optimization

Implements the core DSPyExampleMiner engine for multi-source example collection,
quality assessment, and diversity optimization as specified in Story 2.1.
"""

import asyncio
import sqlite3
import logging
import json
import uuid
import hashlib
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager
from threading import RLock
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Example:
    """Core example structure for DSPy training"""
    input_text: str
    output_text: str
    task_type: str
    source: str
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    id: Optional[str] = None

@dataclass 
class ExampleWithMetrics:
    """Example enhanced with quality and performance metrics"""
    example: Example
    quality_score: float
    diversity_score: Optional[float] = None
    source: str = ""
    created_at: Optional[datetime] = None
    composite_score: Optional[float] = None

@dataclass
class QualityMetrics:
    """Detailed quality assessment metrics"""
    content_quality: float
    task_alignment: float
    output_effectiveness: float
    feedback_correlation: float
    overall_quality: float

class DSPyExampleMiner:
    """
    Core DSPy Example Mining Engine implementing Task 2.1.1 requirements.
    
    Provides multi-source example collection, quality filtering, and performance optimization
    for DSPy compilation workflows.
    """
    
    def __init__(self, db_path: str = "optimization_data.db"):
        """Initialize DSPy example mining system"""
        self.db_path = db_path
        self.min_quality_threshold = 0.8  # As specified in story requirements
        self._connection_lock = RLock()
        
        # Initialize components
        self.example_store = ExampleStore(db_path)
        self.quality_evaluator = ExampleQualityEvaluator()
        self.similarity_engine = EmbeddingSimilarityEngine()
        self.feedback_analyzer = UserFeedbackAnalyzer(db_path)
        
        # Initialize database schema
        self._init_enhanced_database()
        
        logger.info("DSPyExampleMiner initialized successfully")
    
    def _init_enhanced_database(self):
        """Initialize enhanced database schema as specified in story requirements"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Enhanced examples table for mining features
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dspy_examples (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        task_type TEXT NOT NULL,
                        input_text TEXT NOT NULL,
                        output_text TEXT NOT NULL,
                        quality_score REAL NOT NULL CHECK (quality_score >= 0 AND quality_score <= 1),
                        diversity_score REAL DEFAULT NULL,
                        source TEXT DEFAULT 'user_feedback',
                        metadata TEXT DEFAULT '{}',
                        embedding_vector TEXT,  -- JSON serialized vector for similarity
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0
                    )
                """)
                
                # Example quality metrics tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS example_quality_metrics (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        example_id TEXT REFERENCES dspy_examples(id) ON DELETE CASCADE,
                        content_quality REAL NOT NULL,
                        task_alignment REAL NOT NULL,
                        output_effectiveness REAL NOT NULL,
                        feedback_correlation REAL NOT NULL,
                        overall_quality REAL NOT NULL,
                        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # User preferences for example types
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_example_preferences (
                        user_id TEXT PRIMARY KEY,
                        complexity_preferences TEXT DEFAULT '{}',
                        domain_preferences TEXT DEFAULT '{}',
                        style_preferences TEXT DEFAULT '{}',
                        quality_thresholds TEXT DEFAULT '{}',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_type_quality ON dspy_examples(task_type, quality_score DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_desc ON dspy_examples(quality_score DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON dspy_examples(source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON dspy_examples(created_at)")
                
                conn.commit()
                logger.info("Enhanced database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing enhanced database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking"""
        with self._connection_lock:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()
    
    async def mine_examples(self, task_type: str, min_quality: float = 0.8, 
                           max_examples: int = 50) -> List[ExampleWithMetrics]:
        """
        Mine high-quality examples for specific task type
        
        Implements multi-phase example mining as specified in Task 2.1.1:
        - Phase 1: Multi-source collection
        - Phase 2: Quality assessment 
        - Phase 3: Diversity optimization
        
        Args:
            task_type: The task type to mine examples for
            min_quality: Minimum quality threshold (default 0.8 per requirements)
            max_examples: Maximum number of examples to return
            
        Returns:
            List of high-quality, diverse examples with metrics
        """
        logger.info(f"Mining examples for task_type='{task_type}' with min_quality={min_quality}")
        
        try:
            # Phase 1: Multi-source collection
            candidate_sources = await asyncio.gather(
                self._mine_from_user_feedback(task_type, min_quality),
                self._mine_from_successful_sessions(task_type, min_quality),
                self._mine_from_curated_datasets(task_type, min_quality)
            )
            
            all_candidates = []
            for source_examples in candidate_sources:
                all_candidates.extend(source_examples)
            
            logger.info(f"Collected {len(all_candidates)} candidate examples from all sources")
            
            # Phase 2: Quality assessment
            quality_examples = []
            for example in all_candidates:
                try:
                    quality_score = await self.quality_evaluator.evaluate(example)
                    if quality_score >= min_quality:
                        example_with_metrics = ExampleWithMetrics(
                            example=example,
                            quality_score=quality_score,
                            source=example.source,
                            created_at=example.created_at or datetime.now()
                        )
                        quality_examples.append(example_with_metrics)
                except Exception as e:
                    logger.warning(f"Error evaluating example quality: {e}")
                    continue
            
            logger.info(f"Filtered to {len(quality_examples)} examples meeting quality threshold")
            
            # Phase 3: Diversity optimization
            diverse_examples = await self._optimize_for_diversity(
                quality_examples, max_examples
            )
            
            # Sort by quality score (highest first)
            final_examples = sorted(diverse_examples, 
                                  key=lambda x: x.quality_score, 
                                  reverse=True)[:max_examples]
            
            logger.info(f"Selected {len(final_examples)} optimal examples for {task_type}")
            return final_examples
            
        except Exception as e:
            logger.error(f"Error in example mining: {e}")
            return []
    
    async def _mine_from_user_feedback(self, task_type: str, min_quality: float) -> List[Example]:
        """Mine examples from positive user feedback sessions"""
        logger.debug(f"Mining from user feedback for {task_type}")
        
        try:
            feedback_sessions = await self.example_store.get_feedback_sessions(
                task_type=task_type,
                min_feedback_score=0.8
            )
            
            examples = []
            for session in feedback_sessions:
                if session.get('user_feedback', 0) >= 0.8:
                    example = Example(
                        input_text=session.get('original_prompt', ''),
                        output_text=session.get('optimized_prompt', ''),
                        task_type=task_type,
                        source='user_feedback',
                        metadata={
                            'user_feedback': session.get('user_feedback'),
                            'improvement_score': session.get('performance_metrics', {}).get('improvement'),
                            'session_id': session.get('id'),
                            'confidence': session.get('confidence', 0)
                        },
                        created_at=datetime.now(),
                        id=str(uuid.uuid4())
                    )
                    examples.append(example)
            
            logger.debug(f"Found {len(examples)} examples from user feedback")
            return examples
            
        except Exception as e:
            logger.error(f"Error mining from user feedback: {e}")
            return []
    
    async def _mine_from_successful_sessions(self, task_type: str, min_quality: float) -> List[Example]:
        """Mine examples from successful optimization sessions"""
        logger.debug(f"Mining from successful sessions for {task_type}")
        
        try:
            successful_sessions = await self.example_store.get_successful_sessions(
                task_type=task_type,
                min_performance_score=0.7
            )
            
            examples = []
            for session in successful_sessions:
                example = Example(
                    input_text=session.get('original_prompt', ''),
                    output_text=session.get('optimized_result', ''),
                    task_type=task_type,
                    source='successful_sessions',
                    metadata={
                        'performance_score': session.get('performance_score'),
                        'optimization_strategy': session.get('strategy_used'),
                        'session_id': session.get('id'),
                        'processing_time': session.get('processing_time')
                    },
                    created_at=datetime.now(),
                    id=str(uuid.uuid4())
                )
                examples.append(example)
            
            logger.debug(f"Found {len(examples)} examples from successful sessions")
            return examples
            
        except Exception as e:
            logger.error(f"Error mining from successful sessions: {e}")
            return []
    
    async def _mine_from_curated_datasets(self, task_type: str, min_quality: float) -> List[Example]:
        """Mine examples from curated datasets"""
        logger.debug(f"Mining from curated datasets for {task_type}")
        
        try:
            # Use existing enhanced examples from smart_example_mining as curated dataset
            from smart_example_mining import SmartExampleMiner
            
            smart_miner = SmartExampleMiner(self.db_path)
            curated_examples = await smart_miner.get_optimal_examples(
                task_type=task_type,
                quality_threshold=min_quality,
                max_examples=20
            )
            
            examples = []
            for curated in curated_examples:
                if curated.get('composite_score', 0) >= min_quality:
                    data = curated.get('data', {})
                    example = Example(
                        input_text=str(data.get('question', data.get('context', data.get('text', '')))),
                        output_text=str(data.get('answer', data.get('output', data.get('category', '')))),
                        task_type=task_type,
                        source='curated_datasets',
                        metadata={
                            'composite_score': curated.get('composite_score'),
                            'quality_indicators': data.get('quality_indicators', []),
                            'complexity': data.get('complexity', 'medium'),
                            'usage_count': curated.get('usage_count', 0)
                        },
                        created_at=datetime.now(),
                        id=str(uuid.uuid4())
                    )
                    examples.append(example)
            
            logger.debug(f"Found {len(examples)} examples from curated datasets")
            return examples
            
        except Exception as e:
            logger.error(f"Error mining from curated datasets: {e}")
            return []
    
    async def _optimize_for_diversity(self, examples: List[ExampleWithMetrics], 
                                    target_count: int = 20) -> List[ExampleWithMetrics]:
        """Select diverse examples using max-marginal relevance"""
        if len(examples) <= target_count:
            return examples
        
        logger.debug(f"Optimizing diversity for {len(examples)} examples, target: {target_count}")
        
        try:
            # Generate embeddings for similarity calculation
            embeddings = await self._generate_embeddings([ex.example.input_text for ex in examples])
            
            # Apply max-marginal relevance selection
            selected_indices = await self._max_marginal_relevance_selection(
                embeddings=embeddings,
                quality_scores=[ex.quality_score for ex in examples],
                target_count=target_count,
                lambda_param=0.7  # Balance between quality and diversity
            )
            
            selected_examples = [examples[i] for i in selected_indices]
            
            # Calculate and validate diversity score
            diversity_score = await self._calculate_diversity_score(selected_examples)
            
            # Set diversity scores on examples
            for example in selected_examples:
                example.diversity_score = diversity_score
                example.composite_score = (example.quality_score * 0.7 + diversity_score * 0.3)
            
            logger.debug(f"Selected {len(selected_examples)} diverse examples with diversity score: {diversity_score:.3f}")
            
            # If diversity is too low, use clustering-based fallback
            if diversity_score < 0.7:
                logger.info("Diversity score below target, applying clustering-based selection")
                selected_examples = await self._cluster_based_selection(
                    examples, target_count, embeddings
                )
            
            return selected_examples
            
        except Exception as e:
            logger.error(f"Error in diversity optimization: {e}")
            # Return top examples by quality as fallback
            return sorted(examples, key=lambda x: x.quality_score, reverse=True)[:target_count]
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text similarity calculation"""
        try:
            # Use sentence transformers for high-quality embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            return embeddings
        except Exception as e:
            logger.warning(f"Error generating embeddings with SentenceTransformer: {e}")
            # Fallback to TF-IDF
            try:
                vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
                embeddings = vectorizer.fit_transform(texts).toarray()
                return embeddings
            except Exception as e2:
                logger.error(f"Error with TF-IDF fallback: {e2}")
                # Return random embeddings as last resort
                return np.random.random((len(texts), 384))
    
    async def _max_marginal_relevance_selection(self, embeddings: np.ndarray,
                                              quality_scores: List[float],
                                              target_count: int,
                                              lambda_param: float = 0.7) -> List[int]:
        """Select examples balancing quality and diversity using MMR algorithm"""
        
        selected_indices = []
        remaining_indices = list(range(len(embeddings)))
        
        # Start with highest quality example
        best_quality_idx = np.argmax(quality_scores)
        selected_indices.append(best_quality_idx)
        remaining_indices.remove(best_quality_idx)
        
        # Iteratively select examples balancing quality and diversity
        while len(selected_indices) < target_count and remaining_indices:
            mmr_scores = []
            
            for idx in remaining_indices:
                # Quality component
                quality_component = quality_scores[idx]
                
                # Diversity component (minimum similarity to selected examples)
                similarities = [
                    cosine_similarity([embeddings[idx]], [embeddings[sel_idx]])[0][0]
                    for sel_idx in selected_indices
                ]
                diversity_component = 1.0 - max(similarities)
                
                # Max-marginal relevance score
                mmr_score = (lambda_param * quality_component + 
                           (1 - lambda_param) * diversity_component)
                mmr_scores.append(mmr_score)
            
            # Select example with highest MMR score
            if mmr_scores:
                best_mmr_idx = remaining_indices[np.argmax(mmr_scores)]
                selected_indices.append(best_mmr_idx)
                remaining_indices.remove(best_mmr_idx)
            else:
                break
        
        return selected_indices
    
    async def _calculate_diversity_score(self, examples: List[ExampleWithMetrics]) -> float:
        """Calculate overall diversity score for selected examples"""
        if len(examples) < 2:
            return 1.0
        
        try:
            # Generate embeddings for selected examples
            texts = [ex.example.input_text for ex in examples]
            embeddings = await self._generate_embeddings(texts)
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(embeddings)
            
            # Calculate average pairwise similarity (excluding diagonal)
            total_similarity = 0
            pair_count = 0
            
            for i in range(len(similarities)):
                for j in range(i + 1, len(similarities)):
                    total_similarity += similarities[i][j]
                    pair_count += 1
            
            avg_similarity = total_similarity / pair_count if pair_count > 0 else 0
            
            # Diversity score is inverse of similarity
            diversity_score = 1.0 - avg_similarity
            
            return max(0.0, min(1.0, diversity_score))
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {e}")
            return 0.7  # Default moderate diversity
    
    async def _cluster_based_selection(self, examples: List[ExampleWithMetrics], 
                                     target_count: int, embeddings: np.ndarray) -> List[ExampleWithMetrics]:
        """Fallback clustering-based selection for diversity"""
        try:
            from sklearn.cluster import KMeans
            
            # Use k-means clustering to group similar examples
            n_clusters = min(target_count, len(examples))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Select the highest quality example from each cluster
            selected = []
            for cluster_id in range(n_clusters):
                cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                if cluster_indices:
                    # Get the highest quality example from this cluster
                    best_in_cluster = max(cluster_indices, key=lambda i: examples[i].quality_score)
                    selected.append(examples[best_in_cluster])
            
            return selected
            
        except Exception as e:
            logger.error(f"Error in clustering-based selection: {e}")
            # Final fallback: return top examples by quality
            return sorted(examples, key=lambda x: x.quality_score, reverse=True)[:target_count]


class ExampleStore:
    """Data store for example retrieval from various sources"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection_lock = RLock()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking"""
        with self._connection_lock:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                conn.row_factory = sqlite3.Row
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()
    
    async def get_feedback_sessions(self, task_type: str, min_feedback_score: float) -> List[Dict]:
        """Get user feedback sessions for task type"""
        try:
            sessions = []
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First, try to get from dspy_examples table (our stored examples)
                cursor.execute("""
                    SELECT id, input_text, output_text, quality_score, metadata, source
                    FROM dspy_examples 
                    WHERE task_type = ? AND source = 'user_feedback'
                    ORDER BY quality_score DESC
                    LIMIT 10
                """, (task_type,))
                
                for row in cursor.fetchall():
                    try:
                        metadata = json.loads(row[4]) if row[4] else {}
                        user_feedback = metadata.get('user_feedback', row[3])  # Use quality_score as fallback
                        
                        if user_feedback >= min_feedback_score:
                            sessions.append({
                                'id': row[0],
                                'task_type': task_type,
                                'user_feedback': user_feedback,
                                'confidence': metadata.get('confidence', 0.8),
                                'processing_time': metadata.get('processing_time', 100),
                                'original_prompt': row[1],  # input_text
                                'optimized_prompt': row[2],  # output_text
                                'performance_metrics': {'improvement': metadata.get('improvement_score', 0.3)}
                            })
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error parsing metadata for example {row[0]}: {e}")
                        continue
                
                # Fallback to strategy_performance_logs if no dspy_examples found
                if not sessions:
                    cursor.execute("""
                        SELECT DISTINCT 
                            session_id as id,
                            strategy_used as task_type,
                            user_feedback,
                            confidence_score as confidence,
                            processing_time
                        FROM strategy_performance_logs
                        WHERE strategy_used = ? AND user_feedback >= ?
                        ORDER BY user_feedback DESC
                        LIMIT 5
                    """, (task_type, min_feedback_score))
                    
                    for row in cursor.fetchall():
                        sessions.append({
                            'id': row['id'],
                            'task_type': row['task_type'],
                            'user_feedback': row['user_feedback'],
                            'confidence': row['confidence'],
                            'processing_time': row['processing_time'],
                            'original_prompt': f"Example task for {task_type}",  # Placeholder
                            'optimized_prompt': f"Optimized {task_type} task output",  # Placeholder
                            'performance_metrics': {'improvement': 0.3}
                        })
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error getting feedback sessions: {e}")
            return []
    
    async def get_successful_sessions(self, task_type: str, min_performance_score: float) -> List[Dict]:
        """Get successful optimization sessions"""
        try:
            sessions = []
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First, try to get from dspy_examples table (our stored examples)
                cursor.execute("""
                    SELECT id, input_text, output_text, quality_score, metadata, source
                    FROM dspy_examples 
                    WHERE task_type = ? AND source IN ('successful_sessions', 'curated_datasets')
                    ORDER BY quality_score DESC
                    LIMIT 10
                """, (task_type,))
                
                for row in cursor.fetchall():
                    try:
                        metadata = json.loads(row[4]) if row[4] else {}
                        performance_score = metadata.get('performance_score', row[3])  # Use quality_score as fallback
                        
                        if performance_score >= min_performance_score:
                            sessions.append({
                                'id': row[0],
                                'task_type': task_type,
                                'performance_score': performance_score,
                                'strategy_used': task_type,
                                'processing_time': metadata.get('processing_time', 100),
                                'original_prompt': row[1],  # input_text
                                'optimized_result': row[2]  # output_text
                            })
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error parsing metadata for successful session {row[0]}: {e}")
                        continue
                
                # Fallback to performance_metrics if no dspy_examples found
                if not sessions:
                    cursor.execute("""
                        SELECT DISTINCT
                            session_id as id,
                            operation_type as task_type,
                            duration_ms as processing_time,
                            success
                        FROM performance_metrics 
                        WHERE operation_type LIKE ? AND success = 1 AND duration_ms < 10000
                        ORDER BY duration_ms ASC
                        LIMIT 5
                    """, (f"%{task_type}%",))
                    
                    for row in cursor.fetchall():
                        sessions.append({
                            'id': row['id'],
                            'task_type': task_type,
                            'performance_score': 0.8,  # Derived from successful completion
                            'strategy_used': task_type,
                            'processing_time': row['processing_time'],
                            'original_prompt': f"Input for {task_type} task",  # Placeholder
                            'optimized_result': f"Successful {task_type} optimization result"  # Placeholder
                        })
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error getting successful sessions: {e}")
            return []


class ExampleQualityEvaluator:
    """Comprehensive quality evaluation for training examples"""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.content_analyzer = ContentAnalyzer()
        self.performance_predictor = PerformancePredictor()
    
    async def evaluate(self, example: Example) -> float:
        """Comprehensive quality evaluation for training examples"""
        try:
            # Multi-factor quality assessment
            factors = await asyncio.gather(
                self._evaluate_content_quality(example),
                self._evaluate_task_alignment(example),
                self._evaluate_output_effectiveness(example),
                self._evaluate_user_feedback_correlation(example),
                return_exceptions=True
            )
            
            # Handle any exceptions in factor calculation
            valid_factors = []
            for i, factor in enumerate(factors):
                if isinstance(factor, Exception):
                    logger.warning(f"Error in quality factor {i}: {factor}")
                    valid_factors.append(0.5)  # Default moderate score
                else:
                    valid_factors.append(factor)
            
            content_quality, task_alignment, output_effectiveness, feedback_correlation = valid_factors
            
            # Weighted quality score calculation
            quality_score = (
                content_quality * 0.3 +
                task_alignment * 0.25 +
                output_effectiveness * 0.3 +
                feedback_correlation * 0.15
            )
            
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error in quality evaluation: {e}")
            return 0.5  # Default moderate quality
    
    async def _evaluate_content_quality(self, example: Example) -> float:
        """Evaluate input-output content quality"""
        try:
            metrics = {
                'clarity': await self.content_analyzer.assess_clarity(example.input_text),
                'completeness': await self.content_analyzer.assess_completeness(example),
                'relevance': await self.content_analyzer.assess_relevance(example),
                'complexity': await self.content_analyzer.assess_complexity(example.input_text)
            }
            
            # Quality threshold checks
            if metrics['clarity'] < 0.6 or metrics['completeness'] < 0.7:
                return 0.0
            
            return sum(metrics.values()) / len(metrics)
            
        except Exception as e:
            logger.error(f"Error evaluating content quality: {e}")
            return 0.6
    
    async def _evaluate_task_alignment(self, example: Example) -> float:
        """Evaluate alignment with task type requirements"""
        try:
            task_requirements = await self._get_task_requirements(example.task_type)
            
            alignment_score = 0.0
            total_weight = 0.0
            
            for requirement in task_requirements:
                if await self._check_requirement_satisfaction(example, requirement):
                    alignment_score += requirement['weight']
                total_weight += requirement['weight']
            
            return alignment_score / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error evaluating task alignment: {e}")
            return 0.7
    
    async def _evaluate_output_effectiveness(self, example: Example) -> float:
        """Evaluate effectiveness of the example output"""
        try:
            # Assess output quality based on various factors
            output_text = example.output_text
            
            if not output_text or len(output_text.strip()) < 10:
                return 0.2
            
            effectiveness_score = 0.6  # Base score
            
            # Length appropriateness
            if 50 <= len(output_text) <= 500:
                effectiveness_score += 0.1
            elif len(output_text) > 500:
                effectiveness_score += 0.05
            
            # Structure and clarity indicators
            if any(indicator in output_text.lower() for indicator in 
                   ['step', 'first', 'second', 'because', 'therefore', 'however']):
                effectiveness_score += 0.1
            
            # Domain-specific effectiveness
            task_type = example.task_type
            if task_type == 'reasoning' and 'because' in output_text.lower():
                effectiveness_score += 0.1
            elif task_type == 'classification' and any(word in output_text.lower() 
                                                     for word in ['category', 'classify', 'type']):
                effectiveness_score += 0.1
            elif task_type == 'generation' and len(output_text) > 100:
                effectiveness_score += 0.1
            
            return min(1.0, effectiveness_score)
            
        except Exception as e:
            logger.error(f"Error evaluating output effectiveness: {e}")
            return 0.6
    
    async def _evaluate_user_feedback_correlation(self, example: Example) -> float:
        """Evaluate correlation with historical user feedback"""
        try:
            # Check metadata for user feedback indicators
            metadata = example.metadata
            
            if 'user_feedback' in metadata:
                feedback_score = metadata.get('user_feedback', 0)
                if feedback_score >= 0.8:
                    return 0.9
                elif feedback_score >= 0.6:
                    return 0.7
                else:
                    return 0.4
            
            # Check for quality indicators in metadata
            if 'quality_indicators' in metadata:
                indicators = metadata.get('quality_indicators', [])
                return min(0.6 + len(indicators) * 0.1, 1.0)
            
            # Default moderate correlation
            return 0.6
            
        except Exception as e:
            logger.error(f"Error evaluating feedback correlation: {e}")
            return 0.6
    
    async def _get_task_requirements(self, task_type: str) -> List[Dict]:
        """Get requirements for specific task type"""
        requirements = {
            'reasoning': [
                {'requirement': 'step_by_step', 'weight': 0.4},
                {'requirement': 'logical_flow', 'weight': 0.3},
                {'requirement': 'clear_conclusion', 'weight': 0.3}
            ],
            'classification': [
                {'requirement': 'clear_categories', 'weight': 0.5},
                {'requirement': 'confidence_scores', 'weight': 0.3},
                {'requirement': 'decision_criteria', 'weight': 0.2}
            ],
            'generation': [
                {'requirement': 'creative_content', 'weight': 0.4},
                {'requirement': 'appropriate_length', 'weight': 0.3},
                {'requirement': 'coherent_structure', 'weight': 0.3}
            ],
            'analysis': [
                {'requirement': 'data_insights', 'weight': 0.4},
                {'requirement': 'actionable_recommendations', 'weight': 0.3},
                {'requirement': 'evidence_based', 'weight': 0.3}
            ],
            'optimization': [
                {'requirement': 'improvement_areas', 'weight': 0.4},
                {'requirement': 'specific_suggestions', 'weight': 0.3},
                {'requirement': 'measurable_outcomes', 'weight': 0.3}
            ]
        }
        return requirements.get(task_type, [{'requirement': 'general_quality', 'weight': 1.0}])
    
    async def _check_requirement_satisfaction(self, example: Example, requirement: Dict) -> bool:
        """Check if example satisfies specific requirement"""
        req_type = requirement['requirement']
        input_text = example.input_text.lower()
        output_text = example.output_text.lower()
        
        if req_type == 'step_by_step':
            return 'step' in output_text or 'first' in output_text or 'then' in output_text
        elif req_type == 'logical_flow':
            return any(word in output_text for word in ['because', 'therefore', 'thus', 'hence'])
        elif req_type == 'clear_categories':
            return any(word in output_text for word in ['category', 'type', 'class', 'group'])
        elif req_type == 'confidence_scores':
            return 'confidence' in output_text or any(char.isdigit() for char in output_text)
        elif req_type == 'creative_content':
            return len(output_text) > 50 and any(word in output_text 
                                               for word in ['creative', 'innovative', 'unique'])
        elif req_type == 'data_insights':
            return any(word in output_text for word in ['insight', 'trend', 'pattern', 'finding'])
        elif req_type == 'improvement_areas':
            return any(word in output_text for word in ['improve', 'enhance', 'optimize', 'better'])
        else:
            return True  # Default to true for unknown requirements


class EmbeddingSimilarityEngine:
    """Engine for embedding-based similarity calculations"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized SentenceTransformer model")
        except Exception as e:
            logger.warning(f"Could not initialize SentenceTransformer: {e}")
            self.model = None
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        try:
            if self.model:
                embeddings = self.model.encode([text1, text2])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            else:
                # Fallback to simple word overlap
                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())
                if not words1 or not words2:
                    return 0.0
                return len(words1.intersection(words2)) / len(words1.union(words2))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0


class UserFeedbackAnalyzer:
    """Analyzer for user feedback patterns"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def analyze_feedback_patterns(self, user_id: str = None) -> Dict[str, Any]:
        """Analyze user feedback patterns"""
        # Placeholder implementation
        return {
            'avg_feedback_score': 0.8,
            'common_preferences': ['clear_explanations', 'step_by_step'],
            'improvement_areas': ['specificity', 'examples']
        }


# Helper classes for quality evaluation
class MetricsCalculator:
    """Calculator for various quality metrics"""
    
    async def calculate_metrics(self, example: Example) -> Dict[str, float]:
        """Calculate comprehensive metrics for example"""
        return {
            'length_score': min(len(example.input_text) / 100, 1.0),
            'complexity_score': len([w for w in example.input_text.split() if len(w) > 8]) / len(example.input_text.split()) if example.input_text else 0,
            'coherence_score': 0.8  # Placeholder
        }


class ContentAnalyzer:
    """Analyzer for content quality assessment"""
    
    async def assess_clarity(self, text: str) -> float:
        """Assess clarity of text content"""
        if not text:
            return 0.0
        
        # Simple clarity assessment based on sentence structure and word complexity
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Optimal sentence length for clarity
        if 10 <= avg_sentence_length <= 20:
            clarity_score = 0.9
        elif 5 <= avg_sentence_length <= 30:
            clarity_score = 0.7
        else:
            clarity_score = 0.5
        
        # Adjust for complex words
        words = text.split()
        complex_words = [w for w in words if len(w) > 10]
        if len(complex_words) / len(words) > 0.3:
            clarity_score -= 0.2
        
        return max(0.0, min(1.0, clarity_score))
    
    async def assess_completeness(self, example: Example) -> float:
        """Assess completeness of example"""
        score = 0.5  # Base score
        
        # Check if both input and output are present and substantial
        if example.input_text and len(example.input_text.strip()) > 20:
            score += 0.2
        if example.output_text and len(example.output_text.strip()) > 20:
            score += 0.2
        
        # Check for metadata completeness
        if example.metadata and len(example.metadata) > 2:
            score += 0.1
        
        return min(1.0, score)
    
    async def assess_relevance(self, example: Example) -> float:
        """Assess relevance of example to task type"""
        task_keywords = {
            'reasoning': ['why', 'because', 'explain', 'reason', 'logic'],
            'classification': ['classify', 'category', 'type', 'label', 'group'],
            'generation': ['create', 'generate', 'write', 'produce', 'make'],
            'analysis': ['analyze', 'examine', 'evaluate', 'assess', 'study'],
            'optimization': ['improve', 'optimize', 'enhance', 'better', 'refine']
        }
        
        keywords = task_keywords.get(example.task_type, [])
        text = (example.input_text + ' ' + example.output_text).lower()
        
        matches = sum(1 for keyword in keywords if keyword in text)
        relevance = min(0.5 + (matches * 0.1), 1.0)
        
        return relevance
    
    async def assess_complexity(self, text: str) -> float:
        """Assess complexity of text content"""
        if not text:
            return 0.0
        
        words = text.split()
        sentences = text.split('.')
        
        # Calculate various complexity indicators
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        unique_words = len(set(words)) / len(words) if words else 0
        
        # Normalize complexity score
        complexity = (
            min(avg_word_length / 10, 1.0) * 0.3 +
            min(avg_sentence_length / 25, 1.0) * 0.4 +
            unique_words * 0.3
        )
        
        return min(1.0, complexity)


class PerformancePredictor:
    """Predictor for example performance in training"""
    
    async def predict_performance(self, example: Example) -> float:
        """Predict how well this example will perform in training"""
        # Simplified performance prediction based on example characteristics
        base_score = 0.6
        
        # Length factor
        input_length = len(example.input_text) if example.input_text else 0
        output_length = len(example.output_text) if example.output_text else 0
        
        if 50 <= input_length <= 300 and 50 <= output_length <= 500:
            base_score += 0.2
        
        # Metadata quality factor
        if example.metadata and len(example.metadata) > 0:
            base_score += 0.1
        
        # Source reliability factor
        if example.source == 'curated_datasets':
            base_score += 0.1
        elif example.source == 'user_feedback':
            feedback_score = example.metadata.get('user_feedback', 0) if example.metadata else 0
            if feedback_score > 0.8:
                base_score += 0.1
        
        return min(1.0, base_score)


# Export main classes
__all__ = [
    'DSPyExampleMiner',
    'Example',
    'ExampleWithMetrics',
    'QualityMetrics',
    'ExampleStore',
    'ExampleQualityEvaluator',
    'EmbeddingSimilarityEngine',
    'UserFeedbackAnalyzer'
]


if __name__ == "__main__":
    # Test the DSPy example mining system
    async def test_example_mining():
        """Test the DSPy example mining functionality"""
        print("DSPy Example Mining System Test")
        print("=" * 50)
        
        # Initialize the miner
        miner = DSPyExampleMiner()
        
        # Test mining for different task types
        task_types = ['reasoning', 'classification', 'generation', 'analysis', 'optimization']
        
        for task_type in task_types:
            print(f"\nMining examples for {task_type}:")
            
            examples = await miner.mine_examples(
                task_type=task_type,
                min_quality=0.8,
                max_examples=5
            )
            
            print(f"Found {len(examples)} high-quality examples")
            
            for i, example in enumerate(examples[:2], 1):
                print(f"  Example {i}:")
                print(f"    Quality: {example.quality_score:.3f}")
                print(f"    Source: {example.source}")
                print(f"    Input: {example.example.input_text[:50]}...")
                print(f"    Output: {example.example.output_text[:50]}...")
        
        print("\nExample mining test completed!")
    
    # Run test if executed directly
    asyncio.run(test_example_mining())