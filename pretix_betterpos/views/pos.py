from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from pretix_betterpos.auth import get_event_from_request, has_pos_permission
from pretix_betterpos.models import BetterposCashSession, BetterposRegister


class POSIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'pretixplugins/pretix_betterpos/pos/index.html'

    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_from_request(request, kwargs)
        if not has_pos_permission(request.user, self.event, 'can_view_pos'):
            return HttpResponseForbidden('Missing permission: can_view_pos')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['registers'] = BetterposRegister.objects.filter(event=self.event, is_active=True)
        context['open_sessions'] = BetterposCashSession.objects.filter(event=self.event, status=BetterposCashSession.STATUS_OPEN)
        return context
