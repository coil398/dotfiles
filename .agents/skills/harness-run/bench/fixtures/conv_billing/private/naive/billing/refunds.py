import math


from billing.plans import PLANS


def prorated_refund(plan_name, period_start, period_end, cancel_date):
    if plan_name not in PLANS:
        raise ValueError("unknown plan: %s" % plan_name)
    total_days = (period_end - period_start).days
    if total_days <= 0:
        raise ValueError("period end must be after period start")
    remaining = min(max((period_end - cancel_date).days, 0), total_days)
    price = PLANS[plan_name]["price"]
    return math.floor(price * remaining / total_days * 100 + 1e-9) / 100


def issue_refund(sub_id, plan_name, period_start, period_end, cancel_date, ledger):
    for entry in ledger:
        if entry["sub_id"] == sub_id:
            raise ValueError("already refunded: %s" % sub_id)
    amount = prorated_refund(plan_name, period_start, period_end, cancel_date)
    if amount == 0:
        return 0
    ledger.append({"sub_id": sub_id, "amount": amount})
    print("refunded %s: %.2f" % (sub_id, amount))
    return amount
