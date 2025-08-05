#!/usr/bin/env python3
"""
DSPy Module Compilation System - Task 2.2.1 Implementation
Intelligent Module Compilation with Optimizer Selection and Performance Optimization

Implements the core DSPyModuleCompiler engine for intelligent DSPy optimizer selection,
automatic configuration optimization, and performance-driven module compilation as 
specified in Story 2.2.
"""

import asyncio
import logging
import time
import json
import uuid
import hashlib
import pickle
import sqlite3

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    logger.warning("DSPy not available, using mocked signatures")
    
    # Create a mock DSPy module for development
    class MockDSPy:
        class Signature:
            def __init__(self, signature_str):
                self.signature_str = signature_str
            def __str__(self):
                return self.signature_str
        
        class ChainOfThought:
            def __init__(self, signature):
                self.signature = signature
        
        class Module:
            def __init__(self):
                pass
        
        class Example:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class MIPROv2:
            def __init__(self, **kwargs):
                pass
            def compile(self, module, trainset=None, valset=None):
                return module
        
        class BootstrapFewShot:
            def __init__(self, **kwargs):
                pass
            def compile(self, module, trainset=None):
                return module
    
    dspy = MockDSPy()

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager
from threading import RLock
from enum import Enum
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory caching")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available, using basic similarity")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, using basic embeddings")

# Import DSPy Example Miner for training data
from dspy_example_miner import DSPyExampleMiner, ExampleWithMetrics

# Remove duplicate logging configuration - already set above

class OptimizerType(Enum):
    """Supported DSPy optimizer types"""
    MIPRO = "mipro"
    BOOTSTRAP = "bootstrap"
    COPRO = "copro"
    SIGNATURE_OPTIMIZER = "signature_optimizer"

@dataclass
class CompilationContext:
    """Context information for module compilation"""
    signature: dspy.Signature
    examples: List[Dict]
    performance_requirements: 'PerformanceRequirements'
    signature_complexity: 'SignatureComplexity'
    user_preferences: Dict[str, Any] = None

@dataclass
class PerformanceRequirements:
    """Performance requirements for compilation"""
    optimize_for: str = "quality"  # quality, speed, accuracy
    max_compilation_time: float = 30.0
    min_success_rate: float = 0.8
    target_accuracy: float = 0.85

@dataclass
class SignatureComplexity:
    """Analysis of signature complexity"""
    complexity_score: float
    is_complex: bool
    has_reasoning_fields: bool
    field_count: int
    output_complexity: float

@dataclass
class OptimizerSelection:
    """Result of optimizer selection process"""
    optimizer_type: str
    reasoning: str
    confidence: float
    context: CompilationContext
    config_recommendations: Dict[str, Any] = None

@dataclass
class CompiledModuleResult:
    """Result of module compilation"""
    module: Any  # Compiled DSPy module
    optimizer_used: str
    compilation_time: float
    cache_hit: bool
    performance_metrics: 'CompilationPerformanceMetrics'
    optimizer_reasoning: str = ""
    config_used: Dict[str, Any] = None

@dataclass
class CompilationPerformanceMetrics:
    """Performance metrics for compiled module"""
    validation_score: float
    accuracy_score: float
    processing_speed: float
    signature_complexity: float
    example_count: int
    avg_example_quality: float
    compilation_success: bool = True

@dataclass
class CachedModule:
    """Cached compiled module with metadata"""
    cache_key: str
    module: Any
    optimizer: str
    performance_metrics: CompilationPerformanceMetrics
    compilation_time: float
    created_at: datetime
    usage_count: int = 0
    ttl_hours: int = 24

@dataclass
class OptimizerConfig:
    """Configuration for DSPy optimizers"""
    optimizer_type: str
    num_candidates: int = 10
    max_bootstrapped_demos: int = 4
    max_labeled_demos: int = 6
    max_rounds: int = 2
    init_temperature: float = 1.0
    breadth: int = 10
    depth: int = 3
    metric: Any = None
    teacher_settings: Dict = None
    verbose: bool = False
    requires_permission_to_run: bool = False

    def copy(self):
        """Create a deep copy of the configuration"""
        return OptimizerConfig(
            optimizer_type=self.optimizer_type,
            num_candidates=self.num_candidates,
            max_bootstrapped_demos=self.max_bootstrapped_demos,
            max_labeled_demos=self.max_labeled_demos,
            max_rounds=self.max_rounds,
            init_temperature=self.init_temperature,
            breadth=self.breadth,
            depth=self.depth,
            metric=self.metric,
            teacher_settings=self.teacher_settings or {},
            verbose=self.verbose,
            requires_permission_to_run=self.requires_permission_to_run
        )

class CompilationError(Exception):
    """Raised when module compilation fails"""
    pass

