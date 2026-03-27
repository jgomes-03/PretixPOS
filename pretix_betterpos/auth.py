from pretix.base.models import Event


def get_event_from_request(request, kwargs):
    if hasattr(request, 'event') and request.event:
        return request.event
    organizer = kwargs.get('organizer')
    event_slug = kwargs.get('event')
    return Event.objects.select_related('organizer').get(organizer__slug=organizer, slug=event_slug)


def has_pos_permission(user, event, code):
    if not user.is_authenticated:
        return False

    if hasattr(user, 'has_event_permission'):
        return user.has_event_permission(event.organizer, event, f'pretix_betterpos.{code}')

    return user.has_perm(f'pretix_betterpos.{code}')
