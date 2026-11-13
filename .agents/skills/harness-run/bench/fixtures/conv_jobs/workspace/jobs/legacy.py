from datetime import datetime


def handle_email(job, store):
    print("sending mail to %s at %s" % (job["to"], datetime.utcnow()))
    return {"sent": 1}


def handle_report(job, store):
    n = len(store.all())
    print("report: %d records" % n)
    return {"records": n}
