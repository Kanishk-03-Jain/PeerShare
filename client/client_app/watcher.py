import time
import logging
from watchdog.observers import Observer
from watchdog.events import DirCreatedEvent, DirDeletedEvent, DirModifiedEvent, DirMovedEvent, FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent, FileSystemEvent, FileSystemEventHandler

logger = logging.getLogger(__name__)

class FileEventHandler(FileSystemEventHandler):
    """Handles file system events and triggers a callback"""
    def __init__(self, callback, debounce_seconds: float = 1.0):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._last_event_time = 0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        current_time = time.time()
        if current_time - self._last_event_time > self.debounce_seconds:
            self._last_event_time = current_time
            logger.info(f"File change detected: {event.event_type} on {event.src_path}")
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error during file change callback: {e}")
    
    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        self.on_any_event(event)
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        self.on_any_event(event)
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        return self.on_any_event(event)
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        return self.on_any_event(event)
