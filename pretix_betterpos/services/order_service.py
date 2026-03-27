from django.db import transaction
from pretix.base.models import Order, OrderPosition

from pretix_betterpos.models import BetterposTransaction

from .audit_service import AuditService
from .base import ValidationError


class OrderOrchestrationService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(*, event, user, register, session, cart_totals, locale='en'):
        if not session or session.status != session.STATUS_OPEN:
            raise ValidationError('An open cash session is required before selling')

        order = Order.objects.create(
            event=event,
            status=Order.STATUS_PENDING,
            locale=locale,
            sales_channel='betterpos',
        )

        for line in cart_totals['lines']:
            OrderPosition.objects.create(
                order=order,
                item_id=line['item_id'],
                variation_id=line['variation_id'],
                price=line['unit_price'],
                attendee_name='POS Customer',
            )

        order.recalculate_total()
        order.save()

        transaction_row = BetterposTransaction.objects.create(
            event=event,
            register=register,
            session=session,
            order=order,
            operator=user,
            channel=BetterposTransaction.CHANNEL_CASH,
            state=BetterposTransaction.STATE_ORDER_CREATED,
            metadata={
                'subtotal': cart_totals['subtotal'],
                'discount': cart_totals['discount'],
            },
        )

        AuditService.log(
            event=event,
            actor=user,
            action_type='payment_state_change',
            register=register,
            session=session,
            order=order,
            payload={'state': BetterposTransaction.STATE_ORDER_CREATED},
        )

        return order, transaction_row
