from django.urls import path

from .views import (
    AuditFeedView,
    CancelOrderView,
    CatalogView,
    CashMovementView,
    CloseSessionView,
    CreateOrderView,
    EuPagoPaymentView,
    OpenSessionView,
    QuoteView,
    RefundOrderView,
    SessionStatusView,
    TransactionStatusView,
    CashPaymentView,
)

api_urlpatterns = [
    path('session/status/', SessionStatusView.as_view(), name='session.status'),
    path('session/open/', OpenSessionView.as_view(), name='session.open'),
    path('session/close/', CloseSessionView.as_view(), name='session.close'),
    path('cash/movement/', CashMovementView.as_view(), name='cash.movement'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('cart/quote/', QuoteView.as_view(), name='cart.quote'),
    path('order/create/', CreateOrderView.as_view(), name='order.create'),
    path('payment/cash/', CashPaymentView.as_view(), name='payment.cash'),
    path('payment/eupago/', EuPagoPaymentView.as_view(), name='payment.eupago'),
    path('transaction/<int:transaction_id>/status/', TransactionStatusView.as_view(), name='transaction.status'),
    path('order/cancel/', CancelOrderView.as_view(), name='order.cancel'),
    path('order/refund/', RefundOrderView.as_view(), name='order.refund'),
    path('audit/feed/', AuditFeedView.as_view(), name='audit.feed'),
]
