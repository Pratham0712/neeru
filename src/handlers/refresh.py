"""Runs every 15 minutes (EventBridge schedule): new rainfall -> new risk -> alerts."""

import logging

from neeru import engine

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(_event, _context):
    summary = engine.refresh_all()
    log.info("refresh: %s", summary)
    return summary
