"""Seed the database with example data from the recruitment task specification."""

import asyncio
from datetime import date

from sqlalchemy import select

from app.config import settings
from app.db.models import Vehicle, Owner, TransactionHistory, VehicleImage
from app.db.session import async_session, init_db


def _image_url(filename: str) -> str:
    """Return S3 URL if S3 is configured, otherwise a local relative filename."""
    if settings.S3_BUCKET and settings.S3_ENDPOINT_URL:
        base = settings.S3_ENDPOINT_URL.rstrip("/")
        return f"{base}/{settings.S3_BUCKET}/vehicle-images/{filename}"
    return filename


VEHICLES = [
    {"brand": "Toyota", "model": "Corolla", "year": 2018, "price": 45000, "is_available": False, "vehicle_type": "car"},
    {"brand": "BMW", "model": "X5", "year": 2020, "price": 180000, "is_available": True, "vehicle_type": "suv"},
    {"brand": "MAN", "model": "TGS", "year": 2017, "price": 350000, "is_available": True, "vehicle_type": "truck"},
    {"brand": "Honda", "model": "CBR600RR", "year": 2019, "price": 38000, "is_available": True, "vehicle_type": "motorcycle"},
    {"brand": "Skoda", "model": "Octavia", "year": 2016, "price": 32000, "is_available": True, "vehicle_type": "car"},
]

OWNERS = [
    {"first_name": "Jan", "last_name": "Kowalski", "city": "Warszawa", "email": "jan.kowalski@example.com"},
    {"first_name": "Anna", "last_name": "Nowak", "city": "Kraków", "email": "anna.nowak@example.com"},
    {"first_name": "Piotr", "last_name": "Zieliński", "city": "Gdańsk", "email": "piotr.zielinski@example.com"},
    {"first_name": "Maria", "last_name": "Wiśniewska", "city": "Poznań", "email": "maria.wisniewska@example.com"},
]

TRANSACTIONS = [
    {"vehicle_id": 1, "buyer_id": 1, "seller_id": None, "transaction_date": date(2021, 5, 12), "price": 45000},
    {"vehicle_id": 2, "buyer_id": 2, "seller_id": None, "transaction_date": date(2022, 1, 8), "price": 180000},
    {"vehicle_id": 3, "buyer_id": 3, "seller_id": None, "transaction_date": date(2019, 9, 20), "price": 350000},
    {"vehicle_id": 1, "buyer_id": 4, "seller_id": 1, "transaction_date": date(2023, 2, 15), "price": 40000},
    {"vehicle_id": 4, "buyer_id": 1, "seller_id": None, "transaction_date": date(2020, 7, 3), "price": 38000},
]

# Maps vehicle_id -> image filename (stored as relative name, resolved at runtime).
# This avoids baking the developer's absolute path into the DB – the classifier
# resolves relative names via settings.SAMPLE_IMAGES_DIR at query time.
VEHICLE_IMAGES = [
    {"vehicle_id": 1, "image_url": _image_url("1.png")},
    {"vehicle_id": 2, "image_url": _image_url("2.png")},
    {"vehicle_id": 3, "image_url": _image_url("3.png")},
    {"vehicle_id": 4, "image_url": _image_url("4.png")},
    {"vehicle_id": 5, "image_url": _image_url("5.png")},
]


async def seed_database() -> None:
    """Insert seed data if the database is empty."""
    await init_db()

    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(select(Vehicle).limit(1))
        if result.scalars().first() is not None:
            print("Database already seeded – skipping.")
            return

        # Insert vehicles
        for v in VEHICLES:
            session.add(Vehicle(**v))
        await session.flush()

        # Insert owners
        for o in OWNERS:
            session.add(Owner(**o))
        await session.flush()

        # Insert transactions
        for t in TRANSACTIONS:
            session.add(TransactionHistory(**t))
        await session.flush()

        # Insert vehicle images
        for img in VEHICLE_IMAGES:
            session.add(VehicleImage(**img))

        await session.commit()
        print("Database seeded successfully with example data.")


if __name__ == "__main__":
    asyncio.run(seed_database())
