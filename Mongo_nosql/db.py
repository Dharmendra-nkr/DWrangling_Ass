import os
import re
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


# Load environment variables from a local .env file if present.
load_dotenv()


DEFAULT_DB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "port": 27017,
    "database": "Wrangling",
}


def get_db_config() -> Dict[str, Any]:
    """Collect connection settings from environment variables with sane defaults."""
    return {
        "host": os.getenv("MONGO_HOST", DEFAULT_DB_CONFIG["host"]),
        "port": int(os.getenv("MONGO_PORT", DEFAULT_DB_CONFIG["port"])),
        "database": os.getenv("MONGO_DATABASE", DEFAULT_DB_CONFIG["database"]),
        "username": os.getenv("MONGO_USER"),
        "password": os.getenv("MONGO_PASSWORD"),
    }


def get_database() -> Database:
    """Return a MongoDB database connection."""
    config = get_db_config()
    
    # Build connection string
    if config["username"] and config["password"]:
        connection_string = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/"
    else:
        connection_string = f"mongodb://{config['host']}:{config['port']}/"
    
    client = MongoClient(connection_string)
    return client[config["database"]]


def ensure_users_collection() -> None:
    """Create users collection with unique index on name."""
    db = get_database()
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    db.users.create_index("name", unique=True)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier(name: str) -> bool:
    return bool(_IDENT_RE.match(name))


def list_user_collections() -> List[str]:
    """Return all collections in the database, excluding system collections."""
    db = get_database()
    collections = db.list_collection_names()
    # Filter out system collections
    user_collections = [c for c in collections if not c.startswith("system.")]
    return sorted(user_collections)


def get_collection_fields(collection_name: str) -> List[str]:
    """Return field names from a sample document in the collection."""
    if not is_valid_identifier(collection_name):
        raise ValueError("invalid collection name")
    
    db = get_database()
    collection = db[collection_name]
    
    # Get a sample document to determine fields
    sample = collection.find_one()
    if sample:
        return list(sample.keys())
    return []


def fetch_collection_documents(collection_name: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch documents from a collection."""
    if not is_valid_identifier(collection_name):
        raise ValueError("invalid collection name")
    
    db = get_database()
    collection = db[collection_name]
    documents = list(collection.find().limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for doc in documents:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    
    return documents


def insert_user(name: str, password_hash: str) -> Dict[str, Any]:
    """Insert a new user and return the created document."""
    db = get_database()
    result = db.users.insert_one({"name": name, "password": password_hash})
    return {"_id": str(result.inserted_id), "name": name}


def find_user_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a user by name."""
    db = get_database()
    user = db.users.find_one({"name": name})
    if user:
        user["_id"] = str(user["_id"])
    return user


def insert_document(collection_name: str, document: Dict[str, Any]) -> str:
    """Insert a document into a collection and return the inserted ID."""
    if not is_valid_identifier(collection_name):
        raise ValueError("invalid collection name")
    
    db = get_database()
    result = db[collection_name].insert_one(document)
    return str(result.inserted_id)


def update_document(collection_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """Update a document by ID. Returns True if updated."""
    if not is_valid_identifier(collection_name):
        raise ValueError("invalid collection name")
    
    from bson import ObjectId
    db = get_database()
    result = db[collection_name].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": updates}
    )
    return result.modified_count > 0


def delete_document(collection_name: str, doc_id: str) -> bool:
    """Delete a document by ID. Returns True if deleted."""
    if not is_valid_identifier(collection_name):
        raise ValueError("invalid collection name")
    
    from bson import ObjectId
    db = get_database()
    result = db[collection_name].delete_one({"_id": ObjectId(doc_id)})
    return result.deleted_count > 0