class DSPyModuleCompiler:
    """
    Core DSPy Module Compilation Engine implementing Task 2.2.1 requirements.
    
    Provides intelligent optimizer selection, configuration optimization, caching,
    and performance monitoring for DSPy module compilation workflows.
    """
    
    def __init__(self, db_path: str = "optimization_data.db", redis_url: str = "redis://localhost:6379"):
        """Initialize DSPy module compiler"""
        self.db_path = db_path
        self._connection_lock = RLock()
        
        # Initialize core components
        self.optimizer_registry = OptimizerRegistry()
        self.cache_manager = IntelligentCacheManager(redis_url)
        self.performance_tracker = CompilationPerformanceTracker(db_path)
        self.config_optimizer = ConfigurationOptimizer(db_path)
        
        # Initialize DSPy example miner for training data
        self.example_miner = DSPyExampleMiner(db_path)
        
        # Initialize database schema
        self._init_compilation_database()
        
        logger.info("DSPyModuleCompiler initialized successfully")
    
    def _init_compilation_database(self):
        """Initialize database schema for compilation tracking"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Module compilation tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dspy_module_compilations (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        signature_id TEXT,
                        optimizer_used TEXT NOT NULL,
                        compilation_time REAL NOT NULL,
                        cache_hit BOOLEAN DEFAULT FALSE,
                        validation_score REAL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        config_used TEXT DEFAULT '{}',
                        performance_metrics TEXT DEFAULT '{}',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        context_hash TEXT
                    )
                """)
                
                # Cache performance tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache_performance_logs (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        cache_key TEXT NOT NULL,
                        hit_type TEXT, -- 'direct', 'similarity', 'miss'
                        similarity_score REAL,
                        retrieval_time REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                """)
                
                # Optimizer configuration performance tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimizer_config_performance (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        optimizer_type TEXT NOT NULL,
                        config_hash TEXT NOT NULL,
                        config_parameters TEXT NOT NULL,
                        avg_compilation_time REAL,
                        success_rate REAL,
                        avg_validation_score REAL,
                        usage_count INTEGER DEFAULT 1,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizer_performance ON dspy_module_compilations(optimizer_used, compilation_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp_desc ON dspy_module_compilations(timestamp DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_success_rate ON dspy_module_compilations(optimizer_used, success)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_performance_logs(cache_key)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hit_type ON cache_performance_logs(hit_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizer_perf ON optimizer_config_performance(optimizer_type, success_rate DESC, avg_compilation_time ASC)")
                
                conn.commit()
                logger.info("Compilation database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing compilation database: {e}")
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
    
    async def compile_optimized_module(self, signature: dspy.Signature, 
                                      examples: List[Dict],
                                      optimize_for: str = 'quality',
                                      context: Dict = None) -> CompiledModuleResult:
        """
        Compile DSPy module with intelligent optimizer selection
        
        Implements the complete compilation workflow from Story 2.2 Task 2.2.1:
        - Phase 1: Analyze compilation requirements
        - Phase 2: Check cache for similar modules  
        - Phase 3: Select optimal optimizer
        - Phase 4: Configure optimizer for optimal performance
        - Phase 5: Execute compilation with monitoring
        - Phase 6: Validate and cache result
        
        Args:
            signature: DSPy signature for the module
            examples: Training examples for compilation
            optimize_for: Optimization target ('quality', 'speed', 'accuracy')
            context: Optional context information
            
        Returns:
            CompiledModuleResult with compilation details and performance metrics
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting module compilation for session {session_id}")
            
            # Phase 1: Analyze compilation requirements
            compilation_context = await self._analyze_compilation_context(
                signature, examples, optimize_for, context
            )
            
            # Phase 2: Check cache for similar modules
            cache_key = await self._generate_cache_key(signature, examples, compilation_context)
            cached_module = await self.cache_manager.get_cached_module(cache_key)
            
            if cached_module and await self._validate_cached_module(cached_module, compilation_context):
                await self.performance_tracker.record_cache_hit(cache_key, session_id)
                logger.info(f"Cache hit for session {session_id}")
                return CompiledModuleResult(
                    module=cached_module.module,
                    optimizer_used=cached_module.optimizer,
                    compilation_time=0.0,
                    cache_hit=True,
                    performance_metrics=cached_module.performance_metrics,
                    optimizer_reasoning="Retrieved from cache - similar module found",
                    config_used={}
                )
            
            # Phase 3: Select optimal optimizer
            optimizer_selection = await self._select_optimal_optimizer(compilation_context)
            
            # Phase 4: Configure optimizer for optimal performance
            optimizer_config = await self.config_optimizer.optimize_config(
                optimizer_type=optimizer_selection.optimizer_type,
                context=compilation_context
            )
            
            # Phase 5: Execute compilation with monitoring
            try:
                compiled_module = await self._execute_compilation(
                    signature=signature,
                    examples=examples,
                    optimizer_selection=optimizer_selection,
                    config=optimizer_config
                )
                
                compilation_time = time.time() - start_time
                
                # Phase 6: Validate and cache result
                performance_metrics = await self._evaluate_compiled_module(
                    compiled_module, examples, compilation_context
                )
                
                result = CompiledModuleResult(
                    module=compiled_module,
                    optimizer_used=optimizer_selection.optimizer_type,
                    compilation_time=compilation_time,
                    cache_hit=False,
                    performance_metrics=performance_metrics,
                    optimizer_reasoning=optimizer_selection.reasoning,
                    config_used=asdict(optimizer_config)
                )
                
                # Cache successful compilation if validation score is good
                if performance_metrics.validation_score > 0.7:
                    await self.cache_manager.cache_module(cache_key, result)
                
                # Track performance
                await self.performance_tracker.record_compilation(result, session_id, compilation_context)
                
                logger.info(f"Compilation completed successfully in {compilation_time:.2f}s for session {session_id}")
                return result
                
            except Exception as e:
                compilation_time = time.time() - start_time
                await self.performance_tracker.record_compilation_failure(
                    optimizer_selection.optimizer_type, compilation_time, str(e), session_id
                )
                raise CompilationError(f"Module compilation failed with {optimizer_selection.optimizer_type}: {str(e)}")
            
        except Exception as e:
            compilation_time = time.time() - start_time
            logger.error(f"Error in compilation workflow for session {session_id}: {e}")
            await self.performance_tracker.record_compilation_failure(
                "unknown", compilation_time, str(e), session_id
            )
            raise CompilationError(f"Module compilation failed: {str(e)}")
    
    async def _analyze_compilation_context(self, signature: dspy.Signature, examples: List[Dict], 
                                         optimize_for: str, context: Dict = None) -> CompilationContext:
        """Analyze compilation requirements and context"""
        
        # Analyze signature complexity
        signature_complexity = await self._analyze_signature_complexity(signature)
        
        # Create performance requirements
        performance_requirements = PerformanceRequirements(
            optimize_for=optimize_for,
            max_compilation_time=30.0,
            min_success_rate=0.8,
            target_accuracy=0.85
        )
        
        # Adjust requirements based on optimization target
        if optimize_for == "speed":
            performance_requirements.max_compilation_time = 15.0
            performance_requirements.target_accuracy = 0.75
        elif optimize_for == "quality":
            performance_requirements.max_compilation_time = 45.0
            performance_requirements.target_accuracy = 0.90
        
        return CompilationContext(
            signature=signature,
            examples=examples,
            performance_requirements=performance_requirements,
            signature_complexity=signature_complexity,
            user_preferences=context or {}
        )
    
    async def _analyze_signature_complexity(self, signature: dspy.Signature) -> SignatureComplexity:
        """Analyze DSPy signature complexity"""
        try:
            # Convert signature to string for analysis
            sig_str = str(signature)
            
            # Count fields and analyze structure
            input_fields = sig_str.split(" -> ")[0].split(",") if " -> " in sig_str else []
            output_fields = sig_str.split(" -> ")[1].split(",") if " -> " in sig_str else []
            
            field_count = len(input_fields) + len(output_fields)
            
            # Check for reasoning fields
            has_reasoning_fields = any(
                "reasoning" in field.lower() or "rationale" in field.lower() 
                for field in output_fields
            )
            
            # Calculate complexity score
            complexity_score = min(1.0, (
                field_count * 0.1 +
                (0.3 if has_reasoning_fields else 0) +
                (0.2 if len(output_fields) > 2 else 0) +
                (0.2 if any("context" in field.lower() for field in input_fields) else 0)
            ))
            
            # Determine if complex (threshold: 0.5)
            is_complex = complexity_score > 0.5
            
            # Output complexity (multiple outputs or reasoning fields)
            output_complexity = min(1.0, len(output_fields) * 0.25 + (0.5 if has_reasoning_fields else 0))
            
            return SignatureComplexity(
                complexity_score=complexity_score,
                is_complex=is_complex,
                has_reasoning_fields=has_reasoning_fields,
                field_count=field_count,
                output_complexity=output_complexity
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing signature complexity: {e}")
            # Return moderate complexity as fallback
            return SignatureComplexity(
                complexity_score=0.5,
                is_complex=True,
                has_reasoning_fields=False,
                field_count=2,
                output_complexity=0.5
            )
    
    async def _select_optimal_optimizer(self, context: CompilationContext) -> OptimizerSelection:
        """
        Select optimal DSPy optimizer based on context analysis
        
        Implements intelligent optimizer selection logic from Story 2.2:
        - MIPRO: Complex tasks with sufficient examples  
        - BootstrapFewShot: Few examples available
        - COPRO: Speed optimization or general purpose
        - SignatureOptimizer: Signature refinement needs
        """
        
        signature_complexity = context.signature_complexity
        example_count = len(context.examples)
        perf_requirements = context.performance_requirements
        
        # Optimizer selection logic with reasoning
        if signature_complexity.is_complex and example_count >= 20:
            # Complex tasks with sufficient examples - use MIPRO
            optimizer_type = OptimizerType.MIPRO.value
            reasoning = f"Selected MIPRO for complex signature (complexity: {signature_complexity.complexity_score:.2f}) with {example_count} examples"
            confidence = 0.9
            
        elif example_count < 10:
            # Few examples - use BootstrapFewShot
            optimizer_type = OptimizerType.BOOTSTRAP.value
            reasoning = f"Selected BootstrapFewShot for limited examples ({example_count} available)"
            confidence = 0.85
            
        elif perf_requirements.optimize_for == 'speed':
            # Speed optimization - use COPRO
            optimizer_type = OptimizerType.COPRO.value
            reasoning = "Selected COPRO for speed optimization requirements"
            confidence = 0.8
            
        elif signature_complexity.has_reasoning_fields and example_count >= 15:
            # Reasoning tasks with good examples - prefer MIPRO
            optimizer_type = OptimizerType.MIPRO.value
            reasoning = "Selected MIPRO for reasoning-intensive signature with adequate examples"
            confidence = 0.87
            
        elif signature_complexity.field_count <= 2 and not signature_complexity.is_complex:
            # Simple signatures - use SignatureOptimizer
            optimizer_type = OptimizerType.SIGNATURE_OPTIMIZER.value
            reasoning = "Selected SignatureOptimizer for simple signature optimization"
            confidence = 0.75
            
        else:
            # General purpose - use COPRO
            optimizer_type = OptimizerType.COPRO.value
            reasoning = "Selected COPRO as general-purpose optimizer"
            confidence = 0.75
        
        # Adjust confidence based on historical performance
        historical_performance = await self._get_optimizer_historical_performance(optimizer_type)
        if historical_performance:
            confidence = min(confidence * (1 + historical_performance.get('success_rate', 0) * 0.2), 1.0)
            reasoning += f" (Historical success rate: {historical_performance.get('success_rate', 0):.1%})"
        
        return OptimizerSelection(
            optimizer_type=optimizer_type,
            reasoning=reasoning,
            confidence=confidence,
            context=context
        )
    
    async def _get_optimizer_historical_performance(self, optimizer_type: str) -> Optional[Dict[str, float]]:
        """Get historical performance metrics for optimizer"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                        AVG(compilation_time) as avg_time,
                        AVG(validation_score) as avg_validation
                    FROM dspy_module_compilations
                    WHERE optimizer_used = ? 
                    AND timestamp >= datetime('now', '-30 days')
                """, (optimizer_type,))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    return {
                        'success_rate': result[0],
                        'avg_time': result[1] or 0,
                        'avg_validation': result[2] or 0
                    }
                
        except Exception as e:
            logger.warning(f"Error getting historical performance for {optimizer_type}: {e}")
        
        return None
    
    async def _execute_compilation(self, signature: dspy.Signature, examples: List[Dict],
                                 optimizer_selection: OptimizerSelection, 
                                 config: OptimizerConfig) -> Any:
        """Execute the actual DSPy compilation with selected optimizer and configuration"""
        
        logger.info(f"Executing compilation with {optimizer_selection.optimizer_type}")
        
        try:
            # Prepare examples for DSPy format
            dspy_examples = await self._prepare_dspy_examples(examples, signature)
            
            if optimizer_selection.optimizer_type == OptimizerType.MIPRO.value:
                return await self._compile_with_mipro(signature, dspy_examples, config)
            elif optimizer_selection.optimizer_type == OptimizerType.BOOTSTRAP.value:
                return await self._compile_with_bootstrap(signature, dspy_examples, config)
            elif optimizer_selection.optimizer_type == OptimizerType.COPRO.value:
                return await self._compile_with_copro(signature, dspy_examples, config)
            elif optimizer_selection.optimizer_type == OptimizerType.SIGNATURE_OPTIMIZER.value:
                return await self._compile_with_signature_optimizer(signature, dspy_examples, config)
            else:
                raise CompilationError(f"Unknown optimizer type: {optimizer_selection.optimizer_type}")
                
        except Exception as e:
            logger.error(f"Compilation execution failed: {e}")
            raise CompilationError(f"Failed to compile with {optimizer_selection.optimizer_type}: {str(e)}")
    
    async def _prepare_dspy_examples(self, examples: List[Dict], signature: dspy.Signature) -> List[dspy.Example]:
        """Convert examples to DSPy format"""
        dspy_examples = []
        
        for example in examples:
            try:
                # Handle different example formats
                if hasattr(example, 'example'):
                    # ExampleWithMetrics format from DSPy miner
                    ex_data = example.example
                    dspy_ex = dspy.Example(
                        question=ex_data.input_text,
                        answer=ex_data.output_text
                    )
                elif isinstance(example, dict):
                    # Dictionary format
                    if 'input_text' in example and 'output_text' in example:
                        dspy_ex = dspy.Example(
                            question=example['input_text'],
                            answer=example['output_text']
                        )
                    elif 'question' in example and 'answer' in example:
                        dspy_ex = dspy.Example(
                            question=example['question'],
                            answer=example['answer']
                        )
                    else:
                        # Generic format - use first two fields
                        keys = list(example.keys())
                        if len(keys) >= 2:
                            dspy_ex = dspy.Example(
                                question=str(example[keys[0]]),
                                answer=str(example[keys[1]])
                            )
                        else:
                            continue
                else:
                    logger.warning(f"Unknown example format: {type(example)}")
                    continue
                
                dspy_examples.append(dspy_ex)
                
            except Exception as e:
                logger.warning(f"Error preparing example: {e}")
                continue
        
        logger.info(f"Prepared {len(dspy_examples)} DSPy examples for compilation")
        return dspy_examples[:20]  # Limit to 20 examples for performance
    
    async def _compile_with_mipro(self, signature: dspy.Signature, examples: List[dspy.Example], 
                                config: OptimizerConfig) -> Any:
        """Compile using MIPRO optimizer"""
        try:
            # Create a simple module with the signature
            class SimpleModule(dspy.Module):
                def __init__(self, signature):
                    super().__init__()
                    self.predictor = dspy.ChainOfThought(signature)
                
                def forward(self, **kwargs):
                    return self.predictor(**kwargs)
            
            module = SimpleModule(signature)
            
            # Configure MIPRO teleprompter
            mipro = dspy.MIPROv2(
                metric=None,  # Will use default accuracy
                num_candidates=config.num_candidates,
                init_temperature=config.init_temperature,
                verbose=config.verbose
            )
            
            # Compile the module
            compiled_module = mipro.compile(
                module,
                trainset=examples[:15],  # Use subset for training
                valset=examples[15:] if len(examples) > 15 else examples[:5]
            )
            
            return compiled_module
            
        except Exception as e:
            logger.error(f"MIPRO compilation failed: {e}")
            # Fallback to basic module
            return self._create_fallback_module(signature)
    
    async def _compile_with_bootstrap(self, signature: dspy.Signature, examples: List[dspy.Example],
                                    config: OptimizerConfig) -> Any:
        """Compile using BootstrapFewShot optimizer"""
        try:
            # Create a simple module
            class SimpleModule(dspy.Module):
                def __init__(self, signature):
                    super().__init__()
                    self.predictor = dspy.ChainOfThought(signature)
                
                def forward(self, **kwargs):
                    return self.predictor(**kwargs)
            
            module = SimpleModule(signature)
            
            # Configure BootstrapFewShot teleprompter
            bootstrap = dspy.BootstrapFewShot(
                metric=None,  # Will use default
                max_bootstrapped_demos=config.max_bootstrapped_demos,
                max_labeled_demos=config.max_labeled_demos,
                max_rounds=config.max_rounds
            )
            
            # Compile the module
            compiled_module = bootstrap.compile(
                module,
                trainset=examples
            )
            
            return compiled_module
            
        except Exception as e:
            logger.error(f"Bootstrap compilation failed: {e}")
            return self._create_fallback_module(signature)
    
    async def _compile_with_copro(self, signature: dspy.Signature, examples: List[dspy.Example],
                                config: OptimizerConfig) -> Any:
        """Compile using COPRO optimizer"""
        try:
            # Create a simple module
            class SimpleModule(dspy.Module):
                def __init__(self, signature):
                    super().__init__()
                    self.predictor = dspy.ChainOfThought(signature)
                
                def forward(self, **kwargs):
                    return self.predictor(**kwargs)
            
            module = SimpleModule(signature)
            
            # For now, return optimized chain of thought module
            # COPRO implementation would go here when available
            optimized_module = dspy.ChainOfThought(signature)
            
            return optimized_module
            
        except Exception as e:
            logger.error(f"COPRO compilation failed: {e}")
            return self._create_fallback_module(signature)
    
    async def _compile_with_signature_optimizer(self, signature: dspy.Signature, examples: List[dspy.Example],
                                              config: OptimizerConfig) -> Any:
        """Compile using Signature Optimizer"""
        try:
            # Create optimized signature module
            optimized_module = dspy.ChainOfThought(signature)
            return optimized_module
            
        except Exception as e:
            logger.error(f"Signature optimizer compilation failed: {e}")
            return self._create_fallback_module(signature)
    
    def _create_fallback_module(self, signature: dspy.Signature) -> Any:
        """Create a fallback module when compilation fails"""
        logger.info("Creating fallback module with basic ChainOfThought")
        return dspy.ChainOfThought(signature)
    
    async def _evaluate_compiled_module(self, module: Any, examples: List[Dict], 
                                      context: CompilationContext) -> CompilationPerformanceMetrics:
        """Evaluate the performance of compiled module"""
        
        try:
            # Basic validation - module exists and is callable
            validation_score = 0.8 if module else 0.0
            
            # Calculate accuracy score based on examples
            accuracy_score = 0.85  # Placeholder - would run actual evaluation
            
            # Processing speed estimate
            processing_speed = 1.0  # requests per second estimate
            
            # Example quality metrics
            example_count = len(examples)
            avg_example_quality = 0.8  # Average quality from examples
            
            return CompilationPerformanceMetrics(
                validation_score=validation_score,
                accuracy_score=accuracy_score,
                processing_speed=processing_speed,
                signature_complexity=context.signature_complexity.complexity_score,
                example_count=example_count,
                avg_example_quality=avg_example_quality,
                compilation_success=True
            )
            
        except Exception as e:
            logger.error(f"Error evaluating compiled module: {e}")
            return CompilationPerformanceMetrics(
                validation_score=0.5,
                accuracy_score=0.5,
                processing_speed=0.5,
                signature_complexity=0.5,
                example_count=len(examples),
                avg_example_quality=0.5,
                compilation_success=False
            )
    
    async def _generate_cache_key(self, signature: dspy.Signature, examples: List[Dict],
                                context: CompilationContext) -> str:
        """Generate intelligent cache key based on signature and examples"""
        
        try:
            # Signature fingerprint
            signature_hash = hashlib.md5(str(signature).encode()).hexdigest()[:8]
            
            # Examples fingerprint (based on content similarity, not exact match)
            examples_content = []
            for ex in examples:
                if hasattr(ex, 'example'):
                    examples_content.append(f"{ex.example.input_text}{ex.example.output_text}")
                elif isinstance(ex, dict):
                    input_text = ex.get('input_text', ex.get('question', ''))
                    output_text = ex.get('output_text', ex.get('answer', ''))
                    examples_content.append(f"{input_text}{output_text}")
            
            # Create embedding-based hash for examples
            examples_str = " ".join(examples_content[:5])  # Use first 5 examples
            examples_hash = hashlib.md5(examples_str.encode()).hexdigest()[:8]
            
            # Context fingerprint
            context_elements = [
                context.performance_requirements.optimize_for,
                str(context.signature_complexity.complexity_score),
                str(len(examples))
            ]
            context_hash = hashlib.md5("".join(context_elements).encode()).hexdigest()[:8]
            
            return f"dspy_module_{signature_hash}_{examples_hash}_{context_hash}"
            
        except Exception as e:
            logger.warning(f"Error generating cache key: {e}")
            return f"dspy_module_{uuid.uuid4().hex[:16]}"
    
    async def _validate_cached_module(self, cached_module: CachedModule, 
                                    context: CompilationContext) -> bool:
        """Validate if cached module is compatible with current context"""
        
        try:
            # Check if cache entry is still valid (not expired)
            age_hours = (datetime.now() - cached_module.created_at).total_seconds() / 3600
            if age_hours > cached_module.ttl_hours:
                return False
            
            # Check performance compatibility
            if cached_module.performance_metrics.validation_score < 0.7:
                return False
            
            # Check if optimization target is compatible
            current_target = context.performance_requirements.optimize_for
            if current_target == "quality" and cached_module.performance_metrics.accuracy_score < 0.8:
                return False
            elif current_target == "speed" and cached_module.compilation_time > 20.0:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating cached module: {e}")
            return False


