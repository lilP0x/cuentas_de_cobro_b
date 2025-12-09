# db.py
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB", "facturacion")

client = AsyncIOMotorClient(MONGO_URI)
database = client[MONGO_DB_NAME]

# GridFS para PDFs de cuentas de cobro
gridfs_bucket = AsyncIOMotorGridFSBucket(database, bucket_name="invoicesPdf")
