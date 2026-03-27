from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event

from .register import BetterposRegister


class BetterposCashSession(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = (
        (STATUS_OPEN, _('Open')),
        (STATUS_CLOSED, _('Closed')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_cash_sessions', on_delete=models.CASCADE)
    register = models.ForeignKey(BetterposRegister, related_name='cash_sessions', on_delete=models.PROTECT)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='opened_betterpos_sessions', on_delete=models.PROTECT)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='closed_betterpos_sessions',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_OPEN)
    close_notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-opened_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['register'],
                condition=Q(status='open'),
                name='btpos_open_session_reg_uq',
            )
        ]
        verbose_name = _('POS cash session')
        verbose_name_plural = _('POS cash sessions')

    def __str__(self):
        return f'{self.register} ({self.status})'


class BetterposCashMovement(models.Model):
    TYPE_IN = 'in'
    TYPE_OUT = 'out'
    TYPE_CHOICES = (
        (TYPE_IN, _('Cash in')),
        (TYPE_OUT, _('Cash out')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_cash_movements', on_delete=models.CASCADE)
    session = models.ForeignKey(BetterposCashSession, related_name='movements', on_delete=models.PROTECT)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='betterpos_cash_movements', on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    reference = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('POS cash movement')
        verbose_name_plural = _('POS cash movements')

    def __str__(self):
        return f'{self.session_id}:{self.movement_type}:{self.amount}'
