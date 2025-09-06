#!/usr/bin/env python3
"""
Clean up test user and session from database
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_test_user():
    # Connect to MongoDB
    mongo_url = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongo_url)
    db = client["test_database"]
    
    # Delete test user and session
    await db.users.delete_many({"email": "test@example.com"})
    await db.sessions.delete_many({"session_token": "5a7e5ca6-69c0-4434-ae3c-759ff027f1fd"})
    
    print("Test user and session cleaned up")
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_test_user())