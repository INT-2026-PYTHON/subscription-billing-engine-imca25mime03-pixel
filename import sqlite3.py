import sqlite3
from datetime import date
from billing_engine.models import SubscriptionStatus, LedgerEntry, DEBIT, BillingResult
from billing_engine.billing.pipeline import build_invoice

class BillingCycle:
    def __init__(self, db, subscription_repo, usage_repo, invoice_repo,
                 line_item_repo, ledger_repo):
        self.db = db
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo
        self.invoice_repo = invoice_repo
        self.line_item_repo = line_item_repo
        self.ledger_repo = ledger_repo

    def run(self, as_of: date) -> BillingResult:
        invoices_created = 0
        invoices_skipped = 0
        trials_activated = 0

        for sub in self.subscription_repo.list_all():
            if sub.status == SubscriptionStatus.TRIAL and sub.trial_end and sub.trial_end <= as_of:
                self.subscription_repo.update_status(sub.id, SubscriptionStatus.ACTIVE)
                trials_activated += 1

        due = self.subscription_repo.get_due_for_billing(as_of)

        for sub in due:
            usage = self.usage_repo.total_for_subscription(sub.id, sub.period_start, sub.period_end)
            invoice = build_invoice(sub, usage, as_of)

            try:
                with self.db.transaction() as conn:
                    inv = self.invoice_repo.add(conn, invoice)
                    for li in invoice.line_items:
                        self.line_item_repo.add(conn, inv.id, li)
                    self.ledger_repo.add(conn, LedgerEntry(DEBIT, invoice.total, f"Invoice {inv.id}"))
                    self.subscription_repo.advance_period(conn, sub.id)
                invoices_created += 1
            except sqlite3.IntegrityError:
                invoices_skipped += 1

        return BillingResult(invoices_created, invoices_skipped, trials_activated)