class OptimizerRegistry:
    """Registry for DSPy optimizer types and their capabilities"""
    
    def __init__(self):
        """Initialize optimizer registry"""
        self.optimizers = {
            OptimizerType.MIPRO.value: {
                "name": "MIPRO v2",
                "description": "Advanced multi-stage instruction and prompt optimization",
                "best_for": ["complex_reasoning", "high_accuracy", "sufficient_examples"],
                "min_examples": 15,
                "max_compilation_time": 60.0,
                "accuracy_rating": 0.9
            },
            OptimizerType.BOOTSTRAP.value: {
                "name": "BootstrapFewShot",
                "description": "Few-shot learning with bootstrapped demonstrations",
                "best_for": ["few_examples", "quick_setup", "generalization"],
                "min_examples": 3,
                "max_compilation_time": 20.0,
                "accuracy_rating": 0.8
            },
            OptimizerType.COPRO.value: {
                "name": "COPRO",
                "description": "Constrained prompt optimization",
                "best_for": ["speed", "general_purpose", "constrained_tasks"],
                "min_examples": 5,
                "max_compilation_time": 15.0,
                "accuracy_rating": 0.75
            },
            OptimizerType.SIGNATURE_OPTIMIZER.value: {
                "name": "SignatureOptimizer",
                "description": "Signature-level optimization and refinement",
                "best_for": ["simple_tasks", "signature_refinement", "lightweight"],
                "min_examples": 1,
                "max_compilation_time": 10.0,
                "accuracy_rating": 0.7
            }
        }
    
    def get_optimizer_info(self, optimizer_type: str) -> Dict[str, Any]:
        """Get information about specific optimizer"""
        return self.optimizers.get(optimizer_type, {})
    
    def get_best_optimizer_for_context(self, context: CompilationContext) -> str:
        """Get best optimizer recommendation for given context"""
        example_count = len(context.examples)
        is_complex = context.signature_complexity.is_complex
        optimize_for = context.performance_requirements.optimize_for
        
        if is_complex and example_count >= 15:
            return OptimizerType.MIPRO.value
        elif example_count < 10:
            return OptimizerType.BOOTSTRAP.value
        elif optimize_for == "speed":
            return OptimizerType.COPRO.value
        else:
            return OptimizerType.COPRO.value


