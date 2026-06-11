import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# We create the connection client
client = AsyncIOMotorClient(MONGO_URI)

# We create a database called "docmind_os"
db = client.docmind_os

# We create a collection (like a SQL table) called "documents"
documents_collection = db.documents
