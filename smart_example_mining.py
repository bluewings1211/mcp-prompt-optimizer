#!/usr/bin/env python3
"""
Smart Example Mining System for DSPy Optimization
Implements Task 1.2.3 requirements for intelligent example selection.
"""

import asyncio
import sqlite3
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import hashlib
import math
from collections import defaultdict
from contextlib import contextmanager
import threading
import queue
from threading import RLock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExampleMetadata:
    """Metadata for training examples"""
    example_id: str
    task_type: str
    quality_score: float
    performance_prediction: float
    complexity_score: float
    diversity_features: Dict[str, float]
    usage_count: int
    success_rate: float
    created_at: datetime
    last_used: Optional[datetime] = None


@dataclass
class ExampleQualityMetrics:
    """Quality assessment metrics for examples"""
    clarity_score: float
    completeness_score: float
    relevance_score: float
    uniqueness_score: float
    effectiveness_score: float
    composite_score: float


class SmartExampleMiner:
    """
    Smart example mining system with quality assessment and diversity analysis.
    Implements Task 1.2.3 requirements with thread-safe database operations.
    """
    
    def __init__(self, db_path: str = "optimization_data.db"):
        """Initialize the smart example mining system with connection pooling"""
        self.db_path = db_path
        self.quality_assessor = ExampleQualityAssessor()
        self.diversity_analyzer = ExampleDiversityAnalyzer()
        self.performance_predictor = PerformancePredictor()
        
        # Import connection pool from performance_optimization
        try:
            from performance_optimization import DatabaseConnectionPool
            self.db_pool = DatabaseConnectionPool(db_path, max_connections=3)
        except ImportError:
            logger.warning("DatabaseConnectionPool not available, falling back to basic connections")
            self.db_pool = None
            self._connection_lock = RLock()
        # Enhanced example repository with quality-scored examples
        self.enhanced_examples = {
            'reasoning': [
                {
                    "question": "Why do objects fall at the same rate in a vacuum?",
                    "reasoning": "In a vacuum, there's no air resistance to affect different objects differently. Gravity pulls on all objects with the same acceleration regardless of their mass, as described by Newton's law of universal gravitation and his second law of motion.",
                    "answer": "All objects fall at the same rate in a vacuum due to uniform gravitational acceleration",
                    "quality_indicators": ["clear_explanation", "scientific_accuracy", "logical_flow"],
                    "complexity": "medium"
                },
                {
                    "question": "How does compound interest work?",
                    "reasoning": "Compound interest means earning interest not just on your original principal, but also on previously earned interest. This creates exponential growth because each period's interest becomes part of the base for calculating the next period's interest.",
                    "answer": "Compound interest grows exponentially by earning interest on both principal and accumulated interest",
                    "quality_indicators": ["mathematical_accuracy", "practical_example", "clear_definition"],
                    "complexity": "medium"
                }
            ],
            'classification': [
                {
                    "text": "Excellent product quality, fast shipping, great customer service. Highly recommend!",
                    "category": "positive",
                    "confidence": "0.95",
                    "reasoning": "Multiple positive indicators: 'excellent', 'great', 'highly recommend' with no negative aspects mentioned",
                    "quality_indicators": ["clear_sentiment", "multiple_factors", "high_confidence"],
                    "complexity": "low"
                },
                {
                    "text": "Product arrived damaged, customer service was unhelpful, refund process took weeks",
                    "category": "negative", 
                    "confidence": "0.92",
                    "reasoning": "Clear negative experiences across multiple touchpoints: product quality, service, and process efficiency",
                    "quality_indicators": ["specific_issues", "multiple_problems", "clear_classification"],
                    "complexity": "low"
                }
            ],
            'generation': [
                {
                    "context": "Technology blog post about AI ethics",
                    "requirements": "Engaging, 800 words, accessible to general audience, balanced perspective",
                    "output": "AI Ethics: Navigating the Promise and Perils of Artificial Intelligence\n\nAs artificial intelligence reshapes our world at breakneck speed, we find ourselves at a critical crossroads...",
                    "quality_indicators": ["engaging_opening", "clear_structure", "balanced_tone", "appropriate_length"],
                    "complexity": "high"
                },
                {
                    "context": "Marketing email for productivity software",
                    "requirements": "Professional, persuasive, clear call-to-action, under 200 words",
                    "output": "Transform Your Workflow with SmartTask Pro\n\nStop losing hours to disorganized projects and missed deadlines...",
                    "quality_indicators": ["clear_value_proposition", "persuasive_language", "strong_cta", "concise"],
                    "complexity": "medium"
                }
            ],
            'analysis': [
                {
                    "data": "Q3 sales data showing 18% growth in premium segment, 5% decline in budget segment",
                    "criteria": "Market positioning and revenue optimization",
                    "insights": "Premium segment growth indicates successful brand positioning and willingness to pay for quality. Budget segment decline suggests market saturation or competitive pressure.",
                    "recommendations": "Focus marketing spend on premium segment expansion while investigating budget segment challenges through customer feedback analysis",
                    "quality_indicators": ["data_driven", "actionable_insights", "strategic_thinking"],
                    "complexity": "high"
                }
            ],
            'optimization': [
                {
                    "original_prompt": "Write about machine learning",
                    "context": "Educational blog post",
                    "optimized_prompt": "Create an accessible 1000-word educational blog post explaining machine learning fundamentals to beginners, including real-world examples, key concepts (supervised/unsupervised learning), and practical applications they encounter daily. Use conversational tone with clear headings and bullet points for readability.",
                    "improvement_areas": ["specificity", "audience_targeting", "structure", "length_guidance"],
                    "quality_indicators": ["specific_requirements", "clear_audience", "structural_guidance"],
                    "complexity": "medium"
                }
            ]
        }
        
        self._init_database()
        logger.info("SmartExampleMiner initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        if self.db_pool:
            with self.db_pool.get_connection() as conn:
                yield conn
        else:
            # Fallback to direct connection with lock
            with self._connection_lock:
                conn = None
                try:
                    conn = sqlite3.connect(
                        self.db_path, 
                        check_same_thread=False,
                        timeout=30.0
                    )
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
    
    def _init_database(self):
        """Initialize database tables for example management with connection pooling"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create example_repository table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS example_repository (
                        id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        example_data TEXT NOT NULL,
                        quality_score REAL DEFAULT 0.0,
                        performance_prediction REAL DEFAULT 0.0,
                        complexity_score REAL DEFAULT 0.0,
                        diversity_features TEXT,
                        usage_count INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP
                    )
                """)
                
                # Create example_quality_metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS example_quality_metrics (
                        example_id TEXT PRIMARY KEY,
                        clarity_score REAL,
                        completeness_score REAL,
                        relevance_score REAL,
                        uniqueness_score REAL,
                        effectiveness_score REAL,
                        composite_score REAL,
                        assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (example_id) REFERENCES example_repository (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_examples_task_type 
                    ON example_repository(task_type)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_examples_quality 
                    ON example_repository(quality_score)
                """)
                
                conn.commit()
            
            # Populate with enhanced examples if table is empty
            self._populate_initial_examples()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _populate_initial_examples(self):
        """Populate database with enhanced examples if empty with connection pooling"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM example_repository")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    logger.info("Populating database with enhanced examples...")
                    
                    for task_type, examples in self.enhanced_examples.items():
                        for example in examples:
                            example_id = str(uuid.uuid4())
                            
                            # Calculate quality score based on indicators
                            quality_score = self._calculate_initial_quality_score(example)
                            
                            cursor.execute("""
                                INSERT INTO example_repository 
                                (id, task_type, example_data, quality_score, complexity_score)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                example_id,
                                task_type,
                                json.dumps(example),
                                quality_score,
                                self._get_complexity_score(example.get('complexity', 'medium'))
                            ))
                    
                    conn.commit()
                    logger.info(f"Populated database with {sum(len(examples) for examples in self.enhanced_examples.values())} examples")
        
        except Exception as e:
            logger.error(f"Error populating initial examples: {e}")
            # Don't raise - continue without initial examples
    
    def _calculate_initial_quality_score(self, example: Dict) -> float:
        """Calculate initial quality score for an example"""
        indicators = example.get('quality_indicators', [])
        base_score = 0.7
        
        # Bonus for each quality indicator
        score = base_score + (len(indicators) * 0.05)
        
        # Complexity bonus
        complexity = example.get('complexity', 'medium')
        if complexity == 'high':
            score += 0.1
        elif complexity == 'low':
            score += 0.05
        
        return min(score, 1.0)
    
    def _get_complexity_score(self, complexity: str) -> float:
        """Convert complexity string to numeric score"""
        mapping = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        return mapping.get(complexity, 0.6)
    
    async def get_optimal_examples(self, task_type: str, quality_threshold: float = 0.8,
                                  diversity_target: float = 0.7, max_examples: int = 20) -> List[Dict]:
        """
        Mine optimal training examples for DSPy compilation
        
        Args:
            task_type: Type of task to get examples for
            quality_threshold: Minimum quality score required
            diversity_target: Target diversity score (0-1)
            max_examples: Maximum number of examples to return
            
        Returns:
            List of optimal examples with metadata
        """
        logger.info(f"Mining optimal examples for {task_type} with quality >= {quality_threshold}")
        
        try:
            # Get candidate examples from multiple sources
            candidates = await self._get_candidate_examples(task_type, quality_threshold)
            
            if not candidates:
                logger.warning(f"No examples found for {task_type} with quality >= {quality_threshold}")
                return []
            
            # Score examples for optimization potential
            scored_examples = []
            for candidate in candidates:
                try:
                    quality_metrics = await self.quality_assessor.assess_quality(candidate)
                    performance_prediction = await self.performance_predictor.predict_performance(
                        candidate, task_type
                    )
                    
                    # Calculate composite score
                    composite_score = (
                        quality_metrics.composite_score * 0.6 +
                        performance_prediction * 0.4
                    )
                    
                    scored_examples.append({
                        **candidate,
                        'quality_metrics': quality_metrics,
                        'predicted_performance': performance_prediction,
                        'composite_score': composite_score
                    })
                    
                except Exception as e:
                    logger.warning(f"Error scoring example: {e}")
                    continue
            
            # Select diverse, high-quality examples
            optimal_examples = self._select_diverse_examples(
                scored_examples, diversity_target, max_examples
            )
            
            # Update usage statistics
            await self._update_example_usage(optimal_examples)
            
            logger.info(f"Selected {len(optimal_examples)} optimal examples for {task_type}")
            return optimal_examples
            
        except Exception as e:
            logger.error(f"Error in optimal example mining: {e}")
            return []
    
    async def _get_candidate_examples(self, task_type: str, quality_threshold: float) -> List[Dict]:
        """Get candidate examples from database and repository with connection pooling"""
        candidates = []
        
        try:
            # Get from database with connection pooling
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, example_data, quality_score, usage_count, success_rate, last_used
                    FROM example_repository
                    WHERE task_type = ? AND quality_score >= ?
                    ORDER BY quality_score DESC, success_rate DESC
                """, (task_type, quality_threshold))
                
                db_examples = cursor.fetchall()
                
                for row in db_examples:
                    try:
                        example_data = json.loads(row[1])
                        candidates.append({
                            'id': row[0],
                            'source': 'database',
                            'data': example_data,
                            'quality_score': row[2],
                            'usage_count': row[3] or 0,
                            'success_rate': row[4] or 0.0,
                            'last_used': row[5]
                        })
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in example {row[0]}")
                        continue
            
            # Get from enhanced repository as fallback
            if task_type in self.enhanced_examples:
                for i, example in enumerate(self.enhanced_examples[task_type]):
                    quality_score = self._calculate_initial_quality_score(example)
                    if quality_score >= quality_threshold:
                        candidates.append({
                            'id': f"{task_type}_{i}",
                            'source': 'repository',
                            'data': example,
                            'quality_score': quality_score,
                            'usage_count': 0,
                            'success_rate': 0.0,
                            'last_used': None
                        })
            
        except Exception as e:
            logger.error(f"Error getting candidate examples: {e}")
        
        return candidates
    
    def _select_diverse_examples(self, scored_examples: List[Dict], 
                                diversity_target: float, max_examples: int) -> List[Dict]:
        """Select diverse examples using maximal marginal relevance"""
        
        if len(scored_examples) <= max_examples:
            return scored_examples
        
        # Sort by composite score
        sorted_examples = sorted(scored_examples, key=lambda x: x['composite_score'], reverse=True)
        
        # Use MMR algorithm for diversity selection
        selected = [sorted_examples[0]]  # Start with highest scoring
        remaining = sorted_examples[1:]
        
        while len(selected) < max_examples and remaining:
            mmr_scores = []
            
            for candidate in remaining:
                # Calculate similarity to already selected examples
                similarities = []
                for selected_example in selected:
                    similarity = self.diversity_analyzer.calculate_similarity(
                        candidate, selected_example
                    )
                    similarities.append(similarity)
                
                max_similarity = max(similarities) if similarities else 0
                
                # MMR score: balance relevance and diversity
                mmr_score = (0.7 * candidate['composite_score'] - 
                           0.3 * max_similarity)
                mmr_scores.append((mmr_score, candidate))
            
            # Select candidate with highest MMR score
            if mmr_scores:
                best_candidate = max(mmr_scores, key=lambda x: x[0])[1]
                selected.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break
        
        return selected
    
    async def _update_example_usage(self, examples: List[Dict]):
        """Update usage statistics for selected examples with connection pooling"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for example in examples:
                    if example.get('source') == 'database':
                        cursor.execute("""
                            UPDATE example_repository 
                            SET usage_count = usage_count + 1, last_used = ?
                            WHERE id = ?
                        """, (datetime.now().isoformat(), example['id']))
                
                conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating example usage: {e}")


class ExampleQualityAssessor:
    """Assess quality of training examples"""
    
    def __init__(self):
        self.quality_criteria = {
            'clarity': 0.25,
            'completeness': 0.25,
            'relevance': 0.20,
            'uniqueness': 0.15,
            'effectiveness': 0.15
        }
    
    async def assess_quality(self, example: Dict) -> ExampleQualityMetrics:
        """
        Assess the quality of a training example
        
        Args:
            example: Example data with metadata
            
        Returns:
            ExampleQualityMetrics with detailed scores
        """
        try:
            data = example['data']
            
            # Calculate individual quality scores
            clarity_score = self._assess_clarity(data)
            completeness_score = self._assess_completeness(data)
            relevance_score = self._assess_relevance(data)
            uniqueness_score = self._assess_uniqueness(data, example.get('usage_count', 0))
            effectiveness_score = self._assess_effectiveness(data, example.get('success_rate', 0.0))
            
            # Calculate composite score
            composite_score = (
                clarity_score * self.quality_criteria['clarity'] +
                completeness_score * self.quality_criteria['completeness'] +
                relevance_score * self.quality_criteria['relevance'] +
                uniqueness_score * self.quality_criteria['uniqueness'] +
                effectiveness_score * self.quality_criteria['effectiveness']
            )
            
            return ExampleQualityMetrics(
                clarity_score=clarity_score,
                completeness_score=completeness_score,
                relevance_score=relevance_score,
                uniqueness_score=uniqueness_score,
                effectiveness_score=effectiveness_score,
                composite_score=composite_score
            )
            
        except Exception as e:
            logger.error(f"Error assessing example quality: {e}")
            # Return default scores
            return ExampleQualityMetrics(
                clarity_score=0.5,
                completeness_score=0.5,
                relevance_score=0.5,
                uniqueness_score=0.5,
                effectiveness_score=0.5,
                composite_score=0.5
            )
    
    def _assess_clarity(self, example_data: Dict) -> float:
        """Assess clarity of the example"""
        score = 0.6  # Base score
        
        # Check for clear structure
        if isinstance(example_data, dict):
            if len(example_data.keys()) >= 2:  # Has multiple fields
                score += 0.1
            
            # Check for explanatory text
            text_fields = [v for v in example_data.values() if isinstance(v, str)]
            avg_length = sum(len(text) for text in text_fields) / len(text_fields) if text_fields else 0
            
            if avg_length > 50:  # Reasonable explanation length
                score += 0.2
            if avg_length > 100:  # Detailed explanation
                score += 0.1
        
        return min(score, 1.0)
    
    def _assess_completeness(self, example_data: Dict) -> float:
        """Assess completeness of the example"""
        score = 0.5  # Base score
        
        # Count required fields present
        required_fields = ['input', 'output', 'context', 'question', 'answer', 'reasoning']
        present_fields = sum(1 for field in required_fields if field in str(example_data).lower())
        
        score += min(present_fields * 0.1, 0.4)
        
        # Check for quality indicators
        if 'quality_indicators' in example_data:
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_relevance(self, example_data: Dict) -> float:
        """Assess relevance of the example"""
        score = 0.7  # Base score (assume relevant unless evidence suggests otherwise)
        
        # Check for specific, actionable content
        text_content = str(example_data).lower()
        
        if any(word in text_content for word in ['specific', 'example', 'detailed', 'clear']):
            score += 0.1
        
        if any(word in text_content for word in ['vague', 'unclear', 'generic']):
            score -= 0.2
        
        return max(min(score, 1.0), 0.0)
    
    def _assess_uniqueness(self, example_data: Dict, usage_count: int) -> float:
        """Assess uniqueness/novelty of the example"""
        base_score = 0.8
        
        # Reduce score based on usage frequency
        if usage_count > 10:
            base_score -= 0.2
        elif usage_count > 5:
            base_score -= 0.1
        
        # Check for unique characteristics
        text_content = str(example_data)
        if len(set(text_content.split())) / len(text_content.split()) > 0.8:  # High word diversity
            base_score += 0.1
        
        return max(min(base_score, 1.0), 0.0)
    
    def _assess_effectiveness(self, example_data: Dict, success_rate: float) -> float:
        """Assess historical effectiveness of the example"""
        if success_rate > 0:
            return success_rate
        
        # Estimate effectiveness based on content quality
        base_score = 0.6
        
        # Look for effectiveness indicators
        if 'quality_indicators' in example_data:
            indicators = example_data['quality_indicators']
            base_score += min(len(indicators) * 0.05, 0.3)
        
        return min(base_score, 1.0)


class ExampleDiversityAnalyzer:
    """Analyze diversity between examples"""
    
    def __init__(self):
        pass
    
    def calculate_similarity(self, example1: Dict, example2: Dict) -> float:
        """
        Calculate similarity between two examples
        
        Args:
            example1: First example
            example2: Second example
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            data1 = example1['data']
            data2 = example2['data']
            
            # Text-based similarity
            text1 = self._extract_text_content(data1)
            text2 = self._extract_text_content(data2)
            
            text_similarity = self._calculate_text_similarity(text1, text2)
            
            # Structure similarity
            structure_similarity = self._calculate_structure_similarity(data1, data2)
            
            # Weighted combination
            overall_similarity = 0.7 * text_similarity + 0.3 * structure_similarity
            
            return overall_similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.5  # Default moderate similarity
    
    def _extract_text_content(self, data: Dict) -> str:
        """Extract all text content from example data"""
        text_parts = []
        
        def extract_strings(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_strings(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)
        
        extract_strings(data)
        return " ".join(text_parts).lower()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Jaccard similarity
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_structure_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate structural similarity between examples"""
        if not isinstance(data1, dict) or not isinstance(data2, dict):
            return 0.0
        
        keys1 = set(data1.keys())
        keys2 = set(data2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        # Structure similarity based on common keys
        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)
        
        return len(intersection) / len(union) if union else 0.0


class PerformancePredictor:
    """Predict performance of examples for optimization tasks"""
    
    def __init__(self):
        # Historical performance weights based on content characteristics
        self.performance_weights = {
            'length': 0.15,
            'complexity': 0.25,
            'specificity': 0.30,
            'structure': 0.20,
            'novelty': 0.10
        }
    
    async def predict_performance(self, example: Dict, task_type: str) -> float:
        """
        Predict performance of an example for a specific task type
        
        Args:
            example: Example data with metadata
            task_type: Type of task the example will be used for
            
        Returns:
            Predicted performance score (0.0 to 1.0)
        """
        try:
            data = example['data']
            
            # Calculate performance factors
            length_score = self._assess_length_factor(data)
            complexity_score = self._assess_complexity_factor(data, task_type)
            specificity_score = self._assess_specificity_factor(data)
            structure_score = self._assess_structure_factor(data)
            novelty_score = self._assess_novelty_factor(example)
            
            # Weighted combination
            predicted_performance = (
                length_score * self.performance_weights['length'] +
                complexity_score * self.performance_weights['complexity'] +
                specificity_score * self.performance_weights['specificity'] +
                structure_score * self.performance_weights['structure'] +
                novelty_score * self.performance_weights['novelty']
            )
            
            # Task-specific adjustments
            predicted_performance = self._apply_task_specific_adjustments(
                predicted_performance, task_type, data
            )
            
            return max(min(predicted_performance, 1.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error predicting performance: {e}")
            return 0.6  # Default moderate performance
    
    def _assess_length_factor(self, data: Dict) -> float:
        """Assess length appropriateness"""
        text_content = str(data)
        length = len(text_content)
        
        # Optimal length range: 100-500 characters
        if 100 <= length <= 500:
            return 0.9
        elif 50 <= length <= 100 or 500 <= length <= 1000:
            return 0.7
        elif length < 50:
            return 0.4
        else:
            return 0.5
    
    def _assess_complexity_factor(self, data: Dict, task_type: str) -> float:
        """Assess complexity appropriateness for task type"""
        complexity_indicators = sum(1 for word in str(data).lower().split() 
                                  if len(word) > 8)  # Long words indicate complexity
        total_words = len(str(data).split())
        
        if total_words == 0:
            return 0.0
        
        complexity_ratio = complexity_indicators / total_words
        
        # Task-specific complexity preferences
        if task_type in ['reasoning', 'analysis']:
            # Higher complexity preferred
            return min(0.4 + complexity_ratio * 1.2, 1.0)
        elif task_type in ['classification', 'generation']:
            # Moderate complexity preferred
            return max(0.8 - abs(complexity_ratio - 0.3) * 2, 0.2)
        else:
            return 0.6
    
    def _assess_specificity_factor(self, data: Dict) -> float:
        """Assess specificity of the example"""
        text_content = str(data).lower()
        
        # Specificity indicators
        specific_words = ['specific', 'exactly', 'precisely', 'detailed', 'particular']
        vague_words = ['something', 'somehow', 'maybe', 'perhaps', 'general']
        
        specific_count = sum(1 for word in specific_words if word in text_content)
        vague_count = sum(1 for word in vague_words if word in text_content)
        
        base_score = 0.6
        base_score += specific_count * 0.1
        base_score -= vague_count * 0.15
        
        return max(min(base_score, 1.0), 0.0)
    
    def _assess_structure_factor(self, data: Dict) -> float:
        """Assess structural quality of the example"""
        if not isinstance(data, dict):
            return 0.3
        
        base_score = 0.5
        
        # Well-structured examples have multiple relevant fields
        field_count = len(data.keys())
        if field_count >= 3:
            base_score += 0.3
        elif field_count >= 2:
            base_score += 0.2
        
        # Check for logical field relationships
        common_pairs = [
            ('question', 'answer'),
            ('input', 'output'),
            ('context', 'response'),
            ('problem', 'solution')
        ]
        
        data_keys_lower = [k.lower() for k in data.keys()]
        for pair in common_pairs:
            if pair[0] in data_keys_lower and pair[1] in data_keys_lower:
                base_score += 0.1
                break
        
        return min(base_score, 1.0)
    
    def _assess_novelty_factor(self, example: Dict) -> float:
        """Assess novelty based on usage patterns"""
        usage_count = example.get('usage_count', 0)
        
        # Newer examples get higher novelty scores
        base_score = 0.8
        
        if usage_count > 20:
            base_score = 0.3
        elif usage_count > 10:
            base_score = 0.5
        elif usage_count > 5:
            base_score = 0.7
        
        return base_score
    
    def _apply_task_specific_adjustments(self, base_score: float, task_type: str, data: Dict) -> float:
        """Apply task-specific performance adjustments"""
        adjustment = 0.0
        text_content = str(data).lower()
        
        if task_type == 'reasoning':
            if 'because' in text_content or 'therefore' in text_content:
                adjustment += 0.1
            if 'step' in text_content:
                adjustment += 0.05
        
        elif task_type == 'classification':
            if 'category' in text_content or 'confidence' in text_content:
                adjustment += 0.1
        
        elif task_type == 'generation':
            if 'create' in text_content or 'generate' in text_content:
                adjustment += 0.05
            if 'requirements' in text_content:
                adjustment += 0.1
        
        elif task_type == 'analysis':
            if 'insights' in text_content or 'recommendations' in text_content:
                adjustment += 0.1
        
        return base_score + adjustment


# Export main classes
__all__ = [
    'SmartExampleMiner',
    'ExampleQualityAssessor',
    'ExampleDiversityAnalyzer',
    'PerformancePredictor',
    'ExampleMetadata',
    'ExampleQualityMetrics'
]


if __name__ == "__main__":
    # Test the smart example mining system
    async def test_mining():
        """Test the example mining functionality"""
        miner = SmartExampleMiner()
        
        print("Smart Example Mining Test Results:")
        print("=" * 50)
        
        # Test for each task type
        task_types = ['reasoning', 'classification', 'generation', 'analysis', 'optimization']
        
        for task_type in task_types:
            print(f"\nMining examples for {task_type}:")
            examples = await miner.get_optimal_examples(
                task_type=task_type,
                quality_threshold=0.6,
                max_examples=3
            )
            
            print(f"Found {len(examples)} optimal examples")
            for i, example in enumerate(examples[:2], 1):  # Show first 2
                print(f"  Example {i}: Quality={example.get('quality_score', 0):.2f}, "
                      f"Composite={example.get('composite_score', 0):.2f}")
    
    # Run test if executed directly
    asyncio.run(test_mining())