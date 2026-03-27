import json
from decimal import Decimal

from django.http import HttpResponseBadRequest, JsonResponse
from django.views import View
from pretix.base.models import Item

from pretix_betterpos.auth import get_event_from_request, has_pos_permission
from pretix_betterpos.models import BetterposActionLog, BetterposCashSession, BetterposRegister, BetterposTransaction
from pretix_betterpos.services import (
    CancellationService,
    CartService,
    InvalidStateError,
    BetterPOSError,
    OrderOrchestrationService,
    PaymentService,
    RefundService,
    RegisterService,
    ValidationError,
)

from .serializers import serialize_transaction


class BasePOSApiView(View):
    permission_code = 'can_view_pos'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        self.event = get_event_from_request(request, kwargs)
        if not has_pos_permission(request.user, self.event, self.permission_code):
            return JsonResponse({'error': f'Missing permission: {self.permission_code}'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def parse_json(request):
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValidationError('Invalid JSON payload')

    @staticmethod
    def as_decimal(value, field):
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise ValidationError(f'Invalid decimal value for {field}') from exc

    def get_register(self, register_id):
        try:
            return BetterposRegister.objects.get(event=self.event, pk=register_id, is_active=True)
        except BetterposRegister.DoesNotExist as exc:
            raise ValidationError('Invalid register_id') from exc

    def get_open_session(self, register):
        session = RegisterService.get_open_session(register)
        if not session:
            raise InvalidStateError('An open session is required for this register')
        return session

    @staticmethod
    def error_response(exc):
        status = 400
        if isinstance(exc, InvalidStateError):
            status = 409
        return JsonResponse({'error': str(exc)}, status=status)


class SessionStatusView(BasePOSApiView):
    def get(self, request, *args, **kwargs):
        register_id = request.GET.get('register_id')
        if not register_id:
            return HttpResponseBadRequest('register_id is required')

        register = self.get_register(register_id)
        session = RegisterService.get_open_session(register)
        if not session:
            return JsonResponse({'has_open_session': False, 'register_id': register.id})

        return JsonResponse(
            {
                'has_open_session': True,
                'session': {
                    'id': session.id,
                    'opened_at': session.opened_at.isoformat(),
                    'opened_by': session.opened_by_id,
                    'opening_float': str(session.opening_float),
                    'expected_cash': str(session.expected_cash),
                },
            }
        )


class OpenSessionView(BasePOSApiView):
    permission_code = 'can_session_control_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            register = self.get_register(payload.get('register_id'))
            opening_float = self.as_decimal(payload.get('opening_float', '0.00'), 'opening_float')
            session = RegisterService.open_session(
                event=self.event,
                register=register,
                opened_by=request.user,
                opening_float=opening_float,
            )
            return JsonResponse(
                {
                    'session_id': session.id,
                    'status': session.status,
                    'opening_float': str(session.opening_float),
                    'expected_cash': str(session.expected_cash),
                },
                status=201,
            )
        except BetterPOSError as exc:
            return self.error_response(exc)


class CloseSessionView(BasePOSApiView):
    permission_code = 'can_session_control_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            session = BetterposCashSession.objects.get(
                event=self.event,
                register_id=payload.get('register_id'),
                status=BetterposCashSession.STATUS_OPEN,
            )
            counted_cash = self.as_decimal(payload.get('counted_cash'), 'counted_cash')
            closed = RegisterService.close_session(
                session=session,
                closed_by=request.user,
                counted_cash=counted_cash,
                close_notes=payload.get('close_notes', ''),
            )
            return JsonResponse(
                {
                    'session_id': closed.id,
                    'status': closed.status,
                    'expected_cash': str(closed.expected_cash),
                    'counted_cash': str(closed.counted_cash),
                    'difference': str(closed.difference),
                }
            )
        except BetterposCashSession.DoesNotExist:
            return JsonResponse({'error': 'Open session not found'}, status=404)
        except BetterPOSError as exc:
            return self.error_response(exc)


class CashMovementView(BasePOSApiView):
    permission_code = 'can_cash_move_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            register = self.get_register(payload.get('register_id'))
            session = self.get_open_session(register)
            movement = RegisterService.create_cash_movement(
                event=self.event,
                session=session,
                performed_by=request.user,
                movement_type=payload.get('movement_type'),
                amount=self.as_decimal(payload.get('amount'), 'amount'),
                reason=payload.get('reason', ''),
                reference=payload.get('reference', ''),
            )
            return JsonResponse(
                {
                    'movement_id': movement.id,
                    'session_id': session.id,
                    'movement_type': movement.movement_type,
                    'amount': str(movement.amount),
                    'expected_cash': str(session.expected_cash),
                },
                status=201,
            )
        except BetterPOSError as exc:
            return self.error_response(exc)


class CatalogView(BasePOSApiView):
    def get(self, request, *args, **kwargs):
        items = (
            Item.objects.filter(event=self.event, admission=True, active=True)
            .prefetch_related('variations')
            .order_by('name')
        )
        data = []
        for item in items:
            data.append(
                {
                    'id': item.id,
                    'name': str(item.name),
                    'price': str(item.default_price),
                    'variations': [
                        {
                            'id': v.id,
                            'value': str(v.value),
                            'price': str(v.price if v.price is not None else item.default_price),
                        }
                        for v in item.variations.all()
                    ],
                }
            )
        return JsonResponse({'items': data})


class QuoteView(BasePOSApiView):
    permission_code = 'can_sell_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            result = CartService.compute_cart_totals(
                event=self.event,
                lines=payload.get('lines', []),
                discount=payload.get('discount'),
            )
            return JsonResponse(result)
        except BetterPOSError as exc:
            return self.error_response(exc)


