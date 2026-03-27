from django.db import transaction
from pretix.base.models import OrderPayment

from pretix_betterpos.models import BetterposTransaction

from .audit_service import AuditService


class AsyncSettlementService:
    @staticmethod
    @transaction.atomic
    def finalize_pending_payment(*, payment, actor=None, external_state='paid', metadata=None):
        transaction_row = BetterposTransaction.objects.select_for_update().filter(payment=payment).first()
        if not transaction_row:
            return None

        if transaction_row.state in {
            BetterposTransaction.STATE_PAID,
            BetterposTransaction.STATE_FAILED,
            BetterposTransaction.STATE_EXPIRED,
            BetterposTransaction.STATE_CANCELLED_UNPAID,
            BetterposTransaction.STATE_REFUND_FULL,
        }:
            return transaction_row

        if external_state == 'paid':
            if payment.state != OrderPayment.PAYMENT_STATE_CONFIRMED:
                payment.confirm()
            transaction_row.state = BetterposTransaction.STATE_PAID
        elif external_state == 'failed':
            transaction_row.state = BetterposTransaction.STATE_FAILED
        else:
            transaction_row.state = BetterposTransaction.STATE_EXPIRED

        transaction_row.metadata = {**transaction_row.metadata, **(metadata or {})}
        transaction_row.save(update_fields=['state', 'metadata', 'updated_at'])

        AuditService.log(
            event=transaction_row.event,
            actor=actor or transaction_row.operator,
            action_type='payment_state_change',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=transaction_row.payment,
            payload={'state': transaction_row.state, 'source': 'async_settlement'},
        )
        return transaction_row
