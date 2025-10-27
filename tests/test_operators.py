from __future__ import annotations

from typing import Sequence
from uuid import UUID, uuid4

from app.models import Operators, Venues
from app.models.operators import OperatorRole
from tests.conftest import APITestContext


def test_operator_creation_defaults(api_app: APITestContext) -> None:
    _client, session_factory, _events = api_app

    with session_factory() as session:
        operator = Operators(
            email="operator@example.com",
            full_name="Operator Example",
            phone_number="+15555550100",
        )
        session.add(operator)
        session.commit()
        operator_id = operator.id

    with session_factory() as session:
        stored = session.get(Operators, operator_id)
        assert stored is not None
        assert stored.role == OperatorRole.STAFF
        assert stored.is_active is True
        assert stored.created_at is not None
        assert stored.updated_at is not None
        assert stored.venues == []
        assert stored.venue_ids == []


def test_operator_venue_relationship(api_app: APITestContext) -> None:
    _client, session_factory, _events = api_app

    with session_factory() as session:
        operator = Operators(
            email="relationship@example.com",
            full_name="Relationship Operator",
            phone_number="+15555550101",
            role=OperatorRole.OWNER,
        )
        venue_one = Venues(
            name="Venue One",
            email="venue1@example.com",
            owner_id=uuid4(),
            experience_points=0,
        )
        venue_two = Venues(
            name="Venue Two",
            email="venue2@example.com",
            owner_id=uuid4(),
            experience_points=10,
        )
        operator.venues.extend([venue_one, venue_two])
        session.add(operator)
        session.commit()
        operator_id = operator.id
        venue_ids = {venue_one.id, venue_two.id}

    with session_factory() as session:
        stored = session.get(Operators, operator_id)
        assert stored is not None
        retrieved_ids = {venue.id for venue in stored.venues}
        assert retrieved_ids == venue_ids
        assert set(stored.venue_ids) == venue_ids

        for venue_id in venue_ids:
            venue = session.get(Venues, venue_id)
            assert venue is not None
            assert {item.id for item in venue.operators} == {operator_id}


def test_operator_role_persistence(api_app: APITestContext) -> None:
    _client, session_factory, _events = api_app

    with session_factory() as session:
        operator = Operators(
            email="owner@example.com",
            full_name="Owner Example",
            phone_number="+15555550102",
            role=OperatorRole.OWNER,
            is_active=False,
        )
        session.add(operator)
        session.commit()
        operator_id = operator.id

    with session_factory() as session:
        stored = session.get(Operators, operator_id)
        assert stored is not None
        assert stored.role == OperatorRole.OWNER
        assert stored.is_active is False


# CODEX-LOCK: API endpoint coverage starts here.


def test_create_operator_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    venue_ids = _seed_venues(session_factory, count=2)
    payload = {
        "email": "api-operator@example.com",
        "full_name": "API Operator",
        "phone_number": "+15555550110",
        "role": "owner",
        "venue_ids": [str(venue_id) for venue_id in venue_ids],
        "is_active": False,
    }

    response = client.post("/api/v1/operators", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "owner"
    assert data["is_active"] is False
    assert set(UUID(item) for item in data["venue_ids"]) == set(venue_ids)

    with session_factory() as session:
        stored = session.get(Operators, UUID(data["id"]))
        assert stored is not None
        assert stored.role == OperatorRole.OWNER
        assert stored.is_active is False
        assert {venue.id for venue in stored.venues} == set(venue_ids)

    assert events == [("operator.created", {"id": data["id"]})]


def test_list_operator_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        first = Operators(
            email="list-one@example.com",
            full_name="List One",
            phone_number="+15555550111",
        )
        second = Operators(
            email="list-two@example.com",
            full_name="List Two",
            phone_number="+15555550112",
            role=OperatorRole.OWNER,
        )
        session.add_all([first, second])
        session.commit()
        first_id, second_id = first.id, second.id

    response = client.get("/api/v1/operators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert UUID(data[0]["id"]) == second_id  # newest first
    assert UUID(data[1]["id"]) == first_id


def test_get_operator_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        operator = Operators(
            email="get-operator@example.com",
            full_name="Get Operator",
            phone_number="+15555550113",
            role=OperatorRole.OWNER,
        )
        session.add(operator)
        session.commit()
        operator_id = operator.id

    response = client.get(f"/api/v1/operators/{operator_id}")
    assert response.status_code == 200
    data = response.json()
    assert UUID(data["id"]) == operator_id
    assert data["full_name"] == "Get Operator"
    assert data["role"] == "owner"


def test_update_operator_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    original_venues = _seed_venues(session_factory, count=1)
    updated_venues = _seed_venues(session_factory, count=2)

    with session_factory() as session:
        operator = Operators(
            email="update-operator@example.com",
            full_name="Update Me",
            phone_number="+15555550114",
        )
        operator.venues = session.query(Venues).filter(Venues.id.in_(original_venues)).all()
        session.add(operator)
        session.commit()
        operator_id = operator.id

    payload = {
        "email": "updated@example.com",
        "full_name": "Updated Name",
        "phone_number": "+15555550115",
        "role": "owner",
        "venue_ids": [str(venue_id) for venue_id in updated_venues],
        "is_active": False,
    }

    response = client.put(f"/api/v1/operators/{operator_id}", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "owner"
    assert data["is_active"] is False
    assert set(UUID(item) for item in data["venue_ids"]) == set(updated_venues)

    with session_factory() as session:
        stored = session.get(Operators, operator_id)
        assert stored is not None
        assert stored.role == OperatorRole.OWNER
        assert stored.is_active is False
        assert {venue.id for venue in stored.venues} == set(updated_venues)

    assert events == [("operator.updated", {"id": str(operator_id)})]


def test_delete_operator_endpoint(api_app: APITestContext) -> None:
    client, session_factory, events = api_app
    events.clear()

    with session_factory() as session:
        operator = Operators(
            email="delete-operator@example.com",
            full_name="Delete Me",
            phone_number="+15555550116",
        )
        session.add(operator)
        session.commit()
        operator_id = operator.id

    response = client.delete(f"/api/v1/operators/{operator_id}")
    assert response.status_code == 204

    with session_factory() as session:
        assert session.get(Operators, operator_id) is None

    assert events == [("operator.deleted", {"id": str(operator_id)})]


def _seed_venues(session_factory, *, count: int) -> Sequence[UUID]:
    """Create venues with minimal required data for tests."""

    with session_factory() as session:
        venues = [
            Venues(
                name=f"Test Venue {idx}",
                email=f"venue{uuid4()}@example.com",
                owner_id=uuid4(),
                experience_points=idx,
            )
            for idx in range(count)
        ]
        session.add_all(venues)
        session.commit()
        return [venue.id for venue in venues]