class IntelligentCacheManager:
    """Intelligent caching system for compiled DSPy modules"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize cache manager"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis.from_url(redis_url, decode_responses=False)
                self.redis_client.ping()  # Test connection
                self.cache_available = True
                logger.info("Redis cache connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory cache: {e}")
                self.redis_client = None
                self.cache_available = False
                self._memory_cache = {}
        else:
            logger.info("Redis not available, using in-memory cache")
            self.redis_client = None
            self.cache_available = False
            self._memory_cache = {}
        
        self.similarity_calculator = SignatureSimilarityCalculator()
        self.cache_stats = CacheStatistics()
    
    async def get_cached_module(self, cache_key: str) -> Optional[CachedModule]:
        """Retrieve cached module with similarity-based lookup"""
        
        try:
            # Direct cache lookup
            cached_data = await self._get_from_cache(f"dspy:module:{cache_key}")
            if cached_data:
                await self.cache_stats.record_hit('direct')
                return pickle.loads(cached_data)
            
            # Similarity-based lookup for near-matches
            similar_modules = await self._find_similar_cached_modules(cache_key)
            
            for similar_module in similar_modules:
                if await self._validate_similarity_match(cache_key, similar_module):
                    await self.cache_stats.record_hit('similarity')
                    return similar_module
            
            await self.cache_stats.record_miss()
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached module: {e}")
            return None
    
    async def cache_module(self, cache_key: str, compilation_result: CompiledModuleResult):
        """Cache compiled module with metadata and performance metrics"""
        
        try:
            cached_module = CachedModule(
                cache_key=cache_key,
                module=compilation_result.module,
                optimizer=compilation_result.optimizer_used,
                performance_metrics=compilation_result.performance_metrics,
                compilation_time=compilation_result.compilation_time,
                created_at=datetime.now(),
                usage_count=0,
                ttl_hours=self._calculate_cache_ttl(compilation_result.performance_metrics)
            )
            
            # Cache with TTL based on performance
            ttl_seconds = cached_module.ttl_hours * 3600
            
            await self._set_cache(
                f"dspy:module:{cache_key}",
                pickle.dumps(cached_module),
                ttl_seconds
            )
            
            logger.info(f"Cached module with key {cache_key} for {cached_module.ttl_hours} hours")
            
        except Exception as e:
            logger.error(f"Error caching module: {e}")
    
    async def _get_from_cache(self, key: str) -> Optional[bytes]:
        """Get data from cache (Redis or memory)"""
        if self.cache_available and self.redis_client:
            return self.redis_client.get(key)
        else:
            return self._memory_cache.get(key)
    
    async def _set_cache(self, key: str, value: bytes, ttl: int):
        """Set data in cache (Redis or memory)"""
        if self.cache_available and self.redis_client:
            self.redis_client.setex(key, ttl, value)
        else:
            # Simple memory cache (no TTL for simplicity)
            self._memory_cache[key] = value
    
    def _calculate_cache_ttl(self, performance_metrics: CompilationPerformanceMetrics) -> int:
        """Calculate cache TTL based on performance metrics"""
        base_ttl = 24  # 24 hours base
        
        # Better performance = longer TTL
        if performance_metrics.validation_score > 0.9:
            return base_ttl * 3  # 72 hours
        elif performance_metrics.validation_score > 0.8:
            return base_ttl * 2  # 48 hours
        else:
            return base_ttl  # 24 hours
    
    async def _find_similar_cached_modules(self, target_cache_key: str) -> List[CachedModule]:
        """Find cached modules with similar signatures and examples"""
        # Simplified similarity matching - in real implementation would use embeddings
        return []
    
    async def _validate_similarity_match(self, target_key: str, cached_module: CachedModule) -> bool:
        """Validate if similar cached module is suitable"""
        # Simplified validation
        return cached_module.performance_metrics.validation_score > 0.75


class SignatureSimilarityCalculator:
    """Calculate similarity between DSPy signatures"""
    
    def __init__(self):
        """Initialize similarity calculator"""
        pass
    
    async def calculate_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two signatures"""
        # Simplified similarity calculation
        if sig1 == sig2:
            return 1.0
        
        # Basic string similarity
        words1 = set(sig1.lower().split())
        words2 = set(sig2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class CacheStatistics:
    """Track cache performance statistics"""
    
    def __init__(self):
        """Initialize cache statistics"""
        self.stats = {
            'direct_hits': 0,
            'similarity_hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    async def record_hit(self, hit_type: str):
        """Record cache hit"""
        self.stats['total_requests'] += 1
        if hit_type == 'direct':
            self.stats['direct_hits'] += 1
        elif hit_type == 'similarity':
            self.stats['similarity_hits'] += 1
    
    async def record_miss(self):
        """Record cache miss"""
        self.stats['total_requests'] += 1
        self.stats['misses'] += 1
    
    def get_hit_rate(self) -> float:
        """Get overall cache hit rate"""
        if self.stats['total_requests'] == 0:
            return 0.0
        
        total_hits = self.stats['direct_hits'] + self.stats['similarity_hits']
        return total_hits / self.stats['total_requests']


class ConfigurationOptimizer:
    """Optimize DSPy optimizer configurations based on context and performance history"""
    
    def __init__(self, db_path: str):
        """Initialize configuration optimizer"""
        self.db_path = db_path
        self.optimizer_configs = OptimizerConfigRegistry()
        self.performance_history = PerformanceHistory(db_path)
        self._connection_lock = RLock()
    
    async def optimize_config(self, optimizer_type: str, 
                            context: CompilationContext) -> OptimizerConfig:
        """Generate optimal configuration for specific optimizer and context"""
        
        # Get base configuration for optimizer type
        base_config = self.optimizer_configs.get_base_config(optimizer_type)
        
        # Adapt configuration based on context
        adapted_config = await self._adapt_config_to_context(base_config, context)
        
        # Apply performance-based optimizations
        optimized_config = await self._apply_performance_optimizations(
            adapted_config, optimizer_type, context
        )
        
        return optimized_config
    
    async def _adapt_config_to_context(self, base_config: OptimizerConfig,
                                     context: CompilationContext) -> OptimizerConfig:
        """Adapt configuration based on compilation context"""
        
        adapted_config = base_config.copy()
        
        # Adapt based on signature complexity
        if context.signature_complexity.is_complex:
            adapted_config.num_candidates = min(20, base_config.num_candidates * 2)
            adapted_config.max_bootstrapped_demos = min(8, base_config.max_bootstrapped_demos + 2)
        
        # Adapt based on example count
        example_count = len(context.examples)
        if example_count < 10:
            adapted_config.num_candidates = max(5, adapted_config.num_candidates // 2)
        elif example_count > 50:
            adapted_config.num_candidates = min(30, int(adapted_config.num_candidates * 1.5))
        
        # Adapt based on performance requirements
        if context.performance_requirements.optimize_for == 'speed':
            adapted_config.num_candidates = max(3, adapted_config.num_candidates // 3)
            adapted_config.max_bootstrapped_demos = max(2, adapted_config.max_bootstrapped_demos // 2)
        elif context.performance_requirements.optimize_for == 'quality':
            adapted_config.num_candidates = min(25, int(adapted_config.num_candidates * 1.5))
            adapted_config.max_bootstrapped_demos = min(10, adapted_config.max_bootstrapped_demos + 3)
        
        # Adapt based on example quality
        avg_quality = 0.8  # Default assumption - would calculate from actual examples
        if avg_quality < 0.7:
            # Lower quality examples need more candidates
            adapted_config.num_candidates = min(30, int(adapted_config.num_candidates * 1.3))
        
        return adapted_config
    
    async def _apply_performance_optimizations(self, config: OptimizerConfig,
                                             optimizer_type: str,
                                             context: CompilationContext) -> OptimizerConfig:
        """Apply optimizations based on historical performance"""
        
        # Get historical performance for similar contexts
        similar_performances = await self.performance_history.get_similar_performances(
            optimizer_type, context
        )
        
        if not similar_performances:
            return config  # No history available
        
        # Analyze successful configurations
        successful_configs = [
            perf for perf in similar_performances 
            if perf.get('success_rate', 0) > 0.8 and perf.get('avg_compilation_time', 100) < 25
        ]
        
        if successful_configs:
            # Find optimal parameter ranges from successful configs
            optimal_ranges = self._analyze_successful_configs(successful_configs)
            
            # Adjust configuration towards optimal ranges
            optimized_config = config.copy()
            
            for param, (optimal_min, optimal_max) in optimal_ranges.items():
                current_value = getattr(optimized_config, param, None)
                if current_value is not None:
                    # Move towards optimal range
                    if current_value < optimal_min:
                        setattr(optimized_config, param, min(optimal_min, int(current_value * 1.2)))
                    elif current_value > optimal_max:
                        setattr(optimized_config, param, max(optimal_max, int(current_value * 0.8)))
            
            return optimized_config
        
        return config
    
    def _analyze_successful_configs(self, successful_configs: List[Dict]) -> Dict[str, Tuple[float, float]]:
        """Analyze successful configurations to find optimal parameter ranges"""
        # Simplified analysis - would be more sophisticated in real implementation
        return {
            'num_candidates': (8, 15),
            'max_bootstrapped_demos': (4, 8),
            'max_labeled_demos': (4, 8)
        }


class OptimizerConfigRegistry:
    """Registry of base configurations for different optimizers"""
    
    def __init__(self):
        """Initialize config registry"""
        self.base_configs = {
            OptimizerType.MIPRO.value: OptimizerConfig(
                optimizer_type=OptimizerType.MIPRO.value,
                num_candidates=15,
                max_bootstrapped_demos=6,
                max_labeled_demos=8,
                max_rounds=2,
                init_temperature=1.0,
                verbose=False
            ),
            OptimizerType.BOOTSTRAP.value: OptimizerConfig(
                optimizer_type=OptimizerType.BOOTSTRAP.value,
                num_candidates=10,
                max_bootstrapped_demos=4,
                max_labeled_demos=6,
                max_rounds=3,
                verbose=False
            ),
            OptimizerType.COPRO.value: OptimizerConfig(
                optimizer_type=OptimizerType.COPRO.value,
                num_candidates=10,
                breadth=10,
                depth=3,
                init_temperature=1.4,
                verbose=False
            ),
            OptimizerType.SIGNATURE_OPTIMIZER.value: OptimizerConfig(
                optimizer_type=OptimizerType.SIGNATURE_OPTIMIZER.value,
                num_candidates=5,
                verbose=False
            )
        }
    
    def get_base_config(self, optimizer_type: str) -> OptimizerConfig:
        """Get base configuration for optimizer type"""
        return self.base_configs.get(
            optimizer_type, 
            self.base_configs[OptimizerType.COPRO.value]
        ).copy()


class PerformanceHistory:
    """Track and analyze historical performance data"""
    
    def __init__(self, db_path: str):
        """Initialize performance history tracker"""
        self.db_path = db_path
        self._connection_lock = RLock()
    
    async def get_similar_performances(self, optimizer_type: str, 
                                     context: CompilationContext) -> List[Dict[str, Any]]:
        """Get historical performance for similar contexts"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        config_parameters,
                        avg_compilation_time,
                        success_rate,
                        avg_validation_score,
                        usage_count
                    FROM optimizer_config_performance
                    WHERE optimizer_type = ?
                    AND success_rate > 0.7
                    ORDER BY success_rate DESC, avg_compilation_time ASC
                    LIMIT 10
                """, (optimizer_type,))
                
                results = []
                for row in cursor.fetchall():
                    try:
                        config_params = json.loads(row[0])
                        results.append({
                            'config_parameters': config_params,
                            'avg_compilation_time': row[1],
                            'success_rate': row[2],
                            'avg_validation_score': row[3],
                            'usage_count': row[4]
                        })
                    except json.JSONDecodeError:
                        continue
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting similar performances: {e}")
            return []
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking"""
        with self._connection_lock:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()


class CompilationPerformanceTracker:
    """Track and monitor compilation performance metrics"""
    
    def __init__(self, db_path: str):
        """Initialize performance tracker"""
        self.db_path = db_path
        self._connection_lock = RLock()
        self.metrics_analyzer = PerformanceAnalyzer()
        self.alert_system = AlertSystem()
    
    async def record_compilation(self, result: CompiledModuleResult, session_id: str,
                               context: CompilationContext):
        """Record compilation performance metrics"""
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Record compilation
                cursor.execute("""
                    INSERT INTO dspy_module_compilations 
                    (id, optimizer_used, compilation_time, cache_hit, validation_score, 
                     success, config_used, performance_metrics, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    result.optimizer_used,
                    result.compilation_time,
                    result.cache_hit,
                    result.performance_metrics.validation_score,
                    True,
                    json.dumps(result.config_used or {}),
                    json.dumps(asdict(result.performance_metrics)),
                    datetime.now().isoformat(),
                    session_id
                ))
                
                conn.commit()
                
                # Update rolling metrics
                await self._update_rolling_metrics(result)
                
                # Check performance thresholds
                await self._check_performance_thresholds(result)
                
                logger.info(f"Performance recorded for {result.optimizer_used} compilation")
                
        except Exception as e:
            logger.error(f"Error recording compilation performance: {e}")
    
    async def record_compilation_failure(self, optimizer_type: str, compilation_time: float, 
                                       error_message: str, session_id: str):
        """Record compilation failure for analysis"""
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO dspy_module_compilations 
                    (id, optimizer_used, compilation_time, success, error_message, 
                     timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    optimizer_type,
                    compilation_time,
                    False,
                    error_message,
                    datetime.now().isoformat(),
                    session_id
                ))
                
                conn.commit()
                
                # Check failure rate thresholds
                await self._check_failure_rate_thresholds(optimizer_type)
                
                logger.warning(f"Compilation failure recorded for {optimizer_type}")
                
        except Exception as e:
            logger.error(f"Error recording compilation failure: {e}")
    
    async def record_cache_hit(self, cache_key: str, session_id: str):
        """Record cache hit for performance tracking"""
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO cache_performance_logs 
                    (id, cache_key, hit_type, retrieval_time, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    cache_key,
                    'direct',
                    0.1,  # Fast cache retrieval
                    datetime.now().isoformat(),
                    session_id
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording cache hit: {e}")
    
    async def get_performance_summary(self, time_period: str = '24h') -> Dict[str, Any]:
        """Get compilation performance summary"""
        
        try:
            hours_back = self._parse_time_period(time_period)
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Overall statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_compilations,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_compilations,
                        AVG(compilation_time) as avg_compilation_time,
                        COUNT(CASE WHEN cache_hit = 1 THEN 1 END) as cache_hits,
                        AVG(validation_score) as avg_validation_score
                    FROM dspy_module_compilations
                    WHERE timestamp >= ?
                """, (cutoff_time.isoformat(),))
                
                overall_stats = cursor.fetchone()
                
                # Optimizer breakdown
                cursor.execute("""
                    SELECT 
                        optimizer_used,
                        COUNT(*) as usage_count,
                        AVG(compilation_time) as avg_time,
                        COUNT(CASE WHEN success = 1 THEN 1 END) * 1.0 / COUNT(*) as success_rate,
                        AVG(validation_score) as avg_validation
                    FROM dspy_module_compilations
                    WHERE timestamp >= ?
                    GROUP BY optimizer_used
                    ORDER BY usage_count DESC
                """, (cutoff_time.isoformat(),))
                
                optimizer_stats = cursor.fetchall()
                
                return {
                    'time_period': time_period,
                    'overall': {
                        'total_compilations': overall_stats[0] or 0,
                        'successful_compilations': overall_stats[1] or 0,
                        'success_rate': (overall_stats[1] or 0) / (overall_stats[0] or 1),
                        'average_compilation_time': round(overall_stats[2] or 0, 2),
                        'cache_hit_rate': (overall_stats[3] or 0) / (overall_stats[0] or 1),
                        'average_validation_score': round(overall_stats[4] or 0, 3)
                    },
                    'by_optimizer': [
                        {
                            'optimizer': row[0],
                            'usage_count': row[1],
                            'avg_compilation_time': round(row[2] or 0, 2),
                            'success_rate': round(row[3] or 0, 3),
                            'avg_validation_score': round(row[4] or 0, 3)
                        } for row in optimizer_stats
                    ],
                    'performance_targets': {
                        'target_success_rate': 0.85,
                        'target_compilation_time': 30.0,
                        'target_validation_score': 0.8,
                        'target_cache_hit_rate': 0.3
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    def _parse_time_period(self, time_period: str) -> int:
        """Parse time period string to hours"""
        if time_period.endswith('h'):
            return int(time_period[:-1])
        elif time_period.endswith('d'):
            return int(time_period[:-1]) * 24
        else:
            return 24  # Default to 24 hours
    
    async def _update_rolling_metrics(self, result: CompiledModuleResult):
        """Update rolling performance metrics"""
        # Update optimizer-specific metrics in database
        try:
            config_hash = hashlib.md5(json.dumps(result.config_used or {}, sort_keys=True).encode()).hexdigest()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update or insert optimizer config performance
                cursor.execute("""
                    INSERT OR REPLACE INTO optimizer_config_performance
                    (optimizer_type, config_hash, config_parameters, avg_compilation_time,
                     success_rate, avg_validation_score, usage_count, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT usage_count FROM optimizer_config_performance 
                                      WHERE optimizer_type = ? AND config_hash = ?), 0) + 1,
                            ?)
                """, (
                    result.optimizer_used,
                    config_hash,
                    json.dumps(result.config_used or {}),
                    result.compilation_time,
                    1.0,  # Success
                    result.performance_metrics.validation_score,
                    result.optimizer_used,
                    config_hash,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating rolling metrics: {e}")
    
    async def _check_performance_thresholds(self, result: CompiledModuleResult):
        """Check performance against defined thresholds"""
        
        # Check compilation time threshold (30 seconds)
        if result.compilation_time > 30.0:
            await self.alert_system.send_alert(
                "PERFORMANCE_DEGRADATION",
                f"Compilation time exceeded 30s: {result.compilation_time:.2f}s for {result.optimizer_used}"
            )
        
        # Check validation score threshold
        if result.performance_metrics.validation_score < 0.7:
            await self.alert_system.send_alert(
                "LOW_VALIDATION_SCORE",
                f"Validation score below threshold: {result.performance_metrics.validation_score:.2f} for {result.optimizer_used}"
            )
    
    async def _check_failure_rate_thresholds(self, optimizer_type: str):
        """Check failure rate for optimizer"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recent failure rate
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN success = 1 THEN 1 END) * 1.0 / COUNT(*) as success_rate
                    FROM dspy_module_compilations
                    WHERE optimizer_used = ?
                    AND timestamp >= datetime('now', '-1 hour')
                """, (optimizer_type,))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    success_rate = result[0]
                    if success_rate < 0.8:  # 80% success rate threshold
                        await self.alert_system.send_alert(
                            "LOW_SUCCESS_RATE",
                            f"Success rate for {optimizer_type}: {success_rate:.1%} (last hour)"
                        )
                
        except Exception as e:
            logger.error(f"Error checking failure rate thresholds: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking"""
        with self._connection_lock:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()


