"""Retry utilities with circuit breaker pattern."""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Callable, Optional, Type, Union
from functools import wraps

from loguru import logger
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)

from .exceptions import RetryableError, TemporaryError, RateLimitError, TimeoutError


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time to wait before trying half-open
            expected_exception: Exception type to count as failure
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN - rejecting call")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return datetime.now() - self.last_failure_time >= timedelta(seconds=self.timeout)
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker: resetting to CLOSED after successful call")
            self.state = CircuitState.CLOSED
        
        self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"Circuit breaker: OPENING after {self.failure_count} failures")
                self.state = CircuitState.OPEN


class RetryManager:
    """Manages retry logic with different strategies."""
    
    def __init__(self):
        """Initialize retry manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a named resource.
        
        Args:
            name: Name of the resource/service
            
        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        
        return self.circuit_breakers[name]
    
    @staticmethod
    def retry_with_backoff(
        max_attempts: int = 3,
        min_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """Create retry decorator with exponential backoff.
        
        Args:
            max_attempts: Maximum number of retry attempts
            min_delay: Minimum delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for exponential backoff
            
        Returns:
            Retry decorator
        """
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_delay,
                min=min_delay,
                max=max_delay,
                exp_base=backoff_factor
            ),
            retry=retry_if_exception_type((
                RetryableError,
                TemporaryError,
                RateLimitError,
                TimeoutError,
                ConnectionError,
                asyncio.TimeoutError
            )),
            before_sleep=before_sleep_log(logger, "WARNING")
        )
    
    @staticmethod
    def retry_on_rate_limit(max_attempts: int = 5, base_delay: float = 30.0):
        """Create retry decorator specifically for rate limiting.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay for rate limiting
            
        Returns:
            Retry decorator
        """
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=base_delay,
                min=base_delay,
                max=300.0,  # 5 minutes max
                exp_base=2.0
            ),
            retry=retry_if_exception_type(RateLimitError),
            before_sleep=before_sleep_log(logger, "WARNING", exc_info=True)
        )
    
    async def execute_with_retry(
        self,
        func: Callable,
        circuit_breaker_name: Optional[str] = None,
        max_attempts: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry and optional circuit breaker.
        
        Args:
            func: Function to execute
            circuit_breaker_name: Name for circuit breaker (optional)
            max_attempts: Maximum retry attempts
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        # Apply circuit breaker if requested
        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
            func = circuit_breaker(func)
        
        # Apply retry decorator
        retry_decorator = self.retry_with_backoff(max_attempts=max_attempts)
        retried_func = retry_decorator(func)
        
        # Execute function
        return await retried_func(*args, **kwargs)


class RateLimiter:
    """Rate limiter to control request frequency."""
    
    def __init__(self, max_requests: int = 10, time_window: float = 60.0):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request.
        
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            # Check if we can make a new request
            if len(self.requests) >= self.max_requests:
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request)
                
                logger.warning(f"Rate limit exceeded. Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
                # Try again after waiting
                return await self.acquire()
            
            # Record the new request
            self.requests.append(now)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


# Global retry manager instance
retry_manager = RetryManager()


# Convenience decorators
def with_retry(max_attempts: int = 3, circuit_breaker: Optional[str] = None):
    """Convenience decorator for retry with optional circuit breaker.
    
    Args:
        max_attempts: Maximum retry attempts
        circuit_breaker: Circuit breaker name (optional)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_manager.execute_with_retry(
                func, circuit_breaker, max_attempts, *args, **kwargs
            )
        return wrapper
    return decorator


def with_rate_limit(max_requests: int = 10, time_window: float = 60.0):
    """Decorator to apply rate limiting to a function.
    
    Args:
        max_requests: Maximum requests per time window
        time_window: Time window in seconds
        
    Returns:
        Decorator function
    """
    rate_limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with rate_limiter:
                return await func(*args, **kwargs)
        return wrapper
    return decorator