from django.views.generic import TemplateView
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from pretix_betterpos.auth import has_pos_permission


@method_decorator(ensure_csrf_cookie, name='dispatch')
class POSIndexView(TemplateView):
    template_name = 'pretixplugins/pretix_betterpos/pos/index.html'

    def dispatch(self, request, *args, **kwargs):
        event = getattr(request, 'event', None)
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Authentication required')
        if not event or not has_pos_permission(request.user, event, 'can_view_pos'):
            return HttpResponseForbidden('Missing permission: can_view_pos')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.request.event
        context['event'] = event
        context['base_path'] = f'/control/event/{event.organizer.slug}/{event.slug}/betterpos'
        context['api_base'] = f'/control/event/{event.organizer.slug}/{event.slug}/betterpos/api'
        context['can_manage_registers'] = has_pos_permission(self.request.user, event, 'can_manage_registers_pos')
        context['can_view_audit'] = has_pos_permission(self.request.user, event, 'can_view_audit_pos')
        context['can_session_control'] = has_pos_permission(self.request.user, event, 'can_session_control_pos')
        context['can_sell'] = has_pos_permission(self.request.user, event, 'can_sell_pos')
        return context
