#!/usr/bin/env python3
"""
Performance Optimization and Caching System for DSPy Optimization
Implements Task 1.2.4 requirements for performance and caching.
"""

import asyncio
import sqlite3
import logging
import json
import hashlib
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import contextmanager
import queue
from threading import RLock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CachedResult:
    """Cached optimization result"""
    cache_key: str
    result_data: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    session_id: str
    operation_type: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    cache_hit: bool = False
    error_message: Optional[str] = None


class DatabaseConnectionPool:
    """
    Thread-safe SQLite connection pool to handle database concurrency.
    """
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """Initialize connection pool"""
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = queue.Queue(maxsize=max_connections)
        self._lock = RLock()
        
        # Initialize connection pool
        self._initialize_pool()
        
        logger.info(f"DatabaseConnectionPool initialized with {max_connections} connections")
    
    def _initialize_pool(self):
        """Initialize the connection pool with available connections"""
        try:
            for _ in range(self.max_connections):
                conn = sqlite3.connect(
                    self.db_path, 
                    check_same_thread=False,
                    timeout=30.0  # 30 second timeout for database locks
                )
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                conn.commit()
                self._connections.put(conn)
        except Exception as e:
            logger.error(f"Error initializing connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self, timeout: float = 10.0):
        """Get a connection from the pool with automatic return"""
        conn = None
        try:
            # Get connection from pool with timeout
            conn = self._connections.get(timeout=timeout)
            yield conn
        except queue.Empty:
            logger.error(f"Database connection pool timeout after {timeout}s")
            raise RuntimeError("Database connection pool exhausted")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    # Rollback any uncommitted transactions
                    conn.rollback()
                    # Return connection to pool
                    self._connections.put(conn, timeout=1.0)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    # Create new connection if return fails
                    try:
                        new_conn = sqlite3.connect(
                            self.db_path, 
                            check_same_thread=False,
                            timeout=30.0
                        )
                        new_conn.execute("PRAGMA journal_mode=WAL")
                        new_conn.execute("PRAGMA synchronous=NORMAL") 
                        new_conn.commit()
                        self._connections.put(new_conn, timeout=1.0)
                    except Exception as e2:
                        logger.error(f"Failed to create replacement connection: {e2}")
    
    def execute_with_retry(self, query: str, params: tuple = (), max_retries: int = 3) -> Any:
        """Execute query with retry logic for database locks"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    result = cursor.execute(query, params)
                    conn.commit()
                    return result
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower():
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Database execution error: {e}")
                raise
        
        logger.error(f"Database operation failed after {max_retries} retries: {last_error}")
        raise last_error
    
    def close(self):
        """Close all connections in the pool"""
        try:
            while not self._connections.empty():
                conn = self._connections.get_nowait()
                conn.close()
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")


class OptimizationCache:
    """
    High-performance caching system for optimization results.
    Uses SQLite with connection pooling for thread-safe persistence and in-memory caching for speed.
    """
    
    def __init__(self, db_path: str = "optimization_data.db"):
        """Initialize caching system with connection pooling"""
        self.db_path = db_path
        self.memory_cache = {}
        self.cache_lock = RLock()
        self.max_memory_cache_size = 100
        self.default_ttl_hours = 6
        
        # Initialize connection pool for thread-safe database access
        self.db_pool = DatabaseConnectionPool(db_path, max_connections=5)
        
        self._init_cache_tables()
        self._load_recent_cache()
        
        logger.info("OptimizationCache initialized successfully with connection pooling")
    
    def _init_cache_tables(self):
        """Initialize cache tables in database with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Optimization results cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimization_cache (
                        cache_key TEXT PRIMARY KEY,
                        result_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        hit_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMP
                    )
                """)
                
                # Performance metrics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        duration_ms REAL NOT NULL,
                        success BOOLEAN NOT NULL,
                        cache_hit BOOLEAN DEFAULT FALSE,
                        error_message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_expires 
                    ON optimization_cache(expires_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                    ON performance_metrics(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_session 
                    ON performance_metrics(session_id)
                """)
                
                conn.commit()
                
            # Clean expired entries
            self._cleanup_expired_cache()
            
        except Exception as e:
            logger.error(f"Error initializing cache tables: {e}")
            raise
    
    def _load_recent_cache(self):
        """Load recent cache entries into memory with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT cache_key, result_data, created_at, expires_at, hit_count, last_accessed
                    FROM optimization_cache
                    WHERE expires_at > datetime('now')
                    ORDER BY last_accessed DESC, hit_count DESC
                    LIMIT ?
                """, (self.max_memory_cache_size,))
                
                rows = cursor.fetchall()
                
                with self.cache_lock:
                    for row in rows:
                        try:
                            cache_key = row[0]
                            result_data = json.loads(row[1])
                            created_at = datetime.fromisoformat(row[2])
                            expires_at = datetime.fromisoformat(row[3])
                            hit_count = row[4] or 0
                            last_accessed = datetime.fromisoformat(row[5]) if row[5] else None
                            
                            self.memory_cache[cache_key] = CachedResult(
                                cache_key=cache_key,
                                result_data=result_data,
                                created_at=created_at,
                                expires_at=expires_at,
                                hit_count=hit_count,
                                last_accessed=last_accessed
                            )
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Skipping corrupted cache entry {row[0]}: {e}")
                            continue
                
            logger.info(f"Loaded {len(self.memory_cache)} cache entries into memory")
            
        except Exception as e:
            logger.error(f"Error loading cache into memory: {e}")
            # Don't raise - continue with empty memory cache
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM optimization_cache WHERE expires_at <= datetime('now')")
                deleted_count = cursor.rowcount
                
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
            # Also clean memory cache
            with self.cache_lock:
                now = datetime.now()
                expired_keys = [
                    key for key, cached_result in self.memory_cache.items()
                    if cached_result.expires_at <= now
                ]
                for key in expired_keys:
                    del self.memory_cache[key]
                
                if expired_keys:
                    logger.info(f"Removed {len(expired_keys)} expired entries from memory cache")
                    
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            # Don't raise - cleanup is not critical
    
    def generate_cache_key(self, prompt: str, optimize_for: str = "quality", 
                          user_preferences: Dict = None) -> str:
        """Generate a unique cache key for the request"""
        if user_preferences is None:
            user_preferences = {}
        
        # Create a stable hash of the request parameters
        cache_data = {
            'prompt': prompt.strip().lower(),
            'optimize_for': optimize_for,
            'preferences': sorted(user_preferences.items()) if user_preferences else []
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached optimization result with connection pooling"""
        try:
            # Check memory cache first
            with self.cache_lock:
                if cache_key in self.memory_cache:
                    cached = self.memory_cache[cache_key]
                    
                    # Check if expired
                    if cached.expires_at <= datetime.now():
                        del self.memory_cache[cache_key]
                        return None
                    
                    # Update access statistics
                    cached.hit_count += 1
                    cached.last_accessed = datetime.now()
                    
                    # Update in database asynchronously
                    asyncio.create_task(self._update_cache_stats(cache_key, cached.hit_count))
                    
                    logger.debug(f"Cache hit for key {cache_key[:8]}...")
                    return cached.result_data
            
            # Check database cache with connection pooling
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT result_data, expires_at, hit_count
                    FROM optimization_cache
                    WHERE cache_key = ? AND expires_at > datetime('now')
                """, (cache_key,))
                
                row = cursor.fetchone()
                
                if row:
                    result_data = json.loads(row[0])
                    expires_at = datetime.fromisoformat(row[1])
                    hit_count = row[2] or 0
                    
                    # Update hit count
                    cursor.execute("""
                        UPDATE optimization_cache 
                        SET hit_count = hit_count + 1, last_accessed = datetime('now')
                        WHERE cache_key = ?
                    """, (cache_key,))
                    
                    conn.commit()
                    
                    # Add to memory cache if there's space
                    with self.cache_lock:
                        if len(self.memory_cache) < self.max_memory_cache_size:
                            self.memory_cache[cache_key] = CachedResult(
                                cache_key=cache_key,
                                result_data=result_data,
                                created_at=datetime.now(),
                                expires_at=expires_at,
                                hit_count=hit_count + 1,
                                last_accessed=datetime.now()
                            )
                    
                    logger.debug(f"Database cache hit for key {cache_key[:8]}...")
                    return result_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            return None
    
    async def cache_result(self, cache_key: str, result_data: Dict[str, Any], 
                          ttl_hours: Optional[int] = None) -> bool:
        """Cache optimization result with connection pooling"""
        try:
            if ttl_hours is None:
                ttl_hours = self.default_ttl_hours
            
            now = datetime.now()
            expires_at = now + timedelta(hours=ttl_hours)
            
            # Store in database with connection pooling
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO optimization_cache 
                    (cache_key, result_data, created_at, expires_at, hit_count, last_accessed)
                    VALUES (?, ?, ?, ?, 0, ?)
                """, (
                    cache_key,
                    json.dumps(result_data),
                    now.isoformat(),
                    expires_at.isoformat(),
                    now.isoformat()
                ))
                
                conn.commit()
            
            # Store in memory cache
            with self.cache_lock:
                # Make room if necessary
                if len(self.memory_cache) >= self.max_memory_cache_size:
                    # Remove least recently used
                    lru_key = min(
                        self.memory_cache.keys(),
                        key=lambda k: self.memory_cache[k].last_accessed or datetime.min
                    )
                    del self.memory_cache[lru_key]
                
                self.memory_cache[cache_key] = CachedResult(
                    cache_key=cache_key,
                    result_data=result_data,
                    created_at=now,
                    expires_at=expires_at,
                    hit_count=0,
                    last_accessed=now
                )
            
            logger.debug(f"Cached result for key {cache_key[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            return False
    
    async def _update_cache_stats(self, cache_key: str, hit_count: int):
        """Update cache statistics in database with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE optimization_cache 
                    SET hit_count = ?, last_accessed = datetime('now')
                    WHERE cache_key = ?
                """, (hit_count, cache_key))
                
                conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics with connection pooling"""
        try:
            with self.cache_lock:
                memory_size = len(self.memory_cache)
                memory_hit_count = sum(c.hit_count for c in self.memory_cache.values())
            
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(hit_count) as total_hits,
                        AVG(hit_count) as avg_hits_per_entry,
                        COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as active_entries
                    FROM optimization_cache
                """)
                
                row = cursor.fetchone()
                
                # Calculate hit ratio from performance data
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN cache_hit = 1 THEN 1 END) as cache_hits,
                        COUNT(*) as total_requests
                    FROM performance_metrics
                    WHERE timestamp >= datetime('now', '-24 hours')
                """)
                
                perf_row = cursor.fetchone()
                
                cache_hit_ratio = 0.0
                if perf_row and perf_row[1] > 0:
                    cache_hit_ratio = perf_row[0] / perf_row[1]
                
                stats = {
                    'memory_cache_size': memory_size,
                    'memory_cache_hits': memory_hit_count,
                    'database_total_entries': row[0] or 0,
                    'database_total_hits': row[1] or 0,
                    'database_avg_hits_per_entry': row[2] or 0.0,
                    'database_active_entries': row[3] or 0,
                    'cache_hit_ratio': cache_hit_ratio
                }
                
                return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'memory_cache_size': 0,
                'memory_cache_hits': 0,
                'database_total_entries': 0,
                'database_total_hits': 0,
                'database_avg_hits_per_entry': 0.0,
                'database_active_entries': 0,
                'cache_hit_ratio': 0.0,
                'error': str(e)
            }


