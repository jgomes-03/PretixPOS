from pretix_betterpos.models import BetterposTransaction


def serialize_transaction(obj: BetterposTransaction):
    return {
        'id': obj.id,
        'event': obj.event.slug,
        'register_id': obj.register_id,
        'session_id': obj.session_id,
        'order_code': obj.order.code,
        'payment_id': obj.payment_id,
        'channel': obj.channel,
        'state': obj.state,
        'external_reference': obj.external_reference,
        'metadata': obj.metadata,
        'created_at': obj.created_at.isoformat(),
        'updated_at': obj.updated_at.isoformat(),
    }
