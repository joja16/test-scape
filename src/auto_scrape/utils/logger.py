"""Logging configuration and utilities."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ..core.config import LoggingConfig


class LoggerSetup:
    """Handles logger configuration and setup."""
    
    @staticmethod
    def setup_logger(config: LoggingConfig) -> None:
        """Setup logger with configuration.
        
        Args:
            config: Logging configuration
        """
        # Remove default logger
        logger.remove()
        
        # Create log directory if it doesn't exist
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add console handler
        logger.add(
            sys.stdout,
            level=config.level.value,
            format=config.format,
            colorize=True,
            enqueue=True
        )
        
        # Add file handler
        logger.add(
            config.file_path,
            level=config.level.value,
            format=config.format,
            rotation=config.max_file_size,
            retention=config.backup_count,
            compression="zip",
            enqueue=True
        )
        
        logger.info("Logger initialized successfully")
    
    @staticmethod
    def log_scraping_session(
        site_name: str,
        items_scraped: int,
        duration: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log scraping session results.
        
        Args:
            site_name: Name of the site scraped
            items_scraped: Number of items scraped
            duration: Duration in seconds
            success: Whether scraping was successful
            error_message: Error message if failed
        """
        if success:
            logger.info(
                f"✓ {site_name}: {items_scraped} items in {duration:.2f}s"
            )
        else:
            logger.error(
                f"✗ {site_name}: Failed after {duration:.2f}s - {error_message or 'Unknown error'}"
            )
    
    @staticmethod
    def log_performance_metrics(
        total_sites: int,
        successful_sites: int,
        total_items: int,
        total_duration: float,
        avg_items_per_second: float
    ) -> None:
        """Log performance metrics.
        
        Args:
            total_sites: Total number of sites processed
            successful_sites: Number of successfully scraped sites
            total_items: Total items scraped
            total_duration: Total duration in seconds
            avg_items_per_second: Average items per second
        """
        success_rate = (successful_sites / total_sites * 100) if total_sites > 0 else 0
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE METRICS")
        logger.info("=" * 60)
        logger.info(f"Sites processed: {successful_sites}/{total_sites} ({success_rate:.1f}% success)")
        logger.info(f"Total items scraped: {total_items}")
        logger.info(f"Total duration: {total_duration:.2f}s")
        logger.info(f"Average speed: {avg_items_per_second:.2f} items/second")
        logger.info("=" * 60)