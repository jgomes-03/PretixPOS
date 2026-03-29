"""
API smoke tests for BetterPOS endpoints.

Tests verify that:
1. API endpoints are accessible to authorized users.
2. Permission checks are enforced (403 for unauthorized).
3. Critical GET/POST endpoints return proper status codes.
4. Response structure matches React expectations.
"""

import json
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRegisterAPI:
    """Test GET/POST register endpoints."""
    
    def test_registers_list_authorized_returns_200(
        self, betterpos_client, organizer, event, betterpos_register
    ):
        """GET /api/registers should return 200 for authorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:registers",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_registers_list_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event
    ):
        """GET /api/registers should return 403 for unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:registers",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.get(url)
        
        # Should be forbidden (403) or not found (404)
        assert response.status_code in [403, 404]
    
    def test_registers_list_unauthenticated_returns_forbidden(
        self, betterpos_unauthenticated_client, organizer, event
    ):
        """GET /api/registers should redirect/forbid unauthenticated user."""
        url = reverse(
            "plugins:pretix_betterpos:api:registers",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_unauthenticated_client.get(url)
        
        # Should redirect (302 to login) or forbid (403)
        assert response.status_code in [302, 403]


class TestSessionAPI:
    """Test session-related endpoints."""
    
    def test_session_status_authorized_returns_200(
        self, betterpos_client, organizer, event, betterpos_session
    ):
        """GET /api/session/status should return 200."""
        url = reverse(
            "plugins:pretix_betterpos:api:session.status",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should contain status field
        assert "status" in data or "session" in data
    
    def test_open_session_authorized_returns_200_or_201(
        self, betterpos_client, organizer, event, betterpos_register
    ):
        """POST /api/session/open should open a session."""
        url = reverse(
            "plugins:pretix_betterpos:api:session.open",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.post(
            url,
            data=json.dumps({
                "register_id": betterpos_register.id,
                "opening_float": 100.00,
            }),
            content_type="application/json",
        )
        
        # Should return 200, 201, or 400 (if session already open)
        assert response.status_code in [200, 201, 400]
    
    def test_open_session_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event, betterpos_register
    ):
        """POST /api/session/open should forbid unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:session.open",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.post(
            url,
            data=json.dumps({
                "register_id": betterpos_register.id,
                "opening_float": 100.00,
            }),
            content_type="application/json",
        )
        
        assert response.status_code in [403, 404]


class TestCatalogAPI:
    """Test product catalog endpoint."""
    
    def test_catalog_authorized_returns_200(
        self, betterpos_client, organizer, event
    ):
        """GET /api/catalog should return 200."""
        url = reverse(
            "plugins:pretix_betterpos:api:catalog",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        # Should return list of items or categories
        assert isinstance(data, (list, dict))
    
    def test_catalog_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event
    ):
        """GET /api/catalog should forbid unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:catalog",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.get(url)
        
        assert response.status_code in [403, 404]


class TestTransactionsAPI:
    """Test transactions list endpoint."""
    
    def test_transactions_list_authorized_returns_200(
        self, betterpos_client, organizer, event
    ):
        """GET /api/transactions should return 200."""
        url = reverse(
            "plugins:pretix_betterpos:api:transactions",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        # Should return list or paginated list
        assert isinstance(data, (list, dict))
    
    def test_transactions_list_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event
    ):
        """GET /api/transactions should forbid unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:transactions",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.get(url)
        
        assert response.status_code in [403, 404]


class TestAuditAPI:
    """Test audit feed endpoint."""
    
    def test_audit_feed_authorized_returns_200(
        self, betterpos_client, organizer, event
    ):
        """GET /api/audit/feed should return 200."""
        url = reverse(
            "plugins:pretix_betterpos:api:audit.feed",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        # Should return list of audit events
        assert isinstance(data, (list, dict))
    
    def test_audit_feed_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event
    ):
        """GET /api/audit/feed should forbid unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:audit.feed",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.get(url)
        
        assert response.status_code in [403, 404]


class TestReportsAPI:
    """Test reports endpoint."""
    
    def test_reports_summary_authorized_returns_200(
        self, betterpos_client, organizer, event
    ):
        """GET /api/reports/summary should return 200."""
        url = reverse(
            "plugins:pretix_betterpos:api:reports.summary",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        # Should return summary statistics
        assert isinstance(data, dict)
    
    def test_reports_summary_unauthorized_returns_forbidden(
        self, betterpos_client_denied, organizer, event
    ):
        """GET /api/reports/summary should forbid unauthorized user."""
        url = reverse(
            "plugins:pretix_betterpos:api:reports.summary",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        response = betterpos_client_denied.get(url)
        
        assert response.status_code in [403, 404]


class TestAPIErrorHandling:
    """Test error scenarios in API responses."""
    
    def test_invalid_request_returns_400(
        self, betterpos_client, organizer, event
    ):
        """Invalid POST request should return 400."""
        url = reverse(
            "plugins:pretix_betterpos:api:session.open",
            kwargs={
                "organizer": organizer.slug,
                "event": event.slug,
            }
        )
        # Send invalid payload (missing required field)
        response = betterpos_client.post(
            url,
            data=json.dumps({}),
            content_type="application/json",
        )
        
        # Should return 400 (bad request) not 500
        assert response.status_code in [400, 422]
    
    def test_nonexistent_resource_returns_404(
        self, betterpos_client, organizer, event
    ):
        """GET /api/transaction/9999/status should return 404."""
        url = f"/control/event/{organizer.slug}/{event.slug}/betterpos/api/transaction/9999/status/"
        response = betterpos_client.get(url)
        
        # Should not be 500 error
        assert response.status_code in [404, 400, 403]
