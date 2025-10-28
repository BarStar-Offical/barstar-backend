from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select

from app.models import Followers, Users
from app.models.followers import StatusEnum
from tests.conftest import TestBase


class TestFollowers(TestBase):
    __test__ = True

    def _create_user(self, *, email: str, full_name: str) -> UUID:
        with self.session_factory() as session:
            user = Users(
                email=email,
                full_name=full_name,
                oauth_provider="test",
                oauth_provider_id=f"oauth-{uuid4().hex}",
                points=0,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id

    def test_create(self) -> None:
        self.events.clear()
        follower_id = self._create_user(
            email="follower@example.com",
            full_name="Follower",
        )
        followed_id = self._create_user(
            email="followed@example.com",
            full_name="Followed",
        )

        payload = {
            "follower_id": str(follower_id),
            "followed_id": str(followed_id),
        }

        response = self.client.post("/api/v1/followers", json=payload)
        assert response.status_code == 201

        body = response.json()
        assert body["follower_id"] == str(follower_id)
        assert body["followed_id"] == str(followed_id)
        assert body["status"] == StatusEnum.PENDING.value
        assert self.events == [("follow.created", {"id": body["id"]})]

        with self.session_factory() as session:
            stored = session.execute(
                select(Followers).where(Followers.id == UUID(body["id"]))
            ).scalar_one_or_none()
            assert stored is not None
            assert stored.follower_id == follower_id
            assert stored.followed_id == followed_id

    def test_delete(self) -> None:
        follower_id = self._create_user(
            email="delete-follower@example.com",
            full_name="Follower",
        )
        followed_id = self._create_user(
            email="delete-followed@example.com",
            full_name="Followed",
        )

        response = self.client.post(
            "/api/v1/followers",
            json={"follower_id": str(follower_id), "followed_id": str(followed_id)},
        )
        assert response.status_code == 201
        follow_id = response.json()["id"]
        self.events.clear()

        delete_response = self.client.delete(f"/api/v1/followers/{follow_id}")
        assert delete_response.status_code == 204
        assert self.events == [("follow.deleted", {"id": follow_id})]

        with self.session_factory() as session:
            remaining = session.execute(
                select(Followers).where(Followers.id == UUID(follow_id))
            ).scalar_one_or_none()
            assert remaining is None

        get_response = self.client.get(f"/api/v1/followers/{follow_id}")
        assert get_response.status_code == 404
        assert get_response.json()["detail"] == "follow_relationship_not_found"

    def test_update(self) -> None:
        follower_id = self._create_user(
            email="update-follower@example.com",
            full_name="Follower",
        )
        followed_id = self._create_user(
            email="update-followed@example.com",
            full_name="Followed",
        )

        response = self.client.post(
            "/api/v1/followers",
            json={"follower_id": str(follower_id), "followed_id": str(followed_id)},
        )
        assert response.status_code == 201
        follow_id = response.json()["id"]
        self.events.clear()

        update_response = self.client.put(
            f"/api/v1/followers/{follow_id}",
            json={"status": StatusEnum.ACCEPTED.value},
        )
        assert update_response.status_code == 200

        body = update_response.json()
        assert body["status"] == StatusEnum.ACCEPTED.value
        assert self.events == [("follow.updated", {"id": follow_id})]

        with self.session_factory() as session:
            stored = session.execute(
                select(Followers).where(Followers.id == UUID(follow_id))
            ).scalar_one_or_none()
            assert stored is not None
            assert stored.status == StatusEnum.ACCEPTED

    def test_read(self) -> None:
        follower_id = self._create_user(
            email="read-follower@example.com",
            full_name="Follower",
        )
        followed_id = self._create_user(
            email="read-followed@example.com",
            full_name="Followed",
        )

        response = self.client.post(
            "/api/v1/followers",
            json={"follower_id": str(follower_id), "followed_id": str(followed_id)},
        )
        assert response.status_code == 201
        follow_id = response.json()["id"]

        get_response = self.client.get(f"/api/v1/followers/{follow_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert UUID(data["id"]) == UUID(follow_id)
        assert data["follower_id"] == str(follower_id)
        assert data["followed_id"] == str(followed_id)

    def test_create_conflict(self) -> None:
        follower_id = self._create_user(
            email="dup-follower@example.com",
            full_name="Follower",
        )
        followed_id = self._create_user(
            email="dup-followed@example.com",
            full_name="Followed",
        )

        payload = {
            "follower_id": str(follower_id),
            "followed_id": str(followed_id),
        }

        first = self.client.post("/api/v1/followers", json=payload)
        assert first.status_code == 201
        self.events.clear()

        duplicate = self.client.post("/api/v1/followers", json=payload)
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"] == "follow_relationship_exists"
        assert self.events == []

    def test_list(self) -> None:
        follower_one = self._create_user(
            email="list-follower1@example.com", full_name="Follower One"
        )
        follower_two = self._create_user(
            email="list-follower2@example.com", full_name="Follower Two"
        )
        followed = self._create_user(
            email="list-followed@example.com", full_name="Followed"
        )

        self.client.post(
            "/api/v1/followers",
            json={"follower_id": str(follower_one), "followed_id": str(followed)},
        )
        self.client.post(
            "/api/v1/followers",
            json={"follower_id": str(follower_two), "followed_id": str(followed)},
        )
        self.events.clear()

        response = self.client.get(f"/api/v1/followers?followed_id={followed}")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        follower_ids = {UUID(item["follower_id"]) for item in body}
        assert follower_ids == {follower_one, follower_two}

    def test_prevent_self_follow(self) -> None:
        user_id = self._create_user(email="self@example.com", full_name="Self")

        payload = {
            "follower_id": str(user_id),
            "followed_id": str(user_id),
        }

        response = self.client.post("/api/v1/followers", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "cannot_follow_self"
        assert self.events == []
