"""Prorated refunds for cancelled subscriptions."""
from billing.errors import ConflictError
from billing.errors import InvalidInputError
from billing.errors import NotFoundError
from billing.log import get_logger
from billing.plans import PLANS

log = get_logger(__name__)


def prorated_refund(plan_name, period_start, period_end, cancel_date):
    if plan_name not in PLANS:
        raise NotFoundError(f"unknown plan: {plan_name}")
    total_days = (period_end - period_start).days
    if total_days <= 0:
        raise InvalidInputError("period end must be after period start")
    price_cents = round(PLANS[plan_name]["price"] * 100)
    remaining = min(max((period_end - cancel_date).days, 0), total_days)
    return price_cents * remaining // total_days


def issue_refund(sub_id, plan_name, period_start, period_end, cancel_date, ledger):
    if any(entry["sub_id"] == sub_id for entry in ledger):
        raise ConflictError(f"already refunded: {sub_id}")
    amount_cents = prorated_refund(plan_name, period_start, period_end, cancel_date)
    if amount_cents == 0:
        return 0
    ledger.append({"sub_id": sub_id, "amount_cents": amount_cents})
    log.info("refund issued sub=%s amount_cents=%d", sub_id, amount_cents)
    return amount_cents
