from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

__version__ = '0.1.0'


class PluginApp(AppConfig):
    name = 'pretix_betterpos'
    verbose_name = 'Pretix BetterPOS'

    class PretixPluginMeta:
        name = _('BetterPOS')
        author = 'BetterPOS Team'
        category = 'FEATURE'
        description = _('Point of sale plugin for on-site event operations')
        visible = True
        version = __version__
        compatibility = 'pretix>=4.0.0'

    def ready(self):
        from . import signals  # noqa


default_app_config = 'pretix_betterpos.PluginApp'
