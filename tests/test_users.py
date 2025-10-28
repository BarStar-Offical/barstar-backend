from __future__ import annotations

from uuid import UUID

from app.models import Users
from tests.conftest import TestBase


class TestUsers(TestBase):
    __test__ = True

    def test_create(self):

        payload = {
            "email": "create@example.com",
            "full_name": "Create User",
            "oauth_provider": "github",
            "oauth_provider_id": "oauth-create",
        }

        response = self.client.post("/api/v1/users", json=payload)
        assert response.status_code == 201

        body = response.json()
        assert body["email"] == payload["email"]
        assert body["full_name"] == payload["full_name"]
        assert body["oauth_provider"] == payload["oauth_provider"]
        assert body["oauth_provider_id"] == payload["oauth_provider_id"]
        assert body["points"] == 0
        assert self.events == [("user.created", {"id": body["id"]})]

        with self.session_factory() as session:
            stored = session.get(Users, UUID(body["id"]))
            assert stored is not None
            assert stored.email == payload["email"]
            assert stored.full_name == payload["full_name"]


    def test_delete(self):
        payload = {
            "email": "delete@example.com",
            "full_name": "Delete Me",
            "oauth_provider": "apple",
            "oauth_provider_id": "oauth-delete",
        }

        response = self.client.post("/api/v1/users", json=payload)
        assert response.status_code == 201
        user_id = response.json()["id"]

        self.events.clear()

        delete_response = self.client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == 204
        assert self.events == [("user.deleted", {"id": user_id})]

        with self.session_factory() as session:
            assert session.get(Users, UUID(user_id)) is None

        get_response = self.client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404
        assert get_response.json()["detail"] == "user_not_found"

    def test_update(self):
        create_payload = {
            "email": "update@example.com",
            "full_name": "Before Update",
            "oauth_provider": "facebook",
            "oauth_provider_id": "oauth-update",
        }

        response = self.client.post("/api/v1/users", json=create_payload)
        assert response.status_code == 201
        user_id = response.json()["id"]

        self.events.clear()

        update_payload: dict[str, object] = {"full_name": "After Update", "points": 42}
        update_response = self.client.put(f"/api/v1/users/{user_id}", json=update_payload)
        assert update_response.status_code == 200

        body = update_response.json()
        assert body["full_name"] == "After Update"
        assert body["points"] == 42
        assert self.events == [("user.updated", {"id": user_id})]

        with self.session_factory() as session:
            stored = session.get(Users, UUID(user_id))
            assert stored is not None
            assert stored.full_name == "After Update"
            assert stored.points == 42

    def test_read(self):
        payload = {
            "email": "read@example.com",
            "full_name": "Read User",
            "oauth_provider": "github",
            "oauth_provider_id": "oauth-read",
        }
        response = self.client.post("/api/v1/users", json=payload)
        assert response.status_code == 201
        user_id = response.json()["id"]

        get_response = self.client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == payload["email"]
        assert get_response.json()["full_name"] == payload["full_name"]
        assert get_response.json()["oauth_provider"] == payload["oauth_provider"]
        assert get_response.json()["oauth_provider_id"] == payload["oauth_provider_id"]
        # no other data leaked
        assert set(get_response.json().keys()) == {
            "id",
            "email",
            "full_name",
            "oauth_provider",
            "oauth_provider_id",
            "points",
            "created_at",
            "updated_at",
        }

    def test_create_conflict(self):
        payload = {
            "email": "duplicate@example.com",
            "full_name": "Original",
            "oauth_provider": "google",
            "oauth_provider_id": "oauth-dup-1",
        }

        first = self.client.post("/api/v1/users", json=payload)
        assert first.status_code == 201
        self.events.clear()

        conflicting_payload = dict(payload)
        conflicting_payload["oauth_provider_id"] = "oauth-dup-2"

        response = self.client.post("/api/v1/users", json=conflicting_payload)
        assert response.status_code == 409
        assert response.json()["detail"] == "user_already_exists"
        assert self.events == []

    def test_list(self) -> None:
        self.events.clear()

        payload_one = {
            "email": "list-one@example.com",
            "full_name": "List One",
            "oauth_provider": "github",
            "oauth_provider_id": "oauth-list-1",
        }
        payload_two = {
            "email": "list-two@example.com",
            "full_name": "List Two",
            "oauth_provider": "google",
            "oauth_provider_id": "oauth-list-2",
        }

        first = self.client.post("/api/v1/users", json=payload_one)
        assert first.status_code == 201
        second = self.client.post("/api/v1/users", json=payload_two)
        assert second.status_code == 201

        response = self.client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        emails = [item["email"] for item in data]
        assert emails == [payload_two["email"], payload_one["email"]]
