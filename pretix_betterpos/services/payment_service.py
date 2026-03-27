from django.db import transaction
from pretix.base.models import OrderPayment

from pretix_betterpos.models import BetterposTransaction

from .audit_service import AuditService
from .base import InvalidStateError


class PaymentService:
    @staticmethod
    @transaction.atomic
    def pay_cash(*, transaction_row, user):
        if transaction_row.state not in {BetterposTransaction.STATE_ORDER_CREATED, BetterposTransaction.STATE_PAYMENT_CREATED}:
            raise InvalidStateError('Transaction cannot be paid in current state')

        payment = OrderPayment.objects.create(
            order=transaction_row.order,
            provider='manual',
            amount=transaction_row.order.total,
            state=OrderPayment.PAYMENT_STATE_CREATED,
        )
        payment.confirm()

        transaction_row.payment = payment
        transaction_row.channel = BetterposTransaction.CHANNEL_CASH
        transaction_row.state = BetterposTransaction.STATE_PAID
        transaction_row.save(update_fields=['payment', 'channel', 'state', 'updated_at'])

        session = transaction_row.session
        if session:
            session.expected_cash += payment.amount
            session.save(update_fields=['expected_cash'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='payment_state_change',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=payment,
            payload={'state': BetterposTransaction.STATE_PAID, 'channel': 'cash'},
        )
        return payment

    @staticmethod
    @transaction.atomic
    def initiate_eupago(*, request, transaction_row, user, provider='eupago_mbway'):
        if transaction_row.state not in {BetterposTransaction.STATE_ORDER_CREATED, BetterposTransaction.STATE_PAYMENT_CREATED}:
            raise InvalidStateError('Transaction cannot start euPago in current state')

        payment = OrderPayment.objects.create(
            order=transaction_row.order,
            provider=provider,
            amount=transaction_row.order.total,
            state=OrderPayment.PAYMENT_STATE_CREATED,
        )

        provider_instance = payment.payment_provider
        response = provider_instance.execute_payment(request, payment)

        transaction_row.payment = payment
        transaction_row.channel = BetterposTransaction.CHANNEL_EUPAGO
        transaction_row.state = BetterposTransaction.STATE_PENDING
        transaction_row.metadata = {
            **transaction_row.metadata,
            'provider': provider,
            'provider_response': str(response),
        }
        transaction_row.save(update_fields=['payment', 'channel', 'state', 'metadata', 'updated_at'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='payment_state_change',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=payment,
            payload={'state': BetterposTransaction.STATE_PENDING, 'channel': 'eupago'},
        )
        return payment, response