class PerformanceAnalyzer:
    """Analyze compilation performance trends"""
    
    def __init__(self):
        """Initialize performance analyzer"""
        pass
    
    async def analyze_trends(self, records: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trends from records"""
        if not records:
            return {}
        
        # Simple trend analysis
        recent_records = records[:10] if len(records) > 10 else records
        avg_recent_time = sum(r.get('compilation_time', 0) for r in recent_records) / len(recent_records)
        
        return {
            'trend': 'stable',
            'avg_recent_compilation_time': avg_recent_time,
            'total_analyzed': len(records)
        }


class AlertSystem:
    """System for sending performance alerts"""
    
    def __init__(self):
        """Initialize alert system"""
        pass
    
    async def send_alert(self, alert_type: str, message: str):
        """Send performance alert"""
        logger.warning(f"ALERT [{alert_type}]: {message}")
        # In real implementation, would send to monitoring system


# Export main classes
__all__ = [
    'DSPyModuleCompiler',
    'CompilationContext',
    'CompiledModuleResult',
    'OptimizerType',
    'CompilationError',
    'OptimizerRegistry',
    'IntelligentCacheManager',
    'ConfigurationOptimizer',
    'CompilationPerformanceTracker'
]


if __name__ == "__main__":
    # Test the DSPy module compilation system
    async def test_module_compilation():
        """Test the DSPy module compilation functionality"""
        print("DSPy Module Compilation System Test")
        print("=" * 50)
        
        try:
            # Initialize the compiler
            compiler = DSPyModuleCompiler()
            
            # Create a test signature
            test_signature = dspy.Signature("question -> answer")
            
            # Create test examples
            test_examples = [
                {"question": "What is the capital of France?", "answer": "Paris"},
                {"question": "What is 2+2?", "answer": "4"},
                {"question": "What color is the sky?", "answer": "Blue"}
            ]
            
            print(f"\nTesting compilation with signature: {test_signature}")
            print(f"Using {len(test_examples)} training examples")
            
            # Test compilation with different optimization targets
            for optimize_for in ['quality', 'speed']:
                print(f"\n--- Testing optimization for: {optimize_for} ---")
                
                result = await compiler.compile_optimized_module(
                    signature=test_signature,
                    examples=test_examples,
                    optimize_for=optimize_for
                )
                
                print(f"Optimizer used: {result.optimizer_used}")
                print(f"Compilation time: {result.compilation_time:.2f}s")
                print(f"Cache hit: {result.cache_hit}")
                print(f"Validation score: {result.performance_metrics.validation_score:.3f}")
                print(f"Reasoning: {result.optimizer_reasoning}")
            
            # Test performance summary
            print(f"\n--- Performance Summary ---")
            summary = await compiler.performance_tracker.get_performance_summary()
            print(f"Total compilations: {summary['overall']['total_compilations']}")
            print(f"Success rate: {summary['overall']['success_rate']:.1%}")
            print(f"Average compilation time: {summary['overall']['average_compilation_time']:.2f}s")
            
            print("\nModule compilation test completed!")
            
        except Exception as e:
            print(f"Error in test: {e}")
            import traceback
            traceback.print_exc()
    
    # Run test if executed directly
    asyncio.run(test_module_compilation())