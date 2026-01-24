"""
Logging and Metrics System.

Structured logging, performance metrics, and cost tracking for pipeline operations.

Usage:
    >>> from pipeline.metrics import get_logger, MetricsCollector, track_operation
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing sprite", extra={'width': 32, 'height': 32})
    >>>
    >>> with track_operation("sprite_processing") as tracker:
    ...     # Process sprite
    ...     tracker.add_metric('frames_processed', 10)
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from .security import sanitize_for_logging


# ============================================================================
# Structured Logging
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs as JSON objects with consistent fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['data'] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class PipelineLogger(logging.LoggerAdapter):
    """
    Enhanced logger with automatic context and sanitization.

    Automatically sanitizes sensitive data before logging.
    """

    def process(self, msg, kwargs):
        """Process log message and kwargs."""
        # Sanitize extra data
        if 'extra' in kwargs:
            kwargs['extra'] = sanitize_for_logging(kwargs['extra'])

        # Add default context
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        kwargs['extra']['extra_data'] = kwargs.get('extra', {})

        return msg, kwargs


def get_logger(name: str,
               level: int = logging.INFO,
               structured: bool = False,
               log_file: Optional[str] = None) -> PipelineLogger:
    """
    Get a configured pipeline logger.

    Args:
        name: Logger name (typically __name__)
        level: Logging level
        structured: If True, use JSON structured logging
        log_file: Optional file path for logging

    Returns:
        PipelineLogger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing image", extra={'path': 'sprite.png'})
    """
    base_logger = logging.getLogger(name)
    base_logger.setLevel(level)

    # Avoid adding duplicate handlers
    if not base_logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        console_handler.setFormatter(formatter)
        base_logger.addHandler(console_handler)

        # File handler if requested
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            base_logger.addHandler(file_handler)

    return PipelineLogger(base_logger, {})


# ============================================================================
# Metrics Collection
# ============================================================================

class MetricsCollector:
    """
    Collect and track metrics for pipeline operations.

    Tracks processing time, API calls, costs, and custom metrics.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, List[Any]] = {}
        self._timers: Dict[str, float] = {}
        self._costs: Dict[str, float] = {}

    def record_metric(self, name: str, value: Any):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
        """
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append({
            'timestamp': datetime.utcnow().isoformat(),
            'value': value,
        })

    def start_timer(self, name: str):
        """
        Start a named timer.

        Args:
            name: Timer name
        """
        self._timers[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """
        Stop a named timer and record duration.

        Args:
            name: Timer name

        Returns:
            Duration in seconds
        """
        if name not in self._timers:
            return 0.0

        duration = time.time() - self._timers[name]
        self.record_metric(f"{name}_duration_ms", duration * 1000)
        del self._timers[name]
        return duration

    def record_cost(self, provider: str, cost: float, currency: str = "USD"):
        """
        Record API cost.

        Args:
            provider: Provider name
            cost: Cost amount
            currency: Currency code
        """
        key = f"{provider}_{currency}"
        if key not in self._costs:
            self._costs[key] = 0.0
        self._costs[key] += cost

        self.record_metric(f"cost_{provider}", cost)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.

        Returns:
            Dict with all metrics
        """
        return {
            'metrics': self._metrics,
            'costs': self._costs,
            'summary': self._get_summary(),
        }

    def _get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        summary = {}

        for name, values in self._metrics.items():
            if not values:
                continue

            numeric_values = [v['value'] for v in values if isinstance(v['value'], (int, float))]

            if numeric_values:
                summary[name] = {
                    'count': len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values),
                    'total': sum(numeric_values),
                }

        return summary

    def export_json(self, output_path: str):
        """
        Export metrics to JSON file.

        Args:
            output_path: Path to output file
        """
        metrics = self.get_metrics()

        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)

    def clear(self):
        """Clear all metrics."""
        self._metrics.clear()
        self._timers.clear()
        self._costs.clear()


# Global metrics collector
_global_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    return _global_metrics


@contextmanager
def track_operation(operation_name: str,
                   logger: Optional[PipelineLogger] = None,
                   metrics: Optional[MetricsCollector] = None):
    """
    Context manager to track operation timing and log results.

    Args:
        operation_name: Name of operation
        logger: Optional logger for logging
        metrics: Optional metrics collector

    Yields:
        OperationTracker instance

    Example:
        >>> with track_operation("sprite_processing") as tracker:
        ...     # Process sprite
        ...     tracker.add_metric('frames', 10)
        ...     tracker.add_cost('pollinations', 0.01)
    """
    if logger is None:
        logger = get_logger(__name__)

    if metrics is None:
        metrics = get_metrics_collector()

    tracker = OperationTracker(operation_name, logger, metrics)

    logger.info(f"Starting operation: {operation_name}")
    start_time = time.time()

    try:
        yield tracker
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Operation failed: {operation_name}",
            extra={'duration_ms': duration * 1000, 'error': str(e)}
        )
        raise
    else:
        duration = time.time() - start_time
        logger.info(
            f"Operation completed: {operation_name}",
            extra={'duration_ms': duration * 1000, **tracker.get_data()}
        )
        metrics.record_metric(f"{operation_name}_duration_ms", duration * 1000)


