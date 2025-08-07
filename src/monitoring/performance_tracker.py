import time
import logging
from typing import Callable, Any

from src.config.logging import get_logger

logger = get_logger(__name__)

class PerformanceTracker:
    """
    A simple performance tracker to measure execution time of functions.
    """
    def __init__(self, name: str = "default"):
        self.name = name
        self.start_time = None

    def start(self):
        """Starts the timer."""
        self.start_time = time.perf_counter()
        logger.debug(f"PerformanceTracker '{self.name}' started.")

    def stop(self, message: str = "Execution time"):
        """Stops the timer and logs the elapsed time."""
        if self.start_time is None:
            logger.warning(f"PerformanceTracker '{self.name}' was stopped without being started.")
            return None
        
        end_time = time.perf_counter()
        elapsed_time = end_time - self.start_time
        logger.info(f"{message} for '{self.name}': {elapsed_time:.4f} seconds")
        self.start_time = None # Reset for next use
        return elapsed_time

    async def measure_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Measures the execution time of an async function."""
        self.start()
        try:
            result = await func(*args, **kwargs)
        finally:
            self.stop(f"Async function '{func.__name__}' execution time")
        return result

    def measure_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Measures the execution time of a sync function."""
        self.start()
        try:
            result = func(*args, **kwargs)
        finally:
            self.stop(f"Sync function '{func.__name__}' execution time")
        return result

# Example usage (for demonstration, not part of the core implementation)
async def example_async_function():
    await asyncio.sleep(0.1)
    return "Async done"

def example_sync_function():
    time.sleep(0.05)
    return "Sync done"

if __name__ == "__main__":
    import asyncio
    
    # Sync example
    tracker_sync = PerformanceTracker("sync_example")
    result_sync = tracker_sync.measure_sync(example_sync_function)
    print(f"Sync result: {result_sync}")

    # Async example
    async def run_async_example():
        tracker_async = PerformanceTracker("async_example")
        result_async = await tracker_async.measure_async(example_async_function)
        print(f"Async result: {result_async}")

    asyncio.run(run_async_example())
