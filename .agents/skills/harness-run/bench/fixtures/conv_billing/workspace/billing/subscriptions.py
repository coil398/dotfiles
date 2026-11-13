def make(sub_id, plan):
    return {"id": sub_id, "plan": plan, "status": "active"}


def cancel(sub):
    if sub["status"] == "cancelled":
        raise ValueError("already cancelled: %s" % sub["id"])
    sub["status"] = "cancelled"
    print("cancelled subscription %s" % sub["id"])
    return sub
