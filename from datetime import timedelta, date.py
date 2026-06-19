from datetime import timedelta, date
from billing_engine.models import DunningOutcome, DunningState, SubscriptionStatus, LedgerEntry, LedgerDirection

MAX_ATTEMPTS = 3
RETRY_DELAYS_DAYS = {1: 1, 2: 3, 3: 7}

class DunningProcess:
    def __init__(self, gateway, attempt_repo, invoice_repo, ledger_repo, subscription_repo):
        self.gateway = gateway
        self.attempt_repo = attempt_repo
        self.invoice_repo = invoice_repo
        self.ledger_repo = ledger_repo
        self.subscription_repo = subscription_repo

    def attempt(self, invoice, customer_id, now):
        attempt_no = self.attempt_repo.count_for_invoice(invoice.id) + 1
        result = self.gateway.charge(invoice)

        if result == "SUCCESS":
            self.invoice_repo.mark_paid(invoice.id)
            self.ledger_repo.add(LedgerEntry(
                None, invoice.id, customer_id,
                invoice.total, LedgerDirection.CREDIT,
                f"Payment for invoice {invoice.id}"
            ))
            self.attempt_repo.add(invoice.id, attempt_no, "SUCCESS", None, None)
            return DunningOutcome(DunningState.SUCCEEDED, attempt_no, None)

        if attempt_no >= MAX_ATTEMPTS:
            self.invoice_repo.mark_failed(invoice.id)
            self.subscription_repo.update_status(
                invoice.subscription_id, SubscriptionStatus.PAST_DUE,
                past_due_since=now.date()
            )
            self.attempt_repo.add(invoice.id, attempt_no, "FAILED", "Gateway failure", None)
            return DunningOutcome(DunningState.FAILED_FINAL, attempt_no, None)

        delay = RETRY_DELAYS_DAYS[attempt_no]
        next_retry = now + timedelta(days=delay)
        self.attempt_repo.add(invoice.id, attempt_no, "FAILED", "Gateway failure", next_retry)
        return DunningOutcome(DunningState.RETRYING, attempt_no, next_retry)

    @staticmethod
    def should_cancel(past_due_since: date, today: date, grace_days: int = 7) -> bool:
        return (today - past_due_since).days >= grace_days
