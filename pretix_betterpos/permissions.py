from django.utils.translation import gettext_lazy as _


POS_PERMISSIONS = [
    ('can_view_pos', _('Can view POS interface')),
    ('can_sell_pos', _('Can create POS sales')),
    ('can_discount_pos', _('Can apply POS discounts')),
    ('can_cancel_unpaid_pos', _('Can cancel unpaid POS orders')),
    ('can_refund_pos', _('Can refund paid POS orders')),
    ('can_cash_move_pos', _('Can register POS cash movements')),
    ('can_session_control_pos', _('Can open/close POS sessions')),
    ('can_reconcile_pos', _('Can reconcile POS sessions')),
    ('can_manage_registers_pos', _('Can manage POS registers')),
    ('can_view_audit_pos', _('Can view POS audit log')),
]


def permission_codes():
    return [code for code, _ in POS_PERMISSIONS]
