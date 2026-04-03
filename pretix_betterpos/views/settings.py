from django.urls import reverse
from pretix.base.models import Event
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin

from pretix_betterpos.forms import BetterPOSSettingsForm


class BetterPOSSettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = BetterPOSSettingsForm
    template_name = 'pretixplugins/pretix_betterpos/settings.html'
    permission = 'can_change_event_settings'

    def get_success_url(self):
        return reverse(
            'plugins:pretix_betterpos:settings',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )
