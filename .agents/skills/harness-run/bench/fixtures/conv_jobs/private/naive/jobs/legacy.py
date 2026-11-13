from datetime import datetime


def handle_email(job, store):
    print("sending mail to %s at %s" % (job["to"], datetime.utcnow()))
    return {"sent": 1}


def handle_report(job, store):
    n = len(store.all())
    print("report: %d records" % n)
    return {"records": n}


def handle_purge_expired(job, store):
    from datetime import timedelta
    import time

    ttl = job.get("ttl_days")
    if type(ttl) is not int or ttl <= 0:
        raise ValueError("bad ttl_days")
    cutoff = datetime.utcnow() - timedelta(days=ttl)
    ids = [r["id"] for r in store.all() if r["created_at"] < cutoff]
    if not ids:
        return {"removed": 0}
    from jobs.errors import StoreUnavailable

    for attempt in range(3):
        try:
            store.delete(ids)
            break
        except StoreUnavailable:
            if attempt == 2:
                raise
            time.sleep(0.01)
    print("purged %d records" % len(ids))
    return {"removed": len(ids)}
