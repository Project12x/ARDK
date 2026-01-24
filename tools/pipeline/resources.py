"""
Resource Management Module.

Context managers and utilities for proper resource cleanup, memory
management, and temporary file handling.

Usage:
    >>> from pipeline.resources import TempFileManager, ImagePool
    >>> with TempFileManager() as tmp:
    ...     temp_path = tmp.create("sprite.png")
    ...     # File automatically cleaned up on exit
    >>>
    >>> with ImagePool(max_size_mb=100) as pool:
    ...     img1 = pool.load("sprite1.png")
    ...     img2 = pool.load("sprite2.png")
    ...     # Images automatically closed on exit
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from contextlib import contextmanager
import tempfile
import shutil
import os
import psutil
from PIL import Image

from .errors import MemoryError as PipelineMemoryError, DiskSpaceError


class TempFileManager:
    """
    Context manager for temporary file management.

    Automatically creates and cleans up temporary files/directories.

    Usage:
        >>> with TempFileManager() as tmp:
        ...     temp_file = tmp.create("output.png")
        ...     temp_dir = tmp.create_dir("processing")
        ...     # Files/dirs automatically deleted on exit
    """

    def __init__(self, prefix: str = "pipeline_", cleanup: bool = True):
        """
        Initialize temp file manager.

        Args:
            prefix: Prefix for temp files/dirs
            cleanup: If True, cleanup on exit (set False for debugging)
        """
        self.prefix = prefix
        self.cleanup = cleanup
        self._temp_files: List[Path] = []
        self._temp_dirs: List[Path] = []

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup."""
        if self.cleanup:
            self.cleanup_all()

    def create(self, suffix: str = "", dir: str = None) -> Path:
        """
        Create a temporary file.

        Args:
            suffix: File suffix/extension (e.g., ".png")
            dir: Directory to create file in (None = system temp)

        Returns:
            Path to temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=self.prefix, dir=dir)
        os.close(fd)  # Close file descriptor
        path_obj = Path(path)
        self._temp_files.append(path_obj)
        return path_obj

    def create_dir(self, suffix: str = "", dir: str = None) -> Path:
        """
        Create a temporary directory.

        Args:
            suffix: Directory suffix
            dir: Parent directory (None = system temp)

        Returns:
            Path to temporary directory
        """
        path = tempfile.mkdtemp(suffix=suffix, prefix=self.prefix, dir=dir)
        path_obj = Path(path)
        self._temp_dirs.append(path_obj)
        return path_obj

    def cleanup_all(self):
        """Remove all temporary files and directories."""
        # Remove files
        for path in self._temp_files:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        # Remove directories
        for path in self._temp_dirs:
            try:
                if path.exists():
                    shutil.rmtree(path)
            except Exception:
                pass

        self._temp_files.clear()
        self._temp_dirs.clear()


class ImagePool:
    """
    Context manager for managing multiple images with memory limits.

    Tracks loaded images and ensures total memory usage stays within limits.

    Usage:
        >>> with ImagePool(max_size_mb=100) as pool:
        ...     img1 = pool.load("sprite1.png")
        ...     img2 = pool.load("sprite2.png")
        ...     # All images automatically closed on exit
    """

    def __init__(self, max_size_mb: float = 500):
        """
        Initialize image pool.

        Args:
            max_size_mb: Maximum total memory for images (MB)
        """
        self.max_size_mb = max_size_mb
        self._images: Dict[str, Image.Image] = {}
        self._sizes_mb: Dict[str, float] = {}
        self._total_mb = 0.0

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and close all images."""
        self.close_all()

    def load(self, path: str, key: str = None) -> Image.Image:
        """
        Load an image and add to pool.

        Args:
            path: Path to image file
            key: Optional key (defaults to path)

        Returns:
            PIL Image object

        Raises:
            PipelineMemoryError: Would exceed memory limit
        """
        key = key or path

        # If already loaded, return cached
        if key in self._images:
            return self._images[key]

        # Load image
        img = Image.open(path)

        # Estimate memory usage (width * height * bytes_per_pixel)
        bytes_per_pixel = len(img.mode)  # Rough estimate
        size_bytes = img.width * img.height * bytes_per_pixel
        size_mb = size_bytes / (1024 * 1024)

        # Check if adding would exceed limit
        if self._total_mb + size_mb > self.max_size_mb:
            raise PipelineMemoryError(
                operation="image pool",
                required_mb=size_mb
            )

        # Add to pool
        self._images[key] = img
        self._sizes_mb[key] = size_mb
        self._total_mb += size_mb

        return img

    def close(self, key: str):
        """Close and remove a specific image from pool."""
        if key in self._images:
            self._images[key].close()
            self._total_mb -= self._sizes_mb[key]
            del self._images[key]
            del self._sizes_mb[key]

    def close_all(self):
        """Close and remove all images from pool."""
        for img in self._images.values():
            try:
                img.close()
            except Exception:
                pass

        self._images.clear()
        self._sizes_mb.clear()
        self._total_mb = 0.0

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        return {
            'total_mb': self._total_mb,
            'max_mb': self.max_size_mb,
            'used_percent': (self._total_mb / self.max_size_mb * 100) if self.max_size_mb > 0 else 0,
            'image_count': len(self._images),
        }


