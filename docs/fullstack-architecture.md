# Fullstack Architecture: DSPy-MCP Prompt Optimizer

**Document Version:** 1.0  
**Date:** 2025-07-30  
**Technical Architect:** BMad Technical Architect  
**Project:** DSPy-MCP Integration Initiative

---

## System Overview

The DSPy-MCP Prompt Optimizer is a Python-based MCP server that integrates Stanford's DSPy framework for automated prompt optimization. The system transforms manual prompt engineering into an intelligent, self-learning optimization platform delivered through the Model Context Protocol.

### High-Level Architecture Diagram

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Claude Desktop    │    │    Python MCP      │    │     DSPy Engine     │
│                     │◄──►│     Server          │◄──►│                     │
│  - Tool Calls       │    │  - prompt_optimizer │    │  - Module Compiler  │
│  - Resource Access  │    │  - advanced_strat   │    │  - Strategy Engine  │
│  - Progress Updates │    │  - domain_templates │    │  - Learning System  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                           ┌─────────────────────┐
                           │   Storage Layer     │
                           │                     │
                           │ - SQLite/PostgreSQL │
                           │ - Example Storage   │
                           │ - Performance Cache │
                           │ - User Preferences  │
                           └─────────────────────┘
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant Claude as Claude Desktop
    participant MCP as MCP Server
    participant DSPy as DSPy Engine
    participant Storage as Storage Layer
    
    Claude->>MCP: dspy_optimize(prompt, strategy)
    MCP->>DSPy: analyze_prompt(prompt)
    DSPy->>DSPy: detect_signature()
    DSPy->>Storage: fetch_examples(task_type)
    Storage-->>DSPy: training_examples[]
    DSPy->>DSPy: compile_module(signature, examples)
    DSPy->>DSPy: execute_optimization()
    DSPy-->>MCP: optimization_result
    MCP->>Storage: record_performance(result)
    MCP-->>Claude: optimized_prompt + metrics
```

---

## Technology Stack

### Core Framework Stack
```python
# Core MCP Framework
mcp>=0.1.0                    # Model Context Protocol server framework

# DSPy Framework & ML
dspy-ai>=2.4.0                # Stanford DSPy framework for prompt optimization
openai>=1.0.0                 # LLM API integration
anthropic>=0.8.0              # Claude API support
torch>=2.0.0                  # PyTorch for model operations
transformers>=4.30.0          # Hugging Face transformers
scikit-learn>=1.3.0           # Machine learning utilities

# Data Processing & Storage
pandas>=2.0.0                 # Data manipulation and analysis
sqlalchemy>=2.0.0             # Database ORM
alembic>=1.11.0               # Database migrations
sqlite3                       # Default lightweight database
redis>=4.5.0                  # Caching and session management

# Development & Testing
pytest>=7.4.0                 # Testing framework
pytest-asyncio>=0.21.0        # Async testing support
black>=23.7.0                 # Code formatting
mypy>=1.5.0                   # Type checking
structlog>=23.1.0             # Structured logging
```

### Architecture Rationale

**DSPy Framework Choice**: Stanford's DSPy provides automated prompt optimization through compilation, enabling 25-65% performance improvements over manual methods.

**MCP Protocol**: Ensures seamless integration with Claude Desktop and future MCP-compatible tools, providing standardized tool discovery and execution.

**SQLite Default**: Lightweight, zero-configuration database perfect for single-user deployments while supporting PostgreSQL for enterprise use.

**Async Python**: Full async/await pattern for handling concurrent optimization requests and non-blocking MCP operations.

---

## Database Design

### Core Schema Structure

```sql
-- DSPy Signatures Registry
CREATE TABLE dspy_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    signature_definition TEXT NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    performance_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    
    INDEX idx_task_type (task_type),
    INDEX idx_performance (performance_score DESC)
);

-- Compiled DSPy Modules
CREATE TABLE dspy_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signature_id UUID REFERENCES dspy_signatures(id) ON DELETE CASCADE,
    module_data BYTEA NOT NULL,           -- Serialized compiled module
    optimizer_used VARCHAR(100) NOT NULL, -- MIPRO, BootstrapFewShot, etc.
    compilation_params JSONB,             -- Compilation configuration
    compilation_timestamp TIMESTAMP DEFAULT NOW(),
    performance_metrics JSONB,            -- Validation scores, metrics
    validation_score FLOAT,
    
    INDEX idx_signature_id (signature_id),
    INDEX idx_performance_desc (validation_score DESC NULLS LAST)
);

