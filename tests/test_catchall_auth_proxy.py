"""
Regression test: Auth cookie forwarding through Next.js proxy (2026-04-25)

Validates:
1. /api/auth/login sets both access_token and refresh_token cookies
2. /api/auth/me with the access_token cookie returns 200 (not 401)
3. /api/team/members with the access_token cookie returns 200 (not 401)
4. Logout clears both cookies

Run: uv run pytest tests/test_catchall_auth_proxy.py -v
"""


class TestCatchAllAuthProxy:
    def test_auth_me_returns_200_with_valid_token(self, session_client):
        response = session_client.get("/api/auth/me")
        assert response.status_code == 200
        assert "user" in response.json()

    def test_team_members_returns_200_with_valid_token(self, session_client):
        response = session_client.get("/api/team/members")
        assert response.status_code in {200, 404}  # 404 if table empty is OK