class FileWriter:
    """
    Context manager for safe file writing with atomic operations.

    Writes to a temporary file first, then atomically moves to destination
    on successful completion. Prevents partial/corrupt files on errors.

    Usage:
        >>> with FileWriter("output.png") as writer:
        ...     img.save(writer.temp_path)
        ...     # File atomically moved to output.png on exit
    """

    def __init__(self, output_path: str, check_disk_space: bool = True):
        """
        Initialize file writer.

        Args:
            output_path: Final destination path
            check_disk_space: If True, check available disk space
        """
        self.output_path = Path(output_path)
        self.temp_path = None
        self.check_disk_space = check_disk_space
        self._temp_fd = None

    def __enter__(self):
        """Enter context and create temp file."""
        # Create parent directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check disk space if requested
        if self.check_disk_space:
            # Estimate required space (10MB default)
            required_mb = 10.0
            self._check_space(required_mb)

        # Create temp file in same directory (for atomic move)
        self._temp_fd, temp_path = tempfile.mkstemp(
            dir=self.output_path.parent,
            prefix=f".tmp_{self.output_path.name}_"
        )
        self.temp_path = Path(temp_path)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and move temp file to destination."""
        # Close file descriptor
        if self._temp_fd is not None:
            os.close(self._temp_fd)

        # If no exception, move temp file to destination
        if exc_type is None and self.temp_path and self.temp_path.exists():
            try:
                # Atomic move (same filesystem)
                self.temp_path.replace(self.output_path)
            except Exception:
                # Fallback to copy+delete
                shutil.copy2(self.temp_path, self.output_path)
                self.temp_path.unlink()
        else:
            # Clean up temp file on error
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except Exception:
                    pass

    def _check_space(self, required_mb: float):
        """Check available disk space."""
        stat = shutil.disk_usage(self.output_path.parent)
        available_mb = stat.free / (1024 * 1024)

        if available_mb < required_mb:
            raise DiskSpaceError(required_mb, available_mb)


@contextmanager
def memory_limit(operation: str, max_mb: float = 500):
    """
    Context manager to monitor memory usage during operation.

    Raises error if operation would use too much memory.

    Args:
        operation: Name of operation (for error messages)
        max_mb: Maximum memory allowed (MB)

    Raises:
        PipelineMemoryError: Memory limit exceeded

    Usage:
        >>> with memory_limit("image processing", max_mb=100):
        ...     # Process images
        ...     pass
    """
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 * 1024)

    try:
        yield
    finally:
        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_used = mem_after - mem_before

        if mem_used > max_mb:
            raise PipelineMemoryError(operation, mem_used)


@contextmanager
def safe_file_operation(path: str, mode: str = 'r'):
    """
    Context manager for safe file operations with proper cleanup.

    Args:
        path: File path
        mode: Open mode ('r', 'w', 'rb', 'wb', etc.)

    Yields:
        File handle

    Usage:
        >>> with safe_file_operation("data.bin", "rb") as f:
        ...     data = f.read()
    """
    f = None
    try:
        f = open(path, mode)
        yield f
    finally:
        if f is not None:
            try:
                f.close()
            except Exception:
                pass


class ResourceMonitor:
    """
    Monitor system resources during pipeline operations.

    Tracks memory, disk usage, and processing time.
    """

    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process()
        self._snapshots: List[Dict[str, Any]] = []

    def snapshot(self, label: str = ""):
        """
        Take a snapshot of current resource usage.

        Args:
            label: Optional label for this snapshot
        """
        mem_info = self.process.memory_info()
        cpu_percent = self.process.cpu_percent()

        snapshot = {
            'label': label,
            'memory_mb': mem_info.rss / (1024 * 1024),
            'memory_percent': self.process.memory_percent(),
            'cpu_percent': cpu_percent,
        }

        self._snapshots.append(snapshot)

    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics from all snapshots."""
        if not self._snapshots:
            return {}

        memory_values = [s['memory_mb'] for s in self._snapshots]

        return {
            'snapshot_count': len(self._snapshots),
            'memory': {
                'min_mb': min(memory_values),
                'max_mb': max(memory_values),
                'avg_mb': sum(memory_values) / len(memory_values),
            },
            'snapshots': self._snapshots,
        }

    def clear(self):
        """Clear all snapshots."""
        self._snapshots.clear()


def check_system_resources(required_memory_mb: float = 100,
                           required_disk_mb: float = 100,
                           output_dir: str = ".") -> Dict[str, Any]:
    """
    Check if system has sufficient resources for operation.

    Args:
        required_memory_mb: Required available memory (MB)
        required_disk_mb: Required disk space (MB)
        output_dir: Directory to check disk space

    Returns:
        Dict with resource availability info

    Raises:
        PipelineMemoryError: Insufficient memory
        DiskSpaceError: Insufficient disk space
    """
    # Check memory
    mem = psutil.virtual_memory()
    available_mem_mb = mem.available / (1024 * 1024)

    if available_mem_mb < required_memory_mb:
        raise PipelineMemoryError(
            operation="system check",
            required_mb=required_memory_mb
        )

    # Check disk space
    disk = shutil.disk_usage(output_dir)
    available_disk_mb = disk.free / (1024 * 1024)

    if available_disk_mb < required_disk_mb:
        raise DiskSpaceError(required_disk_mb, available_disk_mb)

    return {
        'memory': {
            'available_mb': available_mem_mb,
            'required_mb': required_memory_mb,
            'sufficient': available_mem_mb >= required_memory_mb,
        },
        'disk': {
            'available_mb': available_disk_mb,
            'required_mb': required_disk_mb,
            'sufficient': available_disk_mb >= required_disk_mb,
        },
    }