-- Training Examples for DSPy
CREATE TABLE dspy_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(100) NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    quality_score FLOAT NOT NULL CHECK (quality_score >= 0 AND quality_score <= 1),
    source VARCHAR(100) DEFAULT 'user_feedback', -- 'user_feedback', 'mined', 'curated'
    metadata JSONB,                       -- Additional context, tags, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    usage_count INTEGER DEFAULT 0,
    
    INDEX idx_task_type_quality (task_type, quality_score DESC),
    INDEX idx_quality_desc (quality_score DESC)
);

-- Optimization Session Tracking
CREATE TABLE optimization_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),                 -- Hashed user identifier
    original_prompt TEXT NOT NULL,
    optimized_prompt TEXT NOT NULL,
    strategy_used VARCHAR(100),
    dspy_signature_id UUID REFERENCES dspy_signatures(id),
    dspy_module_id UUID REFERENCES dspy_modules(id),
    performance_metrics JSONB,            -- Improvement scores, timing, etc.
    user_feedback FLOAT,                  -- User satisfaction (0-1)
    session_timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp_desc (session_timestamp DESC),
    INDEX idx_strategy (strategy_used)
);

-- User Learning Preferences
CREATE TABLE user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    preferred_strategies JSONB,           -- Weighted strategy preferences
    optimization_weights JSONB,          -- Speed vs quality preferences
    domain_preferences JSONB,            -- Domain-specific patterns
    personalization_data JSONB,          -- Learned user patterns
    last_updated TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_last_updated (last_updated DESC)
);
```

### Data Flow & Management

**DSPy Example Mining**: Automatically extracts high-quality examples from successful user interactions with quality scores > 0.8.

**Module Caching**: Compiled DSPy modules are cached with performance metadata to avoid recompilation for similar requests.

**Performance Tracking**: All optimization sessions tracked with detailed metrics for continuous learning and user personalization.

---

## API Architecture

### MCP Tool Interface Design

```python
from mcp import Server
from mcp.server.models import Tool, TextContent, Resource
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

app = Server("dspy-prompt-optimizer")

# Core DSPy optimization tools
DSPY_TOOLS = [
    Tool(
        name="dspy_optimize",
        description="Optimize prompts using DSPy with automatic strategy selection",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to optimize using DSPy compilation"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["reasoning", "classification", "generation", "analysis", "auto"],
                    "default": "auto",
                    "description": "Task type hint for signature selection"
                },
                "optimize_for": {
                    "type": "string", 
                    "enum": ["speed", "quality", "accuracy"],
                    "default": "quality",
                    "description": "Optimization priority"
                },
                "custom_examples": {
                    "type": "array",
                    "items": {"type": "object"},
                    "optional": True,
                    "description": "Custom training examples for DSPy compilation"
                }
            },
            "required": ["prompt"]
        }
    ),
    
    Tool(
        name="dspy_compile_module",
        description="Compile custom DSPy module with specified signature and examples",
        inputSchema={
            "type": "object",
            "properties": {
                "signature": {
                    "type": "string",
                    "description": "DSPy signature definition (e.g., 'input -> reasoning, output')"
                },
                "training_examples": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Training examples for module compilation"
                },
                "optimizer_strategy": {
                    "type": "string",
                    "enum": ["mipro", "bootstrap", "copro", "signature_opt", "auto"],
                    "default": "auto",
                    "description": "DSPy optimizer to use for compilation"
                },
                "module_name": {
                    "type": "string",
                    "optional": True,
                    "description": "Name for saving compiled module"
                }
            },
            "required": ["signature", "training_examples"]
        }
    ),
    
    Tool(
        name="dspy_evaluate",
        description="Evaluate prompt performance using DSPy metrics",
        inputSchema={
            "type": "object",
            "properties": {
                "original_prompt": {"type": "string"},
                "optimized_prompt": {"type": "string"},
                "test_cases": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Test cases for evaluation"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["accuracy", "relevance", "coherence"],
                    "description": "Metrics to evaluate"
                }
            },
            "required": ["original_prompt", "optimized_prompt", "test_cases"]
        }
    )
]

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available DSPy-enhanced MCP tools"""
    return DSPY_TOOLS + get_legacy_tools()

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Enhanced MCP tool handler with DSPy integration"""
    
    if name == "dspy_optimize":
        return await handle_dspy_optimize(arguments)
    elif name == "dspy_compile_module":
        return await handle_dspy_compile(arguments)
    elif name == "dspy_evaluate":
        return await handle_dspy_evaluate(arguments)
    else:
        # Fallback to legacy optimization tools
        return await handle_legacy_tool(name, arguments)
