"""
BetterPOS pytest fixtures and configuration.

This file provides reusable test infrastructure for BetterPOS plugin tests,
following patterns from pretix core test suite.
"""

import pytest
from django.test import override_settings
from django_scopes import scopes_disabled

# Import fixtures from pretix test suite
from pretix.testutils.fixtures import event, organizer, user  # noqa: F401


@pytest.fixture
@scopes_disabled()
def betterpos_user_team(organizer, user):
    """Create a team with the given user as team member."""
    from pretix.base.models import Team
    
    team = Team.objects.create(
        organizer=organizer,
        name="BetterPOS Team",
    )
    team.members.add(user)
    return team


@pytest.fixture
@scopes_disabled()
def betterpos_user_with_perms(organizer, user, betterpos_user_team):
    """Assign BetterPOS POS permissions to the user.
    
    Grants: can_view_pos, can_sell_pos, can_discount_pos, can_refund_pos,
    can_manage_registers_pos, can_session_control_pos, can_view_audit_pos.
    """
    from pretix_betterpos.permissions import (
        POS_PERMISSION_CAN_VIEW,
        POS_PERMISSION_CAN_SELL,
        POS_PERMISSION_CAN_DISCOUNT,
        POS_PERMISSION_CAN_REFUND,
        POS_PERMISSION_CAN_MANAGE_REGISTERS,
        POS_PERMISSION_CAN_SESSION_CONTROL,
        POS_PERMISSION_CAN_VIEW_AUDIT,
    )
    
    perms = [
        POS_PERMISSION_CAN_VIEW,
        POS_PERMISSION_CAN_SELL,
        POS_PERMISSION_CAN_DISCOUNT,
        POS_PERMISSION_CAN_REFUND,
        POS_PERMISSION_CAN_MANAGE_REGISTERS,
        POS_PERMISSION_CAN_SESSION_CONTROL,
        POS_PERMISSION_CAN_VIEW_AUDIT,
    ]
    
    for perm in perms:
        setattr(betterpos_user_team, perm, True)
    betterpos_user_team.save()
    
    return user


@pytest.fixture
@scopes_disabled()
def betterpos_user_view_only(organizer):
    """Create a user with only can_view_pos permission (no sell/refund/admin)."""
    from pretix.base.models import Team, User
    from pretix_betterpos.permissions import POS_PERMISSION_CAN_VIEW
    
    user = User.objects.create_user(
        email="viewer@example.com",
        password="test",
        name="View Only User"
    )
    team = Team.objects.create(
        organizer=organizer,
        name="View Team",
    )
    team.members.add(user)
    
    setattr(team, POS_PERMISSION_CAN_VIEW, True)
    team.save()
    
    return user


@pytest.fixture
@scopes_disabled()
def betterpos_user_denied(organizer):
    """Create a user with NO BetterPOS permissions."""
    from pretix.base.models import Team, User
    
    user = User.objects.create_user(
        email="denied@example.com",
        password="test",
        name="Denied User"
    )
    team = Team.objects.create(
        organizer=organizer,
        name="Denied Team",
    )
    team.members.add(user)
    # No permissions set
    return user


@pytest.fixture
@scopes_disabled()
def betterpos_register(event):
    """Create a test BetterPOS register for the event."""
    from pretix_betterpos.models import BetterposRegister
    
    return BetterposRegister.objects.create(
        event=event,
        name="Test Register 1",
        code="reg-001",
        default_currency="EUR",
        is_active=True,
    )


@pytest.fixture
@scopes_disabled()
def betterpos_session(betterpos_register, betterpos_user_with_perms):
    """Create an open BetterPOS cash session."""
    from pretix_betterpos.models import BetterposCashSession
    
    session = BetterposCashSession.objects.create(
        register=betterpos_register,
        opened_by=betterpos_user_with_perms,
        opening_float=100.00,
        status="open",
    )
    return session


@pytest.fixture
def betterpos_client(betterpos_user_with_perms, event, client):
    """Create an authenticated Django test client logged in as a manager user."""
    client.force_login(betterpos_user_with_perms)
    # Store event context for convenience
    client.event = event
    client.register = None  # Set by tests if needed
    return client


@pytest.fixture
def betterpos_client_view_only(betterpos_user_view_only, event, client):
    """Create an authenticated Django test client logged in as view-only user."""
    client.force_login(betterpos_user_view_only)
    client.event = event
    return client


@pytest.fixture
def betterpos_client_denied(betterpos_user_denied, event, client):
    """Create an authenticated Django test client logged in as a user with NO POS access."""
    client.force_login(betterpos_user_denied)
    client.event = event
    return client


@pytest.fixture
def betterpos_unauthenticated_client(client):
    """Return unauthenticated Django test client."""
    return client
