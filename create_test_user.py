#!/usr/bin/env python3
"""
Create a test user and session for backend testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import uuid

async def create_test_user():
    # Connect to MongoDB
    mongo_url = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongo_url)
    db = client["test_database"]
    
    # Create test user
    test_user = {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "picture": None,
        "created_at": datetime.now(timezone.utc)
    }
    
    # Insert user
    await db.users.insert_one(test_user)
    
    # Create test session
    session_token = str(uuid.uuid4())
    test_session = {
        "id": str(uuid.uuid4()),
        "user_id": test_user["id"],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    
    # Insert session
    await db.sessions.insert_one(test_session)
    
    print(f"Test user created: {test_user['id']}")
    print(f"Test session token: {session_token}")
    
    client.close()
    return test_user["id"], session_token

if __name__ == "__main__":
    user_id, token = asyncio.run(create_test_user())