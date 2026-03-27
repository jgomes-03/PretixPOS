from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event, Order, OrderPayment

from .register import BetterposRegister
from .session import BetterposCashSession


class BetterposActionLog(models.Model):
    ACTION_DISCOUNT = 'discount'
    ACTION_CANCEL = 'cancel'
    ACTION_REFUND = 'refund'
    ACTION_CASH_MOVE = 'cash_move'
    ACTION_SESSION_OPEN = 'session_open'
    ACTION_SESSION_CLOSE = 'session_close'
    ACTION_PAYMENT_STATE = 'payment_state_change'
    ACTION_CHOICES = (
        (ACTION_DISCOUNT, _('Discount')),
        (ACTION_CANCEL, _('Cancel')),
        (ACTION_REFUND, _('Refund')),
        (ACTION_CASH_MOVE, _('Cash movement')),
        (ACTION_SESSION_OPEN, _('Session open')),
        (ACTION_SESSION_CLOSE, _('Session close')),
        (ACTION_PAYMENT_STATE, _('Payment state change')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_action_logs', on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='betterpos_action_logs', on_delete=models.PROTECT)
    register = models.ForeignKey(BetterposRegister, related_name='action_logs', on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(BetterposCashSession, related_name='action_logs', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, related_name='betterpos_action_logs', on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(OrderPayment, related_name='betterpos_action_logs', on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=40, choices=ACTION_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['event', 'action_type'], name='betterpos_log_event_action_idx'),
            models.Index(fields=['event', 'created_at'], name='btpos_log_event_created_idx'),
        ]
        verbose_name = _('POS action log')
        verbose_name_plural = _('POS action logs')

    def __str__(self):
        return f'{self.event.slug}:{self.action_type}:{self.created_at.isoformat()}'
