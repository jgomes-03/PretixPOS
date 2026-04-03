from django.urls import include, re_path

from .api.urls import api_urlpatterns
from .views.pos import POSIndexView
from .views.public import PublicBuyView
from .views.settings import BetterPOSSettingsView
from .api.public_urls import public_api_urlpatterns

urlpatterns = [
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/settings/betterpos/?$',
        BetterPOSSettingsView.as_view(),
        name='settings',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/api/',
        include((api_urlpatterns, 'api')),
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/?$',
        POSIndexView.as_view(),
        name='dashboard',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/dashboard/?$',
        POSIndexView.as_view(),
        name='dashboard.explicit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/?$',
        POSIndexView.as_view(),
        name='registers',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/create/?$',
        POSIndexView.as_view(),
        name='register.create',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/(?P<pk>\d+)/edit/?$',
        POSIndexView.as_view(),
        name='register.edit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/(?P<pk>\d+)/delete/?$',
        POSIndexView.as_view(),
        name='register.delete',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/sessions/?$',
        POSIndexView.as_view(),
        name='sessions',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/transactions/?$',
        POSIndexView.as_view(),
        name='transactions',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/audit/?$',
        POSIndexView.as_view(),
        name='audit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/reports/?$',
        POSIndexView.as_view(),
        name='reports',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos(?:/.*)?$',
        POSIndexView.as_view(),
        name='pos.index',
    ),
]

event_patterns = [
    re_path(
        r'^buy/api/',
        include((public_api_urlpatterns, 'public_api')),
    ),
    re_path(
        r'^buy/?$',
        PublicBuyView.as_view(),
        name='public.buy',
    ),
]
organizer_patterns = []
