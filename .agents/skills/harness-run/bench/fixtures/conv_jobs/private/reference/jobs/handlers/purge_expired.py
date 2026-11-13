from datetime import timedelta

from jobs import clock
from jobs import metrics
from jobs.registry import register
from jobs.retry import retry


@retry(attempts=3)
def _delete(store, ids):
    store.delete(ids)


@register("purge_expired")
def handle(job, store):
    metrics.incr("jobs.purge_expired.runs")
    try:
        ttl_days = job["ttl_days"]
        if type(ttl_days) is not int or ttl_days <= 0:
            raise ValueError("ttl_days must be a positive int")
        cutoff = clock.now() - timedelta(days=ttl_days)
        ids = [r["id"] for r in store.all() if r["created_at"] < cutoff]
        if ids:
            _delete(store, ids)
    except Exception:
        metrics.incr("jobs.purge_expired.failures")
        raise
    metrics.incr("jobs.purge_expired.items", len(ids))
    return {"removed": len(ids)}
