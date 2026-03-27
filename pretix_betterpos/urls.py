from django.urls import include, path

from .api.urls import api_urlpatterns
from .views.control import RegisterListView, SessionMonitorView
from .views.pos import POSIndexView


event_patterns = [
    path('betterpos/', POSIndexView.as_view(), name='pos.index'),
    path('betterpos/control/registers/', RegisterListView.as_view(), name='control.registers'),
    path('betterpos/control/sessions/', SessionMonitorView.as_view(), name='control.sessions'),
    path('betterpos/api/', include((api_urlpatterns, 'api'))),
]

organizer_patterns = []

urlpatterns = []