class PerformanceMonitor:
    """Performance monitoring and optimization tracker with connection pooling"""
    
    def __init__(self, db_path: str = "optimization_data.db"):
        """Initialize performance monitor with connection pooling"""
        self.db_path = db_path
        self.active_sessions = {}
        self.session_lock = RLock()
        
        # Share connection pool with cache if available, otherwise create new
        self.db_pool = DatabaseConnectionPool(db_path, max_connections=3)
        
        logger.info("PerformanceMonitor initialized successfully with connection pooling")
    
    def start_session(self, session_id: str, operation_type: str) -> float:
        """Start performance tracking session"""
        start_time = time.time()
        
        with self.session_lock:
            self.active_sessions[session_id] = {
                'operation_type': operation_type,
                'start_time': start_time
            }
        
        return start_time
    
    async def end_session(self, session_id: str, success: bool = True, 
                         cache_hit: bool = False, error_message: str = None) -> PerformanceMetrics:
        """End performance tracking session"""
        end_time = time.time()
        
        with self.session_lock:
            session_data = self.active_sessions.pop(session_id, None)
        
        if not session_data:
            logger.warning(f"No active session found for {session_id}")
            return None
        
        start_time = session_data['start_time']
        duration_ms = (end_time - start_time) * 1000
        
        metrics = PerformanceMetrics(
            session_id=session_id,
            operation_type=session_data['operation_type'],
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            cache_hit=cache_hit,
            error_message=error_message
        )
        
        # Store metrics in database
        await self._store_metrics(metrics)
        
        return metrics
    
    async def _store_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics in database with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (id, session_id, operation_type, start_time, end_time, duration_ms, 
                     success, cache_hit, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    metrics.session_id,
                    metrics.operation_type,
                    metrics.start_time,
                    metrics.end_time,
                    metrics.duration_ms,
                    metrics.success,
                    metrics.cache_hit,
                    metrics.error_message
                ))
                
                conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing performance metrics: {e}")
    
    async def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified time period with connection pooling"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        operation_type,
                        COUNT(*) as total_operations,
                        AVG(duration_ms) as avg_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_operations,
                        COUNT(CASE WHEN cache_hit = 1 THEN 1 END) as cache_hits
                    FROM performance_metrics
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY operation_type
                    ORDER BY total_operations DESC
                """.format(hours), )
                
                rows = cursor.fetchall()
                
                summary = {
                    'time_period_hours': hours,
                    'operations': []
                }
                
                total_ops = 0
                total_cache_hits = 0
                
                for row in rows:
                    op_data = {
                        'operation_type': row[0],
                        'total_operations': row[1],
                        'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                        'min_duration_ms': round(row[3], 2) if row[3] else 0,
                        'max_duration_ms': round(row[4], 2) if row[4] else 0,
                        'success_rate': round((row[5] / row[1]) * 100, 1) if row[1] > 0 else 0,
                        'cache_hit_rate': round((row[6] / row[1]) * 100, 1) if row[1] > 0 else 0
                    }
                    
                    summary['operations'].append(op_data)
                    total_ops += row[1]
                    total_cache_hits += row[6]
                
                summary['overall'] = {
                    'total_operations': total_ops,
                    'overall_cache_hit_rate': round((total_cache_hits / total_ops) * 100, 1) if total_ops > 0 else 0
                }
                
                return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {
                'time_period_hours': hours,
                'operations': [],
                'overall': {'total_operations': 0, 'overall_cache_hit_rate': 0},
                'error': str(e)
            }


class OptimizationPerformanceManager:
    """
    Combined performance optimization and caching manager with shared connection pooling.
    Implements Task 1.2.4 requirements.
    """
    
    def __init__(self, db_path: str = "optimization_data.db"):
        """Initialize performance manager with shared connection pooling"""
        # Create shared connection pool for both cache and monitor
        self.db_pool = DatabaseConnectionPool(db_path, max_connections=8)
        
        # Initialize cache and monitor with shared pool
        self.cache = OptimizationCache(db_path)
        self.monitor = PerformanceMonitor(db_path)
        
        # Share the connection pool to avoid creating separate pools
        self.cache.db_pool = self.db_pool
        self.monitor.db_pool = self.db_pool
        
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        logger.info("OptimizationPerformanceManager initialized successfully with shared connection pooling")
    
    async def optimize_with_performance_management(self, 
                                                  optimization_func, 
                                                  prompt: str,
                                                  optimize_for: str = "quality",
                                                  user_preferences: Dict = None) -> Tuple[Any, bool]:
        """
        Execute optimization with performance optimizations and caching
        
        Args:
            optimization_func: The optimization function to execute
            prompt: The prompt to optimize
            optimize_for: Optimization target
            user_preferences: User preferences
            
        Returns:
            Tuple of (result, was_cached)
        """
        session_id = f"opt_{int(time.time() * 1000)}"
        
        # Start performance monitoring
        self.monitor.start_session(session_id, "optimization")
        
        try:
            # Generate cache key
            cache_key = self.cache.generate_cache_key(prompt, optimize_for, user_preferences)
            
            # Check for cached results first
            cached_result = await self.cache.get_cached_result(cache_key)
            
            if cached_result:
                # Cache hit - return cached result
                await self.monitor.end_session(session_id, success=True, cache_hit=True)
                
                # Mark as from cache
                if isinstance(cached_result, dict):
                    cached_result['from_cache'] = True
                
                logger.info(f"Cache hit for optimization session {session_id}")
                return cached_result, True
            
            # Cache miss - execute optimization
            logger.info(f"Cache miss - executing optimization for session {session_id}")
            
            # Execute optimization function
            if asyncio.iscoroutinefunction(optimization_func):
                result = await optimization_func(prompt, optimize_for, user_preferences)
            else:
                # Run in thread pool for CPU-intensive operations
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor, 
                    optimization_func, 
                    prompt, 
                    optimize_for, 
                    user_preferences
                )
            
            # Cache successful results with good confidence
            if hasattr(result, 'confidence') and result.confidence > 0.7:
                # Convert result to dict for caching
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__.copy()
                else:
                    result_dict = result
                
                await self.cache.cache_result(cache_key, result_dict, ttl_hours=6)
                logger.debug(f"Cached optimization result for session {session_id}")
            
            # End performance monitoring
            await self.monitor.end_session(session_id, success=True, cache_hit=False)
            
            return result, False
            
        except Exception as e:
            # End performance monitoring with error
            await self.monitor.end_session(
                session_id, 
                success=False, 
                cache_hit=False, 
                error_message=str(e)
            )
            
            logger.error(f"Error in performance-managed optimization: {e}")
            raise
    
    async def get_system_performance_status(self) -> Dict[str, Any]:
        """Get comprehensive system performance status with improved error handling"""
        try:
            # Get cache stats with error handling
            cache_stats = self.cache.get_cache_stats()
            
            # Get performance summary with error handling
            performance_summary = await self.monitor.get_performance_summary(hours=24)
            
            # Calculate performance targets safely
            avg_durations = [
                op['avg_duration_ms'] for op in performance_summary.get('operations', [])
                if isinstance(op.get('avg_duration_ms'), (int, float))
            ]
            
            avg_processing_time = sum(avg_durations) / len(avg_durations) if avg_durations else 0
            
            # Calculate cache hit rate safely
            cache_hit_rate = cache_stats.get('cache_hit_ratio', 0.0) * 100
            if cache_hit_rate == 0.0 and performance_summary.get('overall', {}).get('overall_cache_hit_rate', 0) > 0:
                # Use overall cache hit rate from performance summary as fallback
                cache_hit_rate = performance_summary['overall']['overall_cache_hit_rate']
            
            # Determine system health
            has_cache_data = cache_stats.get('memory_cache_size', 0) > 0 or cache_stats.get('database_active_entries', 0) > 0
            meets_speed = avg_processing_time < 30000
            meets_cache = cache_hit_rate >= 20.0  # Lower threshold for initial testing
            
            system_health = 'healthy' if (meets_speed and has_cache_data) else 'degraded'
            
            status = {
                'cache_performance': cache_stats,
                'processing_performance': performance_summary,
                'performance_targets': {
                    'target_processing_time_ms': 30000,  # 30 seconds
                    'target_cache_hit_rate': 25.0,  # 25%
                    'target_success_rate': 95.0
                },
                'current_metrics': {
                    'avg_processing_time_ms': round(avg_processing_time, 2),
                    'cache_hit_rate': round(cache_hit_rate, 2),
                    'meets_speed_target': meets_speed,
                    'meets_cache_target': cache_hit_rate >= 25.0
                },
                'system_health': system_health,
                'health_factors': {
                    'has_cache_data': has_cache_data,
                    'meets_speed_target': meets_speed,
                    'meets_cache_target': cache_hit_rate >= 25.0
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system performance status: {e}")
            return {
                'error': str(e),
                'cache_performance': {},
                'processing_performance': {},
                'current_metrics': {
                    'avg_processing_time_ms': 0,
                    'cache_hit_rate': 0.0,
                    'meets_speed_target': False,
                    'meets_cache_target': False
                },
                'system_health': 'error'
            }


# Export main classes
__all__ = [
    'DatabaseConnectionPool',
    'OptimizationCache',
    'PerformanceMonitor', 
    'OptimizationPerformanceManager',
    'CachedResult',
    'PerformanceMetrics'
]


if __name__ == "__main__":
    # Test the performance optimization system
    async def test_performance_system():
        """Test the performance and caching system"""
        manager = OptimizationPerformanceManager()
        
        print("Performance Optimization System Test:")
        print("=" * 50)
        
        # Mock optimization function
        async def mock_optimize(prompt, optimize_for, preferences):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                'original_prompt': prompt,
                'optimized_prompt': f"Optimized: {prompt}",
                'confidence': 0.85,
                'processing_time': 0.1
            }
        
        # Test with caching
        print("\nTesting optimization with caching...")
        
        # First call - should miss cache
        result1, was_cached1 = await manager.optimize_with_performance_management(
            mock_optimize, "Test prompt", "quality"
        )
        print(f"First call - Cached: {was_cached1}")
        
        # Second call - should hit cache
        result2, was_cached2 = await manager.optimize_with_performance_management(
            mock_optimize, "Test prompt", "quality"
        )
        print(f"Second call - Cached: {was_cached2}")
        
        # Get performance status
        status = await manager.get_system_performance_status()
        print(f"\nSystem Status: {status['system_health']}")
        print(f"Cache Hit Rate: {status['current_metrics']['cache_hit_rate']:.1f}%")
        
        # Get cache stats
        cache_stats = manager.cache.get_cache_stats()
        print(f"Memory Cache Size: {cache_stats['memory_cache_size']}")
        print(f"Database Cache Entries: {cache_stats['database_active_entries']}")
        
        print("\nPerformance system test completed!")
    
    # Run test if executed directly
    asyncio.run(test_performance_system())