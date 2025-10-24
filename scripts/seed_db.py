"""Seed the database with sample data.

Usage:
    python scripts/seed_db.py              # Seed all data
    python scripts/seed_db.py --clear      # Clear existing data first
    python scripts/seed_db.py --users      # Seed only users
    python scripts/seed_db.py --venues     # Seed only venues
"""
from __future__ import annotations

import argparse
import sys
import uuid
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.models.venue import Venue


def clear_data(db: Session) -> None:
    """Clear all existing data from the database."""
    print("Clearing existing data...")
    db.query(User).delete()
    db.query(Venue).delete()
    db.commit()
    print("✓ Data cleared")


def seed_users(db: Session) -> None:
    """Create sample users (idempotent - skips if already exists)."""
    users_data = [
        {"email": "alice@example.com", "full_name": "Alice Johnson", "points": 100},
        {"email": "bob@example.com", "full_name": "Bob Smith", "points": 250},
        {"email": "charlie@example.com", "full_name": "Charlie Brown", "points": 50},
    ]
    
    created = 0
    skipped = 0
    
    for user_data in users_data:
        # Check if user already exists
        existing = db.execute(
            select(User).where(User.email == user_data["email"])
        ).scalar_one_or_none()
        
        if existing:
            skipped += 1
            continue
        
        user = User(**user_data)
        db.add(user)
        created += 1
    
    db.commit()
    print(f"✓ Users: {created} created, {skipped} already exist")


def seed_venues(db: Session) -> None:
    """Create sample venues."""
    # Count existing venues
    existing_count = db.query(Venue).count()
    
    if existing_count >= 3:
        print(f"✓ Venues: {existing_count} already exist, skipping")
        return
    
    venues_to_create = 3 - existing_count
    venues = [Venue(id=uuid.uuid4()) for _ in range(venues_to_create)]
    
    for venue in venues:
        db.add(venue)
    
    db.commit()
    print(f"✓ Venues: {venues_to_create} created, {existing_count} already exist")


SEEDERS: dict[str, Callable[[Session], None]] = {
    "users": seed_users,
    "venues": seed_venues,
}


def main() -> int:
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="Seed the database with sample data")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--users",
        action="store_true",
        help="Seed only users",
    )
    parser.add_argument(
        "--venues",
        action="store_true",
        help="Seed only venues",
    )
    
    args = parser.parse_args()
    
    # Determine which seeders to run
    if args.users or args.venues:
        seeders_to_run = []
        if args.users:
            seeders_to_run.append(("users", seed_users))
        if args.venues:
            seeders_to_run.append(("venues", seed_venues))
    else:
        # Run all seeders
        seeders_to_run = list(SEEDERS.items())
    
    print("🌱 Starting database seeding...")
    
    db = SessionLocal()
    try:
        if args.clear:
            clear_data(db)
        
        for name, seeder in seeders_to_run:
            seeder(db)
        
        print("\n✅ Database seeded successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
