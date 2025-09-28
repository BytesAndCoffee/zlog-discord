

import os
from typing import List, Type

from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func, inspect as sqla_inspect
from sqlalchemy.orm import sessionmaker, class_mapper
from sqlalchemy.exc import SQLAlchemyError

# Import the generated models module (created by autogen)
import models as models


def get_engine():
    """
    Create an engine using the same PlanetScale connection details from .env.
    Uses PyMySQL and passes the CA bundle so TLS works.
    """
    load_dotenv()
    user = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    database = os.getenv("DATABASE")

    if not all([user, password, host, database]):
        raise RuntimeError("Missing one or more DB env vars: DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE")

    # PyMySQL + PlanetScale: supply CA bundle via query param
    conn_str = (
        f"mysql+pymysql://{user}:{password}@{host}/{database}"
        "?ssl_ca=/etc/ssl/cert.pem"
    )
    return create_engine(conn_str, future=True)


def discover_mapped_classes() -> List[Type]:
    """
    Introspect the models module to find all SQLAlchemy mapped classes.
    Works whether sqlacodegen emitted a 1.x-style Base or 2.0 DeclarativeBase.
    """
    mapped = []
    for name, obj in vars(models).items():
        if isinstance(obj, type):
            try:
                # If this succeeds, it's a mapped class
                class_mapper(obj)
                mapped.append(obj)
            except Exception:
                continue
    mapped.sort(key=lambda c: c.__name__)
    return mapped


def main():
    engine = get_engine()
    insp = sqla_inspect(engine)

    # Show DB connectivity & available tables
    print("✅ Connected. Tables present in DB:")
    for t in insp.get_table_names():
        print(f"  - {t}")

    # Discover mapped classes from generated models.py
    mapped_classes = discover_mapped_classes()
    if not mapped_classes:
        raise RuntimeError("No mapped classes discovered in zlog_discord.models. Is models.py generated?")

    print("\n🧪 Testing mapped classes:")
    Session = sessionmaker(bind=engine, future=True)
    with Session() as session:
        for cls in mapped_classes:
            table = getattr(cls, "__tablename__", getattr(getattr(cls, "__table__", None), "name", None))
            print(f"\n• {cls.__name__} (table: {table})")

            # 1) Verify the table exists in the database
            if table and table in insp.get_table_names():
                print("  - Table exists ✅")
            else:
                print("  - Table NOT found in DB ⚠️")

            # 2) Try a COUNT(*)
            try:
                total = session.execute(select(func.count()).select_from(cls)).scalar_one()
                print(f"  - Row count: {total}")
            except SQLAlchemyError as e:
                print(f"  - COUNT failed: {e.__class__.__name__}: {e}")

            # 3) Fetch a single row to validate column mapping
            try:
                row_obj = session.execute(select(cls).limit(1)).scalars().first()
                if row_obj is None:
                    print("  - No rows to sample (table empty) ℹ️")
                else:
                    # Show a compact dict of column -> value
                    data = {}
                    for col in getattr(cls, "__table__").columns:
                        data[col.name] = getattr(row_obj, col.name)
                    print(f"  - Sample row: {data}")
            except SQLAlchemyError as e:
                print(f"  - SELECT 1 failed: {e.__class__.__name__}: {e}")

    print("\n✅ Model test complete.")


if __name__ == "__main__":
    main()