class CreateOrderView(BasePOSApiView):
    permission_code = 'can_sell_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            register = self.get_register(payload.get('register_id'))
            session = self.get_open_session(register)

            idempotency_key = request.headers.get('Idempotency-Key') or payload.get('idempotency_key', '')
            if idempotency_key:
                existing = BetterposTransaction.objects.filter(
                    event=self.event,
                    register=register,
                    idempotency_key=idempotency_key,
                ).first()
                if existing:
                    return JsonResponse({'transaction': serialize_transaction(existing), 'idempotent_replay': True})

            cart_totals = CartService.compute_cart_totals(
                event=self.event,
                lines=payload.get('lines', []),
                discount=payload.get('discount'),
            )
            order, transaction_row = OrderOrchestrationService.create_order_from_cart(
                event=self.event,
                user=request.user,
                register=register,
                session=session,
                cart_totals=cart_totals,
                locale=payload.get('locale', 'en'),
            )
            if idempotency_key:
                transaction_row.idempotency_key = idempotency_key
                transaction_row.save(update_fields=['idempotency_key'])

            return JsonResponse(
                {
                    'order_code': order.code,
                    'transaction': serialize_transaction(transaction_row),
                },
                status=201,
            )
        except BetterPOSError as exc:
            return self.error_response(exc)


class CashPaymentView(BasePOSApiView):
    permission_code = 'can_sell_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            transaction_row = BetterposTransaction.objects.select_related('order', 'session').get(
                event=self.event,
                pk=payload.get('transaction_id'),
            )
            payment = PaymentService.pay_cash(transaction_row=transaction_row, user=request.user)
            return JsonResponse(
                {
                    'payment_id': payment.id,
                    'transaction': serialize_transaction(transaction_row),
                }
            )
        except BetterposTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        except BetterPOSError as exc:
            return self.error_response(exc)


class EuPagoPaymentView(BasePOSApiView):
    permission_code = 'can_sell_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            transaction_row = BetterposTransaction.objects.select_related('order', 'session').get(
                event=self.event,
                pk=payload.get('transaction_id'),
            )
            payment, provider_response = PaymentService.initiate_eupago(
                request=request,
                transaction_row=transaction_row,
                user=request.user,
                provider=payload.get('provider', 'eupago_mbway'),
            )
            return JsonResponse(
                {
                    'payment_id': payment.id,
                    'transaction': serialize_transaction(transaction_row),
                    'provider_response': str(provider_response),
                }
            )
        except BetterposTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        except BetterPOSError as exc:
            return self.error_response(exc)


class TransactionStatusView(BasePOSApiView):
    def get(self, request, transaction_id, *args, **kwargs):
        try:
            transaction_row = BetterposTransaction.objects.get(event=self.event, pk=transaction_id)
            return JsonResponse({'transaction': serialize_transaction(transaction_row)})
        except BetterposTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)


class CancelOrderView(BasePOSApiView):
    permission_code = 'can_cancel_unpaid_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            transaction_row = BetterposTransaction.objects.select_related('order').get(
                event=self.event,
                pk=payload.get('transaction_id'),
            )
            transaction_row = CancellationService.cancel_unpaid_order(
                transaction_row=transaction_row,
                user=request.user,
                reason=payload.get('reason', ''),
            )
            return JsonResponse({'transaction': serialize_transaction(transaction_row)})
        except BetterposTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        except BetterPOSError as exc:
            return self.error_response(exc)


class RefundOrderView(BasePOSApiView):
    permission_code = 'can_refund_pos'

    def post(self, request, *args, **kwargs):
        try:
            payload = self.parse_json(request)
            transaction_row = BetterposTransaction.objects.select_related('payment').get(
                event=self.event,
                pk=payload.get('transaction_id'),
            )
            refund_payment, transaction_row = RefundService.refund_paid_order(
                transaction_row=transaction_row,
                user=request.user,
                amount=payload.get('amount'),
                reason=payload.get('reason', ''),
            )
            return JsonResponse(
                {
                    'refund_payment_id': refund_payment.id,
                    'transaction': serialize_transaction(transaction_row),
                }
            )
        except BetterposTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        except BetterPOSError as exc:
            return self.error_response(exc)


class AuditFeedView(BasePOSApiView):
    permission_code = 'can_view_audit_pos'

    def get(self, request, *args, **kwargs):
        limit = int(request.GET.get('limit', 100))
        rows = BetterposActionLog.objects.filter(event=self.event).select_related('actor', 'register', 'session', 'order', 'payment')[:limit]
        return JsonResponse(
            {
                'actions': [
                    {
                        'id': row.id,
                        'action_type': row.action_type,
                        'actor_id': row.actor_id,
                        'register_id': row.register_id,
                        'session_id': row.session_id,
                        'order_id': row.order_id,
                        'payment_id': row.payment_id,
                        'payload': row.payload,
                        'created_at': row.created_at.isoformat(),
                    }
                    for row in rows
                ]
            }
        )
