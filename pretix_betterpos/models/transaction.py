from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event, Order, OrderPayment

from .register import BetterposRegister
from .session import BetterposCashSession


class BetterposTransaction(models.Model):
    CHANNEL_CASH = 'cash'
    CHANNEL_EUPAGO = 'eupago'
    CHANNEL_CHOICES = (
        (CHANNEL_CASH, _('Cash')),
        (CHANNEL_EUPAGO, _('euPago')),
    )

    STATE_DRAFT = 'draft'
    STATE_ORDER_CREATED = 'order_created'
    STATE_PAYMENT_CREATED = 'payment_created'
    STATE_PENDING = 'pending_async'
    STATE_PAID = 'paid'
    STATE_FAILED = 'failed'
    STATE_EXPIRED = 'expired'
    STATE_CANCELLED_UNPAID = 'cancelled_unpaid'
    STATE_REFUND_PARTIAL = 'refund_partial'
    STATE_REFUND_FULL = 'refund_full'
    STATE_CHOICES = (
        (STATE_DRAFT, _('Draft')),
        (STATE_ORDER_CREATED, _('Order created')),
        (STATE_PAYMENT_CREATED, _('Payment created')),
        (STATE_PENDING, _('Pending async')),
        (STATE_PAID, _('Paid')),
        (STATE_FAILED, _('Failed')),
        (STATE_EXPIRED, _('Expired')),
        (STATE_CANCELLED_UNPAID, _('Cancelled unpaid')),
        (STATE_REFUND_PARTIAL, _('Refund partial')),
        (STATE_REFUND_FULL, _('Refund full')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_transactions', on_delete=models.CASCADE)
    register = models.ForeignKey(BetterposRegister, related_name='transactions', on_delete=models.PROTECT)
    session = models.ForeignKey(BetterposCashSession, related_name='transactions', on_delete=models.PROTECT, null=True, blank=True)
    order = models.ForeignKey(Order, related_name='betterpos_transactions', on_delete=models.PROTECT)
    payment = models.ForeignKey(OrderPayment, related_name='betterpos_transactions', on_delete=models.PROTECT, null=True, blank=True)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='betterpos_transactions', on_delete=models.PROTECT)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=STATE_DRAFT)
    external_reference = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['event', 'state'], name='betterpos_tx_state_idx'),
            models.Index(fields=['register', 'created_at'], name='betterpos_tx_reg_created_idx'),
        ]
        verbose_name = _('POS transaction')
        verbose_name_plural = _('POS transactions')

    def __str__(self):
        return f'{self.event.slug}:{self.order.code}:{self.channel}:{self.state}'


class BetterposCartSnapshot(models.Model):
    event = models.ForeignKey(Event, related_name='betterpos_cart_snapshots', on_delete=models.CASCADE)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='betterpos_cart_snapshots', on_delete=models.CASCADE)
    register = models.ForeignKey(BetterposRegister, related_name='cart_snapshots', on_delete=models.CASCADE)
    snapshot_payload = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('POS cart snapshot')
        verbose_name_plural = _('POS cart snapshots')

    def __str__(self):
        return f'{self.event.slug}:{self.operator_id}:{self.register_id}'
