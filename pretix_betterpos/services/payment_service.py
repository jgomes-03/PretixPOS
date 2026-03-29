import json
import types

from django.db import transaction
from django.http import QueryDict
from pretix.base.models import OrderPayment
from pretix.base.payment import PaymentException

from pretix_betterpos.models import BetterposTransaction

from .audit_service import AuditService
from .base import InvalidStateError, ValidationError


class PaymentService:
    @staticmethod
    def _extract_provider_error_details(response_obj):
        if not isinstance(response_obj, (dict, list)):
            return None

        parts = []

        def _add(value):
            if value is None:
                return
            text = str(value).strip()
            if not text:
                return
            if text not in parts:
                parts.append(text)

        def _walk(node):
            if isinstance(node, dict):
                for key in (
                    'transactionStatus', 'status', 'estado',
                    'code', 'errorCode', 'error_code', 'reason', 'error_reason',
                    'message', 'text', 'error', 'description', 'detail', 'error_description',
                ):
                    if key in node:
                        _add(node.get(key))

                for key in ('errors', 'fieldErrors', 'validationErrors', 'details'):
                    value = node.get(key)
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                field = item.get('field') or item.get('param') or item.get('name')
                                msg = item.get('message') or item.get('text') or item.get('error') or item.get('description')
                                if field and msg:
                                    _add(f'{field}: {msg}')
                                _walk(item)
                            else:
                                _add(item)
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool)):
                                _add(f'{sub_key}: {sub_value}')
                            else:
                                _walk(sub_value)

                for nested_key in ('data', 'result', 'response', 'payload'):
                    if nested_key in node:
                        _walk(node[nested_key])

            elif isinstance(node, list):
                for item in node:
                    _walk(item)
            else:
                _add(node)

        _walk(response_obj)

        if not parts:
            return None
        return ' | '.join(parts[:6])

    @staticmethod
    def _clean_provider_error_text(text):
        if not text:
            return text

        cleaned = str(text).strip()
        prefixes = (
            'MBWay payment failed:',
            'Payment provider communication failed:',
            'MBWay payment provider communication failed:',
        )

        changed = True
        while changed:
            changed = False
            lowered = cleaned.lower()
            for prefix in prefixes:
                if lowered.startswith(prefix.lower()):
                    cleaned = cleaned[len(prefix):].strip(' |:')
                    changed = True
                    break

        return cleaned.strip()

    @staticmethod
    def _description_only_error_text(text):
        cleaned = PaymentService._clean_provider_error_text(text)
        if not cleaned:
            return cleaned

        # Keep only human-readable description, dropping status/code tokens.
        segments = [seg.strip() for seg in str(cleaned).split('|') if seg and seg.strip()]
        if not segments:
            return cleaned

        def _is_code_like(value):
            normalized = value.replace('-', '_').strip()
            if not normalized:
                return False
            if normalized.lower() in {'rejected', 'success', 'failed', 'pending', 'error'}:
                return True
            return normalized.upper() == normalized and '_' in normalized

        descriptive = [seg for seg in segments if not _is_code_like(seg)]
        if descriptive:
            return descriptive[-1]
        return segments[-1]

    @staticmethod
    @transaction.atomic
    def pay_cash(*, transaction_row, user):
        if transaction_row.state not in {BetterposTransaction.STATE_ORDER_CREATED, BetterposTransaction.STATE_PAYMENT_CREATED}:
            raise InvalidStateError('Transaction cannot be paid in current state')

        payment = OrderPayment.objects.create(
            order=transaction_row.order,
            provider='manual',
            amount=transaction_row.order.total,
            state=OrderPayment.PAYMENT_STATE_CREATED,
        )
        payment.confirm(send_mail=False)

        transaction_row.payment = payment
        transaction_row.channel = BetterposTransaction.CHANNEL_CASH
        transaction_row.state = BetterposTransaction.STATE_PAID
        transaction_row.save(update_fields=['payment', 'channel', 'state', 'updated_at'])

        session = transaction_row.session
        if session:
            session.expected_cash += payment.amount
            session.save(update_fields=['expected_cash'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='payment_state_change',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=payment,
            payload={'state': BetterposTransaction.STATE_PAID, 'channel': 'cash'},
        )
        return payment

    @staticmethod
    @transaction.atomic
    def initiate_eupago(*, request, transaction_row, user, provider='eupago_mbway', phone=None):
        if transaction_row.state not in {BetterposTransaction.STATE_ORDER_CREATED, BetterposTransaction.STATE_PAYMENT_CREATED}:
            raise InvalidStateError('Transaction cannot start euPago in current state')

        if provider == 'eupago_mbway':
            normalized_phone = ''.join(ch for ch in str(phone or '') if ch.isdigit() or ch == '+')
            if not normalized_phone:
                raise ValidationError('Phone number is required for MBWay payments')

            request.session[f'payment_{provider}_phone'] = normalized_phone
            request.session['payment_eupago_mbway_phone'] = normalized_phone
            request.session['phone'] = normalized_phone

            # EuPago legacy provider reads request.POST even when our endpoint is JSON.
            qd = QueryDict('', mutable=True)
            qd.update({'phone': normalized_phone})
            request._post = qd

        payment = OrderPayment.objects.create(
            order=transaction_row.order,
            provider=provider,
            amount=transaction_row.order.total,
            state=OrderPayment.PAYMENT_STATE_CREATED,
        )

        provider_instance = payment.payment_provider
        fallback_redirect_url = request.build_absolute_uri(request.path)
        last_provider_response = None

        if not hasattr(provider_instance, 'order_confirm_redirect_url'):
            # Some EuPago flows expect this checkout attribute, which is missing in API-only POS context.
            provider_instance.order_confirm_redirect_url = fallback_redirect_url

        if provider == 'eupago_mbway' and hasattr(provider_instance, '_handle_payment_response'):
            original_handle = provider_instance._handle_payment_response

            def _safe_handle_payment_response(self, payment_obj, response_obj):
                try:
                    return original_handle(payment_obj, response_obj)
                except AttributeError as exc:
                    if 'order_confirm_redirect_url' not in str(exc):
                        raise
                    payment_obj.info = json.dumps(response_obj)
                    payment_obj.state = OrderPayment.PAYMENT_STATE_PENDING
                    payment_obj.save(update_fields=['info', 'state'])
                    return fallback_redirect_url

            provider_instance._handle_payment_response = types.MethodType(_safe_handle_payment_response, provider_instance)

        if provider.startswith('eupago_') and hasattr(provider_instance, '_make_api_request'):
            original_make_api_request = provider_instance._make_api_request

            def _capturing_make_api_request(*args, **kwargs):
                nonlocal last_provider_response
                response_obj = original_make_api_request(*args, **kwargs)
                if isinstance(response_obj, dict):
                    last_provider_response = response_obj
                elif isinstance(response_obj, str):
                    try:
                        parsed = json.loads(response_obj)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, dict):
                        last_provider_response = parsed
                return response_obj

            provider_instance._make_api_request = _capturing_make_api_request

        try:
            response = provider_instance.execute_payment(request, payment)
        except PaymentException as exc:
            details = None
            response_obj = last_provider_response

            if not response_obj:
                try:
                    response_obj = json.loads(payment.info) if payment.info else None
                except Exception:
                    response_obj = None

            if response_obj:
                details = PaymentService._extract_provider_error_details(response_obj)
                details = PaymentService._description_only_error_text(details)

            exc_message = PaymentService._description_only_error_text(str(exc).strip())
            generic_markers = (
                'payment provider communication failed',
                'mbway payment failed. please try again',
                'mbway payment failed. please try again later',
            )
            exc_message_is_generic = exc_message.lower() in generic_markers

            if details and exc_message and exc_message not in details:
                if not exc_message_is_generic:
                    details = f'{details} | {exc_message}'
            elif not details:
                details = exc_message

            raise ValidationError(f'MBWay payment failed: {details or "Unknown provider error"}') from exc

        transaction_row.payment = payment
        transaction_row.channel = BetterposTransaction.CHANNEL_EUPAGO
        transaction_row.state = BetterposTransaction.STATE_PENDING
        transaction_row.metadata = {
            **transaction_row.metadata,
            'provider': provider,
            'provider_response': str(response),
        }
        transaction_row.save(update_fields=['payment', 'channel', 'state', 'metadata', 'updated_at'])

        AuditService.log(
            event=transaction_row.event,
            actor=user,
            action_type='payment_state_change',
            register=transaction_row.register,
            session=transaction_row.session,
            order=transaction_row.order,
            payment=payment,
            payload={'state': BetterposTransaction.STATE_PENDING, 'channel': 'eupago'},
        )
        return payment, response
