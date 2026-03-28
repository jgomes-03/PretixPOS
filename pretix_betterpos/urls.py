from django.urls import include, re_path

from .api.urls import api_urlpatterns
from .views.control import (
    AuditListView,
    DashboardView,
    RegisterCreateView,
    RegisterDeleteView,
    RegisterListView,
    RegisterUpdateView,
    ReportsView,
    SessionListView,
    TransactionListView,
)
from .views.pos import POSIndexView

urlpatterns = [
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/api/',
        include((api_urlpatterns, 'api')),
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/?$',
        DashboardView.as_view(),
        name='dashboard',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/dashboard/?$',
        DashboardView.as_view(),
        name='dashboard.explicit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/?$',
        RegisterListView.as_view(),
        name='registers',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/create/?$',
        RegisterCreateView.as_view(),
        name='register.create',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/(?P<pk>\d+)/edit/?$',
        RegisterUpdateView.as_view(),
        name='register.edit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/registers/(?P<pk>\d+)/delete/?$',
        RegisterDeleteView.as_view(),
        name='register.delete',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/sessions/?$',
        SessionListView.as_view(),
        name='sessions',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/transactions/?$',
        TransactionListView.as_view(),
        name='transactions',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/audit/?$',
        AuditListView.as_view(),
        name='audit',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos/admin/reports/?$',
        ReportsView.as_view(),
        name='reports',
    ),
    re_path(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/betterpos(?:/.*)?$',
        POSIndexView.as_view(),
        name='pos.index',
    ),
]

event_patterns = []
organizer_patterns = []