```

### DSPy Integration Layer

```python
class DSPyMCPIntegration:
    """Core integration between DSPy framework and MCP server"""
    
    def __init__(self):
        self.signature_detector = DSPySignatureDetector()
        self.module_compiler = DSPyModuleCompiler()
        self.example_miner = DSPyExampleMiner()
        self.learning_system = DSPyLearningSystem()
        self.performance_tracker = PerformanceTracker()
    
    async def optimize_prompt(self, request: OptimizationRequest) -> OptimizationResult:
        """Main DSPy optimization workflow"""
        
        # Phase 1: Strategy Detection & Signature Selection
        strategy = await self.signature_detector.detect_optimal_strategy(
            prompt=request.prompt,
            task_type=request.task_type,
            context=request.context
        )
        
        # Phase 2: Example Mining & Preparation  
        examples = await self.example_miner.get_training_examples(
            task_type=strategy.task_type,
            min_quality=0.8,
            max_examples=50
        )
        
        if request.custom_examples:
            examples.extend(request.custom_examples)
        
        # Phase 3: DSPy Module Compilation
        compiled_module = await self.module_compiler.compile_optimized_module(
            signature=strategy.signature,
            examples=examples,
            optimizer=strategy.optimizer,
            optimize_for=request.optimize_for
        )
        
        # Phase 4: Optimization Execution
        with dspy.context(lm=self._get_language_model()):
            optimization_result = await compiled_module.optimize(
                input_prompt=request.prompt
            )
        
        # Phase 5: Performance Tracking & Learning
        result = OptimizationResult(
            original_prompt=request.prompt,
            optimized_prompt=optimization_result.output,
            strategy_used=strategy.name,
            dspy_module_info=compiled_module.get_info(),
            performance_metrics=optimization_result.metrics,
            confidence_score=optimization_result.confidence
        )
        
        await self.performance_tracker.record_session(request, result)
        await self.learning_system.update_from_result(result)
        
        return result
```

---

## Frontend Architecture

### MCP Protocol Integration Patterns

Since this is an MCP server, the "frontend" consists of MCP protocol interactions through Claude Desktop. The user experience is delivered through structured tool responses and resource management.

#### Tool Response Structure

```python
class MCPResponseFormatter:
    """Formats DSPy optimization results for optimal MCP presentation"""
    
    @staticmethod
    def format_optimization_result(result: OptimizationResult) -> List[TextContent]:
        """Format DSPy optimization for Claude Desktop display"""
        
        response_data = {
            "optimization_summary": {
                "original_length": len(result.original_prompt),
                "optimized_length": len(result.optimized_prompt),
                "improvement_score": f"{result.performance_metrics.improvement:.1%}",
                "confidence": f"{result.confidence_score:.1%}"
            },
            "dspy_details": {
                "strategy_used": result.strategy_used,
                "signature": str(result.dspy_module_info.signature),
                "optimizer": result.dspy_module_info.optimizer,
                "examples_count": result.dspy_module_info.examples_count,
                "compilation_time": f"{result.dspy_module_info.compilation_time:.2f}s"
            },
            "prompts": {
                "original": result.original_prompt,
                "optimized": result.optimized_prompt
            },
            "performance_analysis": {
                "expected_improvement": f"{result.performance_metrics.expected_improvement:.1%}",
                "reasoning_quality": result.performance_metrics.reasoning_quality,
                "clarity_score": result.performance_metrics.clarity_score
            }
        }
        
        # Format for Claude Desktop presentation
        formatted_response = json.dumps(response_data, indent=2)
        
        return [TextContent(
            type="text", 
            text=f"# DSPy Optimization Complete\n\n```json\n{formatted_response}\n```"
        )]
