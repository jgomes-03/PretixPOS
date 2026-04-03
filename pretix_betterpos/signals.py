from django.dispatch import receiver
from django.urls import resolve
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.settings import settings_hierarkey
from pretix.control.signals import nav_event, nav_event_settings


settings_hierarkey.add_default('betterpos_selfservice_enabled', True, bool)


@receiver(nav_event, dispatch_uid='pretix_betterpos_nav_event')
def nav_event_entry(sender, request, **kwargs):
    event = kwargs.get('event')
    if not event:
        return []

    return [{
        'label': _('POS'),
        'url': reverse('plugins:pretix_betterpos:pos.index', kwargs={
            'organizer': event.organizer.slug,
            'event': event.slug,
        }),
        'active': request.resolver_match and request.resolver_match.namespace == 'plugins:pretix_betterpos',
        'icon': 'shopping-cart',
    }]


@receiver(nav_event_settings, dispatch_uid='pretix_betterpos_nav_settings')
def nav_settings_entry(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('BetterPOS'),
        'url': reverse('plugins:pretix_betterpos:settings', kwargs={
            'organizer': request.organizer.slug,
            'event': request.event.slug,
        }),
        'active': url.namespace == 'plugins:pretix_betterpos' and url.url_name == 'settings',
    }]
