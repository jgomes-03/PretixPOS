from decimal import Decimal

from django.db import transaction
from pretix.base.models import OrderPayment

from pretix_betterpos.models import BetterposTransaction

from .audit_service import AuditService
from .base import InvalidStateError, ValidationError


class CancellationService:
    @staticmethod
    @transaction.atomic
    def cancel_unpaid_order(*, transaction_row, user, reason=''):
        if transaction_row.state == BetterposTransaction.STATE_PAID:
            raise InvalidStateError('Paid orders cannot be cancelled')

        transaction_row.state = BetterposTransaction.STATE_CANCELLED_UNPAID
        transaction_row.metadata = {**transaction_row.metadata, 'cancel_reason': reason}
        transaction_row.save(update_fields=['state', 'metadata', 'updated_at'])

        transaction_row.order.status = transaction_row.order.STATUS_CANCELED
        transaction_row.order.save(update_fields=['status'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='cancel',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payload={'reason': reason, 'state': transaction_row.state},
        )
        return transaction_row


class RefundService:
    @staticmethod
    @transaction.atomic
    def refund_paid_order(*, transaction_row, user, amount=None, reason=''):
        if transaction_row.state != BetterposTransaction.STATE_PAID:
            raise InvalidStateError('Only paid orders can be refunded')

        if not transaction_row.payment:
            raise ValidationError('Transaction has no payment attached')

        payment = transaction_row.payment
        refund_amount = Decimal(str(amount)) if amount is not None else payment.amount
        if refund_amount <= 0 or refund_amount > payment.amount:
            raise ValidationError('Invalid refund amount')

        refund_payment = OrderPayment.objects.create(
            order=payment.order,
            provider=payment.provider,
            amount=-refund_amount,
            state=OrderPayment.PAYMENT_STATE_CONFIRMED,
            info='{"source":"betterpos_refund"}',
        )

        if refund_amount == payment.amount:
            transaction_row.state = BetterposTransaction.STATE_REFUND_FULL
        else:
            transaction_row.state = BetterposTransaction.STATE_REFUND_PARTIAL
        transaction_row.metadata = {**transaction_row.metadata, 'refund_reason': reason, 'refund_amount': str(refund_amount)}
        transaction_row.save(update_fields=['state', 'metadata', 'updated_at'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='refund',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=payment,
            payload={
                'refund_payment_id': refund_payment.id,
                'amount': str(refund_amount),
                'reason': reason,
                'state': transaction_row.state,
            },
        )
        return refund_payment, transaction_row
