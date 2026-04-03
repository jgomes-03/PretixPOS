from django.urls import path

from .public_views import (
    PublicCatalogView,
    PublicCheckoutStartView,
    PublicCheckoutStatusView,
    PublicQuoteView,
)

public_api_urlpatterns = [
    path('catalog/', PublicCatalogView.as_view(), name='public.catalog'),
    path('cart/quote/', PublicQuoteView.as_view(), name='public.cart.quote'),
    path('checkout/start/', PublicCheckoutStartView.as_view(), name='public.checkout.start'),
    path('checkout/<str:token>/status/', PublicCheckoutStatusView.as_view(), name='public.checkout.status'),
]
