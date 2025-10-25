from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Followers, Users
from app.models.followers import StatusEnum
from tests.conftest import APITestContext


def _create_user(session_factory: sessionmaker[Session], *, email: str, full_name: str) -> UUID:
    with session_factory() as session:
        user = Users(
            email=email,
            full_name=full_name,
            oauth_provider="test",
            oauth_provider_id=f"oauth-{uuid4().hex}",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_create_follower_relationship(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    follower_id = _create_user(session_factory, email="follower@example.com", full_name="Follower")
    followed_id = _create_user(session_factory, email="followed@example.com", full_name="Followed")

    payload = {
        "follower_id": str(follower_id),
        "followed_id": str(followed_id),
    }

    response = client.post("/api/v1/followers", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["follower_id"] == str(follower_id)
    assert body["followed_id"] == str(followed_id)
    assert body["status"] == StatusEnum.PENDING.value
    assert events == [("follow.created", {"id": body["id"]})]

    with session_factory() as session:
        stored = session.execute(
            select(Followers).where(Followers.id == UUID(body["id"]))
        ).scalar_one_or_none()
        assert stored is not None
        assert stored.follower_id == follower_id
        assert stored.followed_id == followed_id


def test_prevent_duplicate_relationship(api_app: APITestContext) -> None:
    client, _session_factory, events = api_app
    follower_id = _create_user(
        _session_factory, email="dup-follower@example.com", full_name="Follower"
    )
    followed_id = _create_user(
        _session_factory, email="dup-followed@example.com", full_name="Followed"
    )

    payload = {
        "follower_id": str(follower_id),
        "followed_id": str(followed_id),
    }

    first = client.post("/api/v1/followers", json=payload)
    assert first.status_code == 201
    events.clear()

    duplicate = client.post("/api/v1/followers", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "follow_relationship_exists"
    assert events == []


def test_prevent_self_follow(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    user_id = _create_user(session_factory, email="self@example.com", full_name="Self")

    payload = {
        "follower_id": str(user_id),
        "followed_id": str(user_id),
    }

    response = client.post("/api/v1/followers", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "cannot_follow_self"
    assert events == []


def test_update_follow_status(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    follower_id = _create_user(
        session_factory, email="update-follower@example.com", full_name="Follower"
    )
    followed_id = _create_user(
        session_factory, email="update-followed@example.com", full_name="Followed"
    )

    response = client.post(
        "/api/v1/followers",
        json={"follower_id": str(follower_id), "followed_id": str(followed_id)},
    )
    assert response.status_code == 201
    follow_id = response.json()["id"]
    events.clear()

    update_response = client.put(
        f"/api/v1/followers/{follow_id}",
        json={"status": StatusEnum.ACCEPTED.value},
    )
    assert update_response.status_code == 200

    body = update_response.json()
    assert body["status"] == StatusEnum.ACCEPTED.value
    assert events == [("follow.updated", {"id": follow_id})]

    with session_factory() as session:
        stored = session.execute(
            select(Followers).where(Followers.id == UUID(follow_id))
        ).scalar_one_or_none()
        assert stored is not None
        assert stored.status == StatusEnum.ACCEPTED


def test_delete_follow_relationship(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    follower_id = _create_user(
        session_factory, email="delete-follower@example.com", full_name="Follower"
    )
    followed_id = _create_user(
        session_factory, email="delete-followed@example.com", full_name="Followed"
    )

    response = client.post(
        "/api/v1/followers",
        json={"follower_id": str(follower_id), "followed_id": str(followed_id)},
    )
    assert response.status_code == 201
    follow_id = response.json()["id"]
    events.clear()

    delete_response = client.delete(f"/api/v1/followers/{follow_id}")
    assert delete_response.status_code == 204
    assert events == [("follow.deleted", {"id": follow_id})]

    with session_factory() as session:
        assert (
            session.execute(
                select(Followers).where(Followers.id == UUID(follow_id))
            ).scalar_one_or_none()
            is None
        )

    get_response = client.get(f"/api/v1/followers/{follow_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "follow_relationship_not_found"


def test_list_followers_filters(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    follower_one = _create_user(
        session_factory, email="list-follower1@example.com", full_name="Follower One"
    )
    follower_two = _create_user(
        session_factory, email="list-follower2@example.com", full_name="Follower Two"
    )
    followed = _create_user(
        session_factory, email="list-followed@example.com", full_name="Followed"
    )

    client.post(
        "/api/v1/followers",
        json={"follower_id": str(follower_one), "followed_id": str(followed)},
    )
    client.post(
        "/api/v1/followers",
        json={"follower_id": str(follower_two), "followed_id": str(followed)},
    )
    events.clear()

    response = client.get(f"/api/v1/followers?followed_id={followed}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    follower_ids = {UUID(item["follower_id"]) for item in body}
    assert follower_ids == {follower_one, follower_two}