class OperationTracker:
    """
    Tracks metrics and costs for a single operation.

    Used within track_operation context manager.
    """

    def __init__(self,
                 operation_name: str,
                 logger: PipelineLogger,
                 metrics: MetricsCollector):
        """Initialize operation tracker."""
        self.operation_name = operation_name
        self.logger = logger
        self.metrics = metrics
        self._data: Dict[str, Any] = {}

    def add_metric(self, name: str, value: Any):
        """Add a metric for this operation."""
        self._data[name] = value
        self.metrics.record_metric(f"{self.operation_name}_{name}", value)

    def add_cost(self, provider: str, cost: float, currency: str = "USD"):
        """Add a cost for this operation."""
        self._data[f"cost_{provider}"] = cost
        self.metrics.record_cost(provider, cost, currency)

    def get_data(self) -> Dict[str, Any]:
        """Get all tracked data."""
        return self._data.copy()


# ============================================================================
# Cost Tracking
# ============================================================================

class CostTracker:
    """
    Track API costs and budget limits.

    Prevents exceeding budget by tracking costs across providers.
    """

    def __init__(self, budget_limit: Optional[float] = None):
        """
        Initialize cost tracker.

        Args:
            budget_limit: Maximum total cost allowed (USD)
        """
        self.budget_limit = budget_limit
        self._provider_costs: Dict[str, float] = {}
        self._total_cost = 0.0
        self._transactions: List[Dict[str, Any]] = []

    def add_cost(self,
                 provider: str,
                 cost: float,
                 description: str = "",
                 metadata: Optional[Dict] = None):
        """
        Add a cost transaction.

        Args:
            provider: Provider name
            cost: Cost amount (USD)
            description: Description of the transaction
            metadata: Additional transaction data

        Raises:
            ValueError: Would exceed budget limit
        """
        # Check budget
        if self.budget_limit and (self._total_cost + cost) > self.budget_limit:
            raise ValueError(
                f"Cost ${cost:.4f} would exceed budget limit "
                f"${self.budget_limit:.2f} (current: ${self._total_cost:.2f})"
            )

        # Record transaction
        transaction = {
            'timestamp': datetime.utcnow().isoformat(),
            'provider': provider,
            'cost': cost,
            'description': description,
            'metadata': metadata or {},
        }
        self._transactions.append(transaction)

        # Update totals
        if provider not in self._provider_costs:
            self._provider_costs[provider] = 0.0
        self._provider_costs[provider] += cost
        self._total_cost += cost

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            'total_cost': self._total_cost,
            'budget_limit': self.budget_limit,
            'remaining_budget': (self.budget_limit - self._total_cost) if self.budget_limit else None,
            'provider_costs': self._provider_costs.copy(),
            'transaction_count': len(self._transactions),
        }

    def get_transactions(self) -> List[Dict[str, Any]]:
        """Get all transactions."""
        return self._transactions.copy()

    def export_report(self, output_path: str):
        """
        Export cost report to JSON.

        Args:
            output_path: Path to output file
        """
        report = {
            'summary': self.get_summary(),
            'transactions': self._transactions,
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)


# ============================================================================
# Performance Profiler
# ============================================================================

class PerformanceProfiler:
    """
    Profile pipeline performance with detailed timing breakdowns.
    """

    def __init__(self):
        """Initialize performance profiler."""
        self._stages: List[Dict[str, Any]] = []
        self._current_stage = None
        self._start_time = None

    def start(self):
        """Start profiling."""
        self._start_time = time.time()
        self._stages.clear()

    def start_stage(self, name: str, metadata: Optional[Dict] = None):
        """
        Start timing a pipeline stage.

        Args:
            name: Stage name
            metadata: Additional stage metadata
        """
        if self._current_stage:
            self.end_stage()

        self._current_stage = {
            'name': name,
            'start_time': time.time(),
            'metadata': metadata or {},
        }

    def end_stage(self):
        """End current stage timing."""
        if not self._current_stage:
            return

        self._current_stage['end_time'] = time.time()
        self._current_stage['duration_ms'] = (
            (self._current_stage['end_time'] - self._current_stage['start_time']) * 1000
        )

        self._stages.append(self._current_stage)
        self._current_stage = None

    def get_report(self) -> Dict[str, Any]:
        """
        Get performance report.

        Returns:
            Dict with timing breakdown
        """
        if self._current_stage:
            self.end_stage()

        total_time = time.time() - self._start_time if self._start_time else 0

        return {
            'total_duration_ms': total_time * 1000,
            'stages': self._stages,
            'stage_count': len(self._stages),
        }

    def print_report(self):
        """Print performance report to console."""
        report = self.get_report()

        print(f"\n{'='*60}")
        print(f"Performance Report")
        print(f"{'='*60}")
        print(f"Total Duration: {report['total_duration_ms']:.2f}ms")
        print(f"Stages: {report['stage_count']}")
        print(f"{'-'*60}")

        for stage in report['stages']:
            print(f"  {stage['name']}: {stage['duration_ms']:.2f}ms")
            if stage['metadata']:
                for key, value in stage['metadata'].items():
                    print(f"    {key}: {value}")

        print(f"{'='*60}\n")
