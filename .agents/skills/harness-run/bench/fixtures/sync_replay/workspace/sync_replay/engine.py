"""Ordered replication; the checkpoint is a page acknowledgement."""
import logging
logger = logging.getLogger(__name__)


class SyncEngine:
    def __init__(self, source, sink, checkpoint, page_size=100):
        self.source, self.sink, self.checkpoint = source, sink, checkpoint
        self.page_size = page_size

    def run(self):
        cursor = self.checkpoint.load()
        applied = 0
        page_count = 0
        logger.info("sync_start")
        while True:
            events, next_cursor = self.source.fetch(cursor)
            if not events:
                break
            if next_cursor is not None:
                self.checkpoint.save(next_cursor)
            for event in events:
                if self.sink.apply(event):
                    applied += 1
            if next_cursor is not None:
                self.checkpoint.save(next_cursor)
            page_count += 1
            logger.debug("page_ack pages=%d events=%d applied=%d",
                         page_count, len(events), applied)
            if next_cursor is None:
                break
            cursor = next_cursor
        logger.info("sync_done pages=%d applied=%d", page_count, applied)
        return applied
