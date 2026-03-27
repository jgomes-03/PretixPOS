from pretix_betterpos.models import BetterposActionLog


class AuditService:
    @staticmethod
    def log(*, event, actor, action_type, payload=None, register=None, session=None, order=None, payment=None):
        return BetterposActionLog.objects.create(
            event=event,
            actor=actor,
            action_type=action_type,
            payload=payload or {},
            register=register,
            session=session,
            order=order,
            payment=payment,
        )
