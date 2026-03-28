from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView
)
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from pretix.control.permissions import EventPermissionRequiredMixin

from pretix_betterpos.auth import has_pos_permission
from pretix_betterpos.models import (
    BetterposCashSession, BetterposRegister, BetterposTransaction,
    BetterposActionLog
)


class AdminBaseMixin(EventPermissionRequiredMixin):
    """Base class for all admin views"""
    permission = 'can_change_event_settings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.request.event
        
        # Add permission flags for template-level checks
        user = self.request.user
        event = self.request.event
        context['user_permissions'] = {
            'can_manage_registers': has_pos_permission(user, event, 'can_manage_registers_pos'),
            'can_session_control': has_pos_permission(user, event, 'can_session_control_pos'),
            'can_reconcile': has_pos_permission(user, event, 'can_reconcile_pos'),
            'can_refund': has_pos_permission(user, event, 'can_refund_pos'),
            'can_view_audit': has_pos_permission(user, event, 'can_view_audit_pos'),
        }
        
        return context


class DashboardView(AdminBaseMixin, TemplateView):
    """POS Dashboard with KPIs"""
    template_name = 'pretixplugins/pretix_betterpos/admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        event = self.request.event

        # Today's transactions (paid only)
        today_transactions = BetterposTransaction.objects.filter(
            event=event,
            created_at__date=today,
            state__in=['paid', 'pending_async']
        )
        
        # Calculate totals
        today_total = today_transactions.aggregate(total=Sum('order__total'))['total'] or Decimal('0.00')
        today_count = today_transactions.count()
        
        # Open sessions
        open_sessions = BetterposCashSession.objects.filter(
            event=event,
            status=BetterposCashSession.STATUS_OPEN
        )
        
        # Pending payments
        pending_transactions = BetterposTransaction.objects.filter(
            event=event,
            state='pending_async'
        ).count()
        
        # Recent transactions (last 10)
        recent_transactions = today_transactions.select_related(
            'order', 'register', 'operator'
        ).order_by('-created_at')[:10]
        
        context.update({
            'today_total': today_total,
            'today_count': today_count,
            'open_sessions': open_sessions,
            'open_sessions_count': open_sessions.count(),
            'pending_transactions': pending_transactions,
            'recent_transactions': recent_transactions,
        })
        return context


class RegisterListView(AdminBaseMixin, ListView):
    """List all registers"""
    template_name = 'pretixplugins/pretix_betterpos/admin/registers_list.html'
    context_object_name = 'registers'
    paginate_by = 50

    def get_queryset(self):
        return BetterposRegister.objects.filter(
            event=self.request.event
        ).order_by('code')


class RegisterCreateView(AdminBaseMixin, CreateView):
    """Create a new register"""
    template_name = 'pretixplugins/pretix_betterpos/admin/register_form.html'
    model = BetterposRegister
    fields = ['name', 'code', 'default_currency', 'is_active']

    def form_valid(self, form):
        form.instance.event = self.request.event
        response = super().form_valid(form)
        messages.success(self.request, _('Register created successfully.'))
        return response

    def get_success_url(self):
        return reverse('plugins:pretix_betterpos:registers', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class RegisterUpdateView(AdminBaseMixin, UpdateView):
    """Update register details"""
    template_name = 'pretixplugins/pretix_betterpos/admin/register_form.html'
    model = BetterposRegister
    fields = ['name', 'code', 'default_currency', 'is_active']

    def get_queryset(self):
        return BetterposRegister.objects.filter(event=self.request.event)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Register updated successfully.'))
        return response

    def get_success_url(self):
        return reverse('plugins:pretix_betterpos:registers', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class RegisterDeleteView(AdminBaseMixin, DeleteView):
    """Delete/deactivate a register"""
    template_name = 'pretixplugins/pretix_betterpos/admin/register_confirm_delete.html'
    model = BetterposRegister

    def get_queryset(self):
        return BetterposRegister.objects.filter(event=self.request.event)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        messages.success(request, _('Register deactivated successfully.'))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('plugins:pretix_betterpos:registers', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class SessionListView(AdminBaseMixin, ListView):
    """List all cash sessions"""
    template_name = 'pretixplugins/pretix_betterpos/admin/sessions_list.html'
    context_object_name = 'sessions'
    paginate_by = 50

    def get_queryset(self):
        return BetterposCashSession.objects.filter(
            event=self.request.event
        ).select_related('register', 'opened_by', 'closed_by').order_by('-opened_at')


class TransactionListView(AdminBaseMixin, ListView):
    """List all transactions with filtering"""
    template_name = 'pretixplugins/pretix_betterpos/admin/transactions_list.html'
    context_object_name = 'transactions'
    paginate_by = 50

    def get_queryset(self):
        qs = BetterposTransaction.objects.filter(
            event=self.request.event
        ).select_related('order', 'register', 'operator', 'session').order_by('-created_at')

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Filter by payment channel
        channel = self.request.GET.get('channel')
        if channel:
            qs = qs.filter(channel=channel)

        # Filter by state
        state = self.request.GET.get('state')
        if state:
            qs = qs.filter(state=state)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['channels'] = BetterposTransaction.CHANNEL_CHOICES
        context['states'] = BetterposTransaction.STATE_CHOICES
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['channel'] = self.request.GET.get('channel', '')
        context['state'] = self.request.GET.get('state', '')
        return context


class AuditListView(AdminBaseMixin, ListView):
    """List audit log with filtering"""
    template_name = 'pretixplugins/pretix_betterpos/admin/audit_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 100

    def get_queryset(self):
        qs = BetterposActionLog.objects.filter(
            event=self.request.event
        ).select_related('actor', 'register', 'session', 'order', 'payment').order_by('-created_at')

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Filter by action type
        action_type = self.request.GET.get('action_type')
        if action_type:
            qs = qs.filter(action_type=action_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_types'] = BetterposActionLog.ACTION_CHOICES
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['action_type'] = self.request.GET.get('action_type', '')
        return context


class ReportsView(AdminBaseMixin, TemplateView):
    """Reports and analytics dashboard"""
    template_name = 'pretixplugins/pretix_betterpos/admin/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.request.event

        # Date range (default: last 30 days)
        today = date.today()
        days_range = int(self.request.GET.get('days', 30))
        date_from = today - timedelta(days=days_range)

        # Transactions in range
        transactions = BetterposTransaction.objects.filter(
            event=event,
            created_at__date__gte=date_from,
            created_at__date__lte=today,
            state__in=['paid', 'pending_async']
        )

        # Overall stats
        total_sales = transactions.aggregate(total=Sum('order__total'))['total'] or Decimal('0.00')
        total_count = transactions.count()

        # By channel
        by_channel = {}
        for channel, label in BetterposTransaction.CHANNEL_CHOICES:
            channel_total = transactions.filter(channel=channel).aggregate(
                total=Sum('order__total')
            )['total'] or Decimal('0.00')
            by_channel[label] = {
                'total': channel_total,
                'count': transactions.filter(channel=channel).count(),
            }

        # By operator (top 10)
        operators = transactions.values('operator__first_name', 'operator__last_name').annotate(
            total=Sum('order__total'),
            count=Count('id')
        ).order_by('-total')[:10]

        # By register (activity)
        registers = transactions.values('register__name').annotate(
            total=Sum('order__total'),
            count=Count('id')
        ).order_by('-total')

        context.update({
            'total_sales': total_sales,
            'total_count': total_count,
            'by_channel': by_channel,
            'operators': operators,
            'registers': registers,
            'days_range': days_range,
            'date_from': date_from,
            'date_to': today,
        })
        return context
