from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from pretix_betterpos.models import BetterposCashMovement, BetterposCashSession

from .audit_service import AuditService
from .base import InvalidStateError, ValidationError


class RegisterService:
    @staticmethod
    def get_open_session(register):
        return BetterposCashSession.objects.filter(register=register, status=BetterposCashSession.STATUS_OPEN).first()

    @staticmethod
    @transaction.atomic
    def open_session(*, event, register, opened_by, opening_float=Decimal('0.00')):
        if RegisterService.get_open_session(register):
            raise InvalidStateError('Register already has an open session')

        session = BetterposCashSession.objects.create(
            event=event,
            register=register,
            opened_by=opened_by,
            opening_float=opening_float,
            expected_cash=opening_float,
            status=BetterposCashSession.STATUS_OPEN,
        )
        AuditService.log(
            event=event,
            actor=opened_by,
            action_type='session_open',
            session=session,
            register=register,
            payload={'opening_float': str(opening_float)},
        )
        return session

    @staticmethod
    @transaction.atomic
    def close_session(*, session, closed_by, counted_cash, close_notes=''):
        if session.status != BetterposCashSession.STATUS_OPEN:
            raise InvalidStateError('Session is not open')

        if counted_cash is None:
            raise ValidationError('counted_cash is required')

        session.counted_cash = counted_cash
        session.difference = counted_cash - session.expected_cash
        session.closed_by = closed_by
        session.closed_at = timezone.now()
        session.close_notes = close_notes
        session.status = BetterposCashSession.STATUS_CLOSED
        session.save(update_fields=['counted_cash', 'difference', 'closed_by', 'closed_at', 'close_notes', 'status'])

        AuditService.log(
            event=session.event,
            actor=closed_by,
            action_type='session_close',
            session=session,
            register=session.register,
            payload={
                'expected_cash': str(session.expected_cash),
                'counted_cash': str(session.counted_cash),
                'difference': str(session.difference),
            },
        )
        return session

    @staticmethod
    @transaction.atomic
    def create_cash_movement(*, event, session, performed_by, movement_type, amount, reason, reference=''):
        if session.status != BetterposCashSession.STATUS_OPEN:
            raise InvalidStateError('Cannot register movement in closed session')

        movement = BetterposCashMovement.objects.create(
            event=event,
            session=session,
            performed_by=performed_by,
            movement_type=movement_type,
            amount=amount,
            reason=reason,
            reference=reference,
        )

        if movement_type == BetterposCashMovement.TYPE_IN:
            session.expected_cash += amount
        else:
            session.expected_cash -= amount
        session.save(update_fields=['expected_cash'])

        AuditService.log(
            event=event,
            actor=performed_by,
            action_type='cash_move',
            session=session,
            register=session.register,
            payload={
                'movement_type': movement_type,
                'amount': str(amount),
                'reason': reason,
                'reference': reference,
            },
        )

        return movement