```

#### Resource Management for DSPy Assets

```python
@app.list_resources()
async def list_resources() -> List[Resource]:
    """Provide access to DSPy examples, strategies, and modules"""
    
    resources = []
    
    # DSPy compiled modules
    modules = await get_compiled_modules()
    for module in modules:
        resources.append(Resource(
            uri=f"dspy://modules/{module.id}",
            name=f"Compiled Module: {module.name}",
            description=f"DSPy module for {module.task_type} with {module.performance_score:.1%} performance",
            mimeType="application/json"
        ))
    
    # Training example collections
    example_collections = await get_example_collections()
    for collection in example_collections:
        resources.append(Resource(
            uri=f"dspy://examples/{collection.task_type}",
            name=f"Training Examples: {collection.task_type}",
            description=f"{collection.count} high-quality examples (avg quality: {collection.avg_quality:.1%})",
            mimeType="application/json"
        ))
    
    return resources

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Provide access to DSPy resources"""
    
    if uri.startswith("dspy://modules/"):
        module_id = uri.split("/")[-1]
        module = await get_compiled_module(module_id)
        return json.dumps(module.serialize())
    
    elif uri.startswith("dspy://examples/"):
        task_type = uri.split("/")[-1]
        examples = await get_training_examples(task_type)
        return json.dumps([ex.to_dict() for ex in examples])
    
    raise ValueError(f"Unknown resource URI: {uri}")
```

---

## Database and Caching Design

### Caching Strategy

```python
import redis
from typing import Optional, Dict, Any
import json
import pickle
from datetime import timedelta

class DSPyCacheManager:
    """Redis-based caching for DSPy operations"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=False  # Binary for pickle storage
        )
        self.default_ttl = timedelta(hours=24)
    
    async def cache_compiled_module(self, signature_hash: str, module: Any, ttl: Optional[timedelta] = None):
        """Cache compiled DSPy module to avoid recompilation"""
        cache_key = f"dspy:module:{signature_hash}"
        serialized_module = pickle.dumps(module)
        
        await self.redis_client.setex(
            cache_key, 
            (ttl or self.default_ttl).total_seconds(),
            serialized_module
        )
    
    async def get_cached_module(self, signature_hash: str) -> Optional[Any]:
        """Retrieve cached compiled module"""
        cache_key = f"dspy:module:{signature_hash}"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return pickle.loads(cached_data)
        return None
    
    async def cache_optimization_result(self, prompt_hash: str, result: Dict[str, Any]):
        """Cache optimization results for identical prompts"""
        cache_key = f"dspy:result:{prompt_hash}"
        await self.redis_client.setex(
            cache_key,
            timedelta(hours=4).total_seconds(),  # Shorter TTL for results
            json.dumps(result)
        )
    
    async def cache_training_examples(self, task_type: str, examples: List[Dict]):
        """Cache mined training examples"""
        cache_key = f"dspy:examples:{task_type}"
        await self.redis_client.setex(
            cache_key,
            timedelta(hours=12).total_seconds(),
            json.dumps(examples)
        )
```

### Database Connection Management

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

class Database:
    """Async database connection manager"""
    
    def __init__(self):
        # Support both SQLite (development) and PostgreSQL (production)
        database_url = os.getenv(
            "DATABASE_URL", 
            "sqlite+aiosqlite:///./dspy_mcp_optimizer.db"
        )
        
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        """Get database session for operations"""
        async with self.async_session() as session:
            yield session
    
    async def initialize_database(self):
        """Initialize database schema"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
```

---

## Performance Considerations

### Async Processing Architecture

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any

