import os
import logging
from typing import Generator
from contextlib import asynccontextmanager

import pymongo
from pymongo.database import Database
from fastapi import FastAPI, Request, Depends
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")

if not MONGODB_URI or not MONGODB_DB:
    raise RuntimeError("MONGODB_URI and MONGODB_DB must be set in environment variables")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle MongoDB connection lifecycle for FastAPI app."""
    logger.info("Connecting to MongoDB")
    client = pymongo.MongoClient(MONGODB_URI)
    try:
        client.admin.command("ping")
        logger.info("MongoDB ping succeeded")
    except Exception as e:  # pragma: no cover
        logger.warning("MongoDB ping failed: %s", e)

    app.state.mongo_client = client
    app.state.db = client[MONGODB_DB]

    yield  # Hand control back to FastAPI

    logger.info("Closing MongoDB connection")
    client.close()


app = FastAPI(lifespan=lifespan)


def get_db(request: Request) -> Generator[Database, None, None]:
    """Dependency to provide MongoDB Database instance."""
    db = getattr(request.app.state, "db", None)
    if db is None:
        # Fallback: create temp client if not initialized
        client = pymongo.MongoClient(MONGODB_URI)
        try:
            yield client[MONGODB_DB]
        finally:
            client.close()
    else:
        yield db


# Example route
@app.get("/items")
def list_items(db: Database = Depends(get_db)):
    return list(db.items.find())
