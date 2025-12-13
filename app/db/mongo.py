import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "facturacion")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
bucket = AsyncIOMotorGridFSBucket(db, bucket_name="invoicesPdf")
