from django import forms
from django.utils.translation import gettext_lazy as _
from pretix.base.forms import SettingsForm


class BetterPOSSettingsForm(SettingsForm):
    betterpos_selfservice_enabled = forms.BooleanField(
        label=_("Enable BetterPOS selfservice"),
        required=False,
        help_text=_("Allow customers to access the public selfservice buy page for this event."),
    )
