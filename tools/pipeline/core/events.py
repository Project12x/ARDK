"""
Pipeline Events - For GUI Progress Updates.

This module provides an event system that allows the GUI (or any listener)
to receive updates about pipeline progress without tight coupling.

Usage:
    from tools.pipeline.core import Pipeline, PipelineConfig, EventEmitter

    # Create event handler
    def on_progress(event):
        print(f"Progress: {event.percent}% - {event.message}")

    # Create pipeline with event emitter
    emitter = EventEmitter()
    emitter.on('progress', on_progress)

    config = PipelineConfig(dry_run=False)
    pipeline = Pipeline(config, event_emitter=emitter)

    # Events will be emitted during processing
    result = pipeline.process('sprite.png', 'output/')
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List, Callable
from enum import Enum, auto
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of pipeline events."""
    # Progress events
    PROGRESS = auto()           # Overall progress update
    STAGE_START = auto()        # Stage started
    STAGE_COMPLETE = auto()     # Stage completed
    STAGE_SKIP = auto()         # Stage skipped

    # Status events
    PIPELINE_START = auto()     # Pipeline started
    PIPELINE_COMPLETE = auto()  # Pipeline completed
    PIPELINE_ERROR = auto()     # Pipeline error

    # Generation events
    GENERATION_START = auto()   # AI generation started
    GENERATION_POLL = auto()    # Polling for async job
    GENERATION_COMPLETE = auto() # AI generation complete
    GENERATION_CACHED = auto()  # Result loaded from cache

    # Safeguard events
    BUDGET_WARNING = auto()     # Budget running low
    BUDGET_EXHAUSTED = auto()   # Budget exhausted
    CONFIRMATION_REQUIRED = auto()  # User confirmation needed
    DRY_RUN_BLOCKED = auto()    # Operation blocked by dry-run

    # Aseprite events
    ASEPRITE_EXPORT = auto()    # Exporting from Aseprite
    ASEPRITE_PARSE = auto()     # Parsing Aseprite JSON

    # Processing events
    SPRITE_DETECTED = auto()    # Sprite detected
    SPRITE_PROCESSED = auto()   # Sprite processed
    PALETTE_EXTRACTED = auto()  # Palette extracted
    TILE_OPTIMIZED = auto()     # Tile optimization result


@dataclass
class PipelineEvent:
    """Base event class."""
    type: EventType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressEvent(PipelineEvent):
    """Progress update event."""
    percent: float = 0.0
    message: str = ""
    stage: str = ""
    stage_percent: float = 0.0

    def __post_init__(self):
        self.type = EventType.PROGRESS


@dataclass
class StageEvent(PipelineEvent):
    """Stage lifecycle event."""
    stage_name: str = ""
    stage_index: int = 0
    total_stages: int = 0
    result: Any = None
    error: Optional[str] = None


@dataclass
class ErrorEvent(PipelineEvent):
    """Error event."""
    error_type: str = ""
    message: str = ""
    recoverable: bool = True
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.type = EventType.PIPELINE_ERROR


@dataclass
class GenerationEvent(PipelineEvent):
    """Generation-related event."""
    description: str = ""
    provider: str = ""
    cost_usd: float = 0.0
    cached: bool = False
    poll_attempt: int = 0
    max_attempts: int = 0


@dataclass
class SafeguardEvent(PipelineEvent):
    """Safeguard-related event."""
    safeguard_type: str = ""
    message: str = ""
    remaining_budget: Optional[Dict[str, Any]] = None


class EventEmitter:
    """
    Event emitter for pipeline progress updates.

    Allows registering callbacks for specific event types.
    Thread-safe for use with async operations.
    """

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = {}
        self._all_listeners: List[Callable] = []

    def on(self, event_type: EventType, callback: Callable):
        """Register a callback for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        return self  # For chaining

    def on_all(self, callback: Callable):
        """Register a callback for all events."""
        self._all_listeners.append(callback)
        return self

    def off(self, event_type: EventType, callback: Callable):
        """Unregister a callback."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]

    def emit(self, event: PipelineEvent):
        """Emit an event to all registered listeners."""
        # Call specific listeners
        if event.type in self._listeners:
            for callback in self._listeners[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event listener error: {e}")

        # Call all-event listeners
        for callback in self._all_listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

    def emit_progress(
        self,
        percent: float,
        message: str,
        stage: str = "",
        stage_percent: float = 0.0
    ):
        """Convenience method to emit a progress event."""
        self.emit(ProgressEvent(
            type=EventType.PROGRESS,
            percent=percent,
            message=message,
            stage=stage,
            stage_percent=stage_percent,
        ))

    def emit_stage_start(self, stage_name: str, stage_index: int, total: int):
        """Emit a stage start event."""
        self.emit(StageEvent(
            type=EventType.STAGE_START,
            stage_name=stage_name,
            stage_index=stage_index,
            total_stages=total,
        ))

    def emit_stage_complete(
        self,
        stage_name: str,
        stage_index: int,
        total: int,
        result: Any = None
    ):
        """Emit a stage complete event."""
        self.emit(StageEvent(
            type=EventType.STAGE_COMPLETE,
            stage_name=stage_name,
            stage_index=stage_index,
            total_stages=total,
            result=result,
        ))

    def emit_error(
        self,
        error_type: str,
        message: str,
        recoverable: bool = True,
        details: Optional[Dict] = None
    ):
        """Emit an error event."""
        self.emit(ErrorEvent(
            error_type=error_type,
            message=message,
            recoverable=recoverable,
            details=details,
        ))


class ConsoleEventHandler:
    """
    Default event handler that prints to console.

    Used by CLI when no custom handler is provided.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def __call__(self, event: PipelineEvent):
        """Handle an event."""
        if isinstance(event, ProgressEvent):
            self._handle_progress(event)
        elif isinstance(event, StageEvent):
            self._handle_stage(event)
        elif isinstance(event, ErrorEvent):
            self._handle_error(event)
        elif self.verbose:
            print(f"[{event.type.name}] {event.data}")

    def _handle_progress(self, event: ProgressEvent):
        """Handle progress event."""
        bar_width = 30
        filled = int(bar_width * event.percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r[{bar}] {event.percent:5.1f}% {event.message}", end="", flush=True)
        if event.percent >= 100:
            print()  # New line at completion

    def _handle_stage(self, event: StageEvent):
        """Handle stage event."""
        if event.type == EventType.STAGE_START:
            print(f"\n[{event.stage_index}/{event.total_stages}] {event.stage_name}...")
        elif event.type == EventType.STAGE_COMPLETE:
            print(f"      Done.")

    def _handle_error(self, event: ErrorEvent):
        """Handle error event."""
        prefix = "[WARN]" if event.recoverable else "[ERROR]"
        print(f"\n{prefix} {event.error_type}: {event.message}")
