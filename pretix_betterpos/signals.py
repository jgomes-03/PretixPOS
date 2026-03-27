from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.control.signals import nav_event


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
