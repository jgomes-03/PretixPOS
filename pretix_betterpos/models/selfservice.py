import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event, Order, OrderPayment


class BetterposSelfserviceCheckout(models.Model):
    STATE_CREATED = 'created'
    STATE_PENDING = 'pending'
    STATE_PAID = 'paid'
    STATE_FAILED = 'failed'
    STATE_TIMEOUT = 'timeout'
    STATE_CHOICES = (
        (STATE_CREATED, _('Created')),
        (STATE_PENDING, _('Pending')),
        (STATE_PAID, _('Paid')),
        (STATE_FAILED, _('Failed')),
        (STATE_TIMEOUT, _('Timeout')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_selfservice_checkouts', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='betterpos_selfservice_checkouts', on_delete=models.CASCADE)
    payment = models.ForeignKey(
        OrderPayment,
        related_name='betterpos_selfservice_checkouts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    phone = models.CharField(max_length=64)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default=STATE_CREATED)
    expires_at = models.DateTimeField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('POS selfservice checkout')
        verbose_name_plural = _('POS selfservice checkouts')
        indexes = [
            models.Index(fields=['event', 'state'], name='btpos_ss_event_state_idx'),
            models.Index(fields=['event', 'created_at'], name='btpos_ss_event_created_idx'),
        ]

    @staticmethod
    def make_token() -> str:
        return secrets.token_urlsafe(24)

    @staticmethod
    def default_expiry():
        return timezone.now() + timedelta(minutes=5)

    def is_expired(self):
        return timezone.now() >= self.expires_at