class AsyncOptimizationManager:
    """Manages concurrent DSPy optimizations with resource limits"""
    
    def __init__(self, max_concurrent_optimizations: int = 5):
        self.max_concurrent = max_concurrent_optimizations
        self.semaphore = asyncio.Semaphore(max_concurrent_optimizations)
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
    
    async def optimize_with_concurrency_control(self, request: OptimizationRequest) -> OptimizationResult:
        """Execute optimization with concurrency limits"""
        
        async with self.semaphore:
            # CPU-intensive DSPy compilation runs in thread pool
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                self.thread_pool,
                self._sync_optimization_worker,
                request
            )
            
            return result
    
    def _sync_optimization_worker(self, request: OptimizationRequest) -> OptimizationResult:
        """Synchronous worker for CPU-intensive DSPy operations"""
        # This runs DSPy compilation in a separate thread
        # to avoid blocking the main event loop
        return self.dspy_integration.optimize_prompt_sync(request)
    
    async def batch_optimize(self, requests: List[OptimizationRequest]) -> List[OptimizationResult]:
        """Process multiple optimization requests concurrently"""
        
        tasks = [
            self.optimize_with_concurrency_control(request) 
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in batch processing
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(OptimizationResult.create_error(
                    original_prompt=requests[i].prompt,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
```

### Performance Monitoring

```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Prometheus metrics for monitoring
optimization_requests = Counter('dspy_optimization_requests_total', 'Total optimization requests')
optimization_duration = Histogram('dspy_optimization_duration_seconds', 'Optimization processing time')
active_optimizations = Gauge('dspy_active_optimizations', 'Currently active optimizations')
compilation_cache_hits = Counter('dspy_compilation_cache_hits_total', 'Module compilation cache hits')

def monitor_performance(func):
    """Decorator for monitoring optimization performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        optimization_requests.inc()
        active_optimizations.inc()
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            optimization_duration.observe(time.time() - start_time)
            return result
        finally:
            active_optimizations.dec()
    
    return wrapper
```

---

## Error Handling Approach

### Comprehensive Error Management

```python
from enum import Enum
from typing import Optional, Dict, Any
import structlog
import traceback

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DSPyMCPError(Exception):
    """Base exception for DSPy-MCP integration errors"""
    
    def __init__(self, message: str, error_code: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()

class CompilationError(DSPyMCPError):
    """DSPy module compilation failed"""
    pass

class OptimizationError(DSPyMCPError):
    """Prompt optimization failed"""
    pass

class ResourceError(DSPyMCPError):
    """Resource access or management failed"""
    pass

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self):
        self.logger = structlog.get_logger("error_handler")
    
    async def handle_optimization_error(self, error: Exception, request: OptimizationRequest) -> OptimizationResult:
        """Handle optimization errors with fallback strategies"""
        
        self.logger.error(
            "optimization_failed",
            error=str(error),
            request_id=request.id,
            prompt_length=len(request.prompt),
            strategy=request.strategy
        )
        
        # Attempt fallback to basic optimization
        if not isinstance(error, CompilationError):
            try:
                fallback_result = await self._fallback_basic_optimization(request)
                fallback_result.add_warning("Used fallback optimization due to DSPy error")
                return fallback_result
            except Exception as fallback_error:
                self.logger.error("fallback_optimization_failed", error=str(fallback_error))
        
        # Return error result if all fallbacks fail
        return OptimizationResult.create_error(
            original_prompt=request.prompt,
            error_message=f"Optimization failed: {str(error)}",
            error_code=getattr(error, 'error_code', 'UNKNOWN_ERROR')
        )
    
    async def _fallback_basic_optimization(self, request: OptimizationRequest) -> OptimizationResult:
        """Fallback to basic optimization strategies when DSPy fails"""
        from advanced_strategies import AdvancedPromptOptimizer
        
        basic_optimizer = AdvancedPromptOptimizer()
        
        # Use the most reliable strategy as fallback
        result = basic_optimizer.optimize_prompt(
            request.prompt,
            strategy="chain_of_thought"  # Most reliable fallback
        )
        
        return OptimizationResult(
            original_prompt=request.prompt,
            optimized_prompt=result["optimized"],
            strategy_used="fallback_chain_of_thought",
            performance_metrics={"fallback_used": True},
            confidence_score=0.6  # Lower confidence for fallback
        )

# Global error handler
error_handler = ErrorHandler()

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """MCP tool handler with comprehensive error handling"""
    
    try:
        if name == "dspy_optimize":
            request = OptimizationRequest.from_mcp_args(arguments)
            result = await dspy_integration.optimize_prompt(request)
            return MCPResponseFormatter.format_optimization_result(result)
            
    except DSPyMCPError as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "error_code": e.error_code,
                "message": e.message,
                "severity": e.severity.value,
                "timestamp": e.timestamp.isoformat()
            }, indent=2)
        )]
        
    except Exception as e:
        # Log unexpected errors
        structlog.get_logger().error(
            "unexpected_error",
            tool_name=name,
            arguments=arguments,
            error=str(e),
            traceback=traceback.format_exc()
        )
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": True,
                "error_code": "UNEXPECTED_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": str(e) if os.getenv("DEBUG") else None
            }, indent=2)
        )]
```

---

## Source Tree Structure

```
mcp-prompt-optimizer/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py                 # Main MCP server entry point
│   │   ├── tools/                    # MCP tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── dspy_tools.py         # DSPy-powered MCP tools
│   │   │   ├── legacy_tools.py       # Existing optimization tools
│   │   │   └── evaluation_tools.py   # Performance evaluation tools
│   │   └── resources/                # MCP resource handlers
│   │       ├── __init__.py
│   │       ├── module_resources.py   # DSPy module access
│   │       └── example_resources.py  # Training example access
│   │
│   ├── dspy_integration/
│   │   ├── __init__.py
│   │   ├── core.py                   # Main DSPy integration orchestrator
│   │   ├── signature_detection.py   # Auto-signature detection
│   │   ├── module_compiler.py       # DSPy module compilation
│   │   ├── example_mining.py        # Training example management
│   │   ├── learning_system.py       # Continuous learning engine  
│   │   └── performance_tracker.py   # Performance metrics & analysis
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── connection.py            # Database connection management
│   │   ├── migrations/              # Alembic database migrations
│   │   └── repositories/            # Data access layer
│   │       ├── __init__.py
│   │       ├── signature_repo.py
│   │       ├── module_repo.py
│   │       ├── example_repo.py
│   │       └── session_repo.py
│   │
│   ├── caching/
│   │   ├── __init__.py
│   │   ├── redis_cache.py           # Redis caching implementation
│   │   ├── memory_cache.py          # In-memory caching fallback
│   │   └── cache_manager.py         # Cache coordination
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py               # Prometheus metrics
│   │   ├── logging.py               # Structured logging setup
│   │   └── health_checks.py         # System health monitoring
│   │
│   └── utils/
│       ├── __init__.py
│       ├── async_helpers.py         # Async utility functions
│       ├── error_handling.py        # Error management utilities
│       └── config.py                # Configuration management
│
├── legacy/                          # Existing code (preserved)
│   ├── prompt_optimizer.py          # Original MCP server
│   ├── advanced_strategies.py       # Advanced optimization strategies
│   └── domain_templates.py          # Domain-specific templates
│
├── config/
│   ├── dspy_config.yaml            # DSPy framework configuration
│   ├── mcp_config.yaml             # MCP server configuration
│   └── database_config.yaml        # Database settings
│
├── tests/
│   ├── unit/                       # Unit tests
│   │   ├── test_dspy_integration/
│   │   ├── test_mcp_tools/
│   │   └── test_database/
│   ├── integration/                # Integration tests
│   │   ├── test_mcp_protocol/
│   │   └── test_end_to_end/
│   └── performance/                # Performance tests
│       └── test_load_handling/
│
├── docs/
│   ├── api_reference.md            # Complete API documentation
│   ├── deployment_guide.md         # Production deployment guide
│   ├── development_setup.md        # Developer environment setup
│   └── troubleshooting.md          # Common issues and solutions
│
├── scripts/
│   ├── setup_development.py        # Development environment setup
│   ├── run_migrations.py           # Database migration runner
│   ├── benchmark_performance.py    # Performance benchmarking
│   └── export_modules.py           # DSPy module export utility
│
├── requirements/
│   ├── base.txt                    # Core dependencies
│   ├── development.txt             # Development dependencies
│   └── production.txt              # Production dependencies
│
├── docker/
│   ├── Dockerfile                  # Production container
│   ├── docker-compose.yml          # Local development stack
│   └── docker-compose.prod.yml     # Production stack
│
├── .github/
│   └── workflows/
│       ├── test.yml                # CI/CD pipeline
│       └── deploy.yml              # Deployment automation
│
├── prompt_optimizer.py             # Main entry point (backwards compatibility)
├── requirements.txt                # Core requirements (backwards compatibility)
├── setup.py                        # Package setup
├── pyproject.toml                  # Modern Python project configuration
├── README.md                       # Project documentation
└── CHANGELOG.md                    # Version history
```

---

## Development Standards

### Code Quality & Type Safety

```python
# Type hints and documentation standards
from typing import Protocol, TypeVar, Generic, Optional, Union, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

T = TypeVar('T')

class DSPyOptimizer(Protocol):
    """Protocol defining DSPy optimizer interface"""
    
    async def optimize(self, prompt: str, context: Dict[str, Any]) -> OptimizationResult:
        """Optimize prompt using DSPy compilation"""
        ...
    
    async def compile_module(self, signature: str, examples: List[Dict]) -> CompiledModule:
        """Compile DSPy module with training examples"""
        ...

@dataclass(frozen=True)
class OptimizationResult:
    """Immutable optimization result with full type safety"""
    original_prompt: str
    optimized_prompt: str
    strategy_used: str
    confidence_score: float
    performance_metrics: Dict[str, float]
    dspy_module_info: Optional['ModuleInfo'] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        # Validation
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0 and 1")
        
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])

# Error handling with type safety
class Result(Generic[T]):
    """Result type for error handling without exceptions"""
    
    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self._value = value
        self._error = error
    
    @property
    def is_success(self) -> bool:
        return self._error is None
    
    @property
    def value(self) -> T:
        if self._error:
            raise ValueError(f"Result contains error: {self._error}")
        return self._value
    
    @property
    def error(self) -> Optional[str]:
        return self._error

async def safe_optimization(prompt: str) -> Result[OptimizationResult]:
    """Type-safe optimization with error handling"""
    try:
        result = await dspy_integration.optimize_prompt(prompt)
        return Result(value=result)
    except Exception as e:
        return Result(error=str(e))
```

### Testing Strategy

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.dspy_integration.core import DSPyMCPIntegration

class TestDSPyIntegration:
    """Comprehensive test suite for DSPy integration"""
    
    @pytest.fixture
    async def dspy_integration(self):
        """Create DSPy integration instance for testing"""
        integration = DSPyMCPIntegration()
        await integration.initialize()
        return integration
    
    @pytest.mark.asyncio
    async def test_prompt_optimization_quality(self, dspy_integration):
        """Test optimization produces measurable improvements"""
        test_prompt = "Write a blog post about AI"
        
        result = await dspy_integration.optimize_prompt(
            OptimizationRequest(prompt=test_prompt)
        )
        
        # Quality assertions
        assert len(result.optimized_prompt) > len(test_prompt)
        assert result.confidence_score > 0.7
        assert result.performance_metrics['expected_improvement'] > 0.2
        assert result.optimized_prompt != test_prompt
    
    @pytest.mark.asyncio
    async def test_concurrent_optimization_handling(self, dspy_integration):
        """Test system handles concurrent optimization requests"""
        prompts = [f"Optimize prompt {i}" for i in range(10)]
        
        tasks = [
            dspy_integration.optimize_prompt(OptimizationRequest(prompt=p))
            for p in prompts
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert len(results) == 10
        assert all(r.confidence_score > 0 for r in results)
        assert all(r.optimized_prompt != r.original_prompt for r in results)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, dspy_integration):
        """Test error handling provides appropriate fallbacks"""
        # Mock DSPy compilation failure
        dspy_integration.module_compiler.compile_module = AsyncMock(
            side_effect=CompilationError("Mock compilation failure")
        )
        
        result = await dspy_integration.optimize_prompt(
            OptimizationRequest(prompt="Test prompt")
        )
        
        # Should fallback gracefully
        assert result.optimized_prompt is not None
        assert "fallback" in result.strategy_used.lower()
        assert len(result.warnings) > 0
        assert result.confidence_score < 0.8  # Lower confidence for fallback

# Performance benchmarks
@pytest.mark.performance
class TestPerformanceBenchmarks:
    
    @pytest.mark.asyncio
    async def test_optimization_speed_benchmark(self, dspy_integration):
        """Benchmark optimization speed requirements"""
        import time
        
        start_time = time.time()
        result = await dspy_integration.optimize_prompt(
            OptimizationRequest(prompt="Standard optimization test prompt")
        )
        end_time = time.time()
        
        optimization_time = end_time - start_time
        
        # Performance requirements
        assert optimization_time < 30.0  # Must complete within 30 seconds
        assert result.confidence_score > 0.8  # Must maintain quality
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, dspy_integration):
        """Test memory usage remains stable under load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Run 50 optimizations
        for i in range(50):
            await dspy_integration.optimize_prompt(
                OptimizationRequest(prompt=f"Memory test prompt {i}")
            )
            
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024
```

---

## TECHNICAL_ARCHITECTURE_COMPLETE

This comprehensive technical architecture provides a production-ready foundation for the DSPy-MCP Prompt Optimizer integration. The architecture includes:

✅ **System Overview**: Clear component interaction and high-level architecture  
✅ **Technology Stack**: Complete dependency management with version specifications  
✅ **Database Design**: Optimized schema for DSPy operations with performance indexes  
✅ **API Architecture**: Full MCP protocol integration with async patterns  
✅ **Performance Design**: Concurrent processing, caching, and monitoring strategies  
✅ **Error Handling**: Comprehensive error management with fallback strategies  
✅ **Source Tree Structure**: Organized, maintainable project layout  
✅ **Development Standards**: Type safety, testing strategy, and code quality guidelines  

**Key Technical Strengths:**
- **Production-Ready**: Async Python with proper error handling and monitoring
- **Scalable Architecture**: Redis caching, connection pooling, and concurrent processing
- **Type Safety**: Complete type hints and protocol definitions
- **Testing Strategy**: Unit, integration, and performance test coverage
- **MCP Protocol Native**: Designed specifically for MCP server optimization
- **DSPy Integration**: Seamless integration with Stanford's DSPy framework for automated optimization

The architecture enables the development team to build a robust, scalable MCP server that delivers 25-65% performance improvements through intelligent DSPy-powered prompt optimization while maintaining enterprise-grade reliability and user experience.

**Implementation Readiness:**
- All major components have detailed implementation patterns
- Database schema is optimized for DSPy operations
- Error handling provides graceful degradation
- Performance monitoring ensures production reliability
- Testing strategy covers all critical paths

```python
# Update workflow state
workflow_state = read_json(".bmad/workflow-state.json")

# Update completion status
workflow_state["phase_status"]["planning"]["technical_architecture"] = "completed"
workflow_state["current_stage"] = "product_owner_validation"
workflow_state["last_updated"] = current_timestamp()
workflow_state["next_action"] = {
    "agent": "orchestrator-new",
    "description": "Technical architecture complete - awaiting user confirmation",
    "priority": "high",
    "user_confirmation_required": true,
    "pending_transition": "product-owner",
    "user_options": ["approve_and_continue", "request_modifications", "redo_architecture", "rollback_previous"]
}

# Update artifact status
workflow_state["artifacts"]["planning_docs"]["architecture"] = true

write_json(".bmad/workflow-state.json", workflow_state)
```

```python
# Log the completion and handoff
handoff_entry = {
    "timestamp": current_timestamp(),
    "from_agent": "technical-architect",
    "to_agent": "orchestrator-new",
    "deliverable": "docs/fullstack-architecture.md",
    "status": "completed",
    "notes": "Technical architecture and system design completed. Awaiting user confirmation before Product Owner validation."
}

handoffs = read_json(".bmad/agent-handoffs.log")
handoffs["handoffs"].append(handoff_entry)
handoffs["last_updated"] = current_timestamp()
handoffs["total_handoffs"] += 1
write_json(".bmad/agent-handoffs.log", handoffs)
```

**Technical Architecture Complete**

**Deliverable Created:** /Users/jeff/Documents/personal/mcp-prompt-optimizer/docs/fullstack-architecture.md  
**Ready for Review:** System architecture and technical specifications finished  
**Status:** Awaiting user confirmation before proceeding to Product Owner validation

**User Options:**
1. Approve and continue to Product Owner
2. Request modifications to current architecture
3. Redo architecture with different approach
4. Rollback to previous stage

The BMad Orchestrator-new will present these options to the user.