from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event

from pretix_betterpos.permissions import POS_PERMISSIONS


class BetterposRegister(models.Model):
    event = models.ForeignKey(Event, related_name='betterpos_registers', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=40)
    is_active = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='EUR')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('event', 'code')
        unique_together = (('event', 'code'),)
        permissions = POS_PERMISSIONS
        verbose_name = _('POS register')
        verbose_name_plural = _('POS registers')

    def __str__(self):
        return f'{self.event.slug}:{self.code}'


class BetterposRegisterAssignment(models.Model):
    ROLE_CASHIER = 'cashier'
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_MANAGER = 'manager'
    ROLE_CHOICES = (
        (ROLE_CASHIER, _('Cashier')),
        (ROLE_SUPERVISOR, _('Supervisor')),
        (ROLE_MANAGER, _('Manager')),
    )

    event = models.ForeignKey(Event, related_name='betterpos_assignments', on_delete=models.CASCADE)
    register = models.ForeignKey(BetterposRegister, related_name='assignments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='betterpos_assignments', on_delete=models.CASCADE)
    role_at_register = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CASHIER)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('register', 'user')
        unique_together = (('event', 'register', 'user'),)
        verbose_name = _('POS register assignment')
        verbose_name_plural = _('POS register assignments')

    def __str__(self):
        return f'{self.user} -> {self.register}'
