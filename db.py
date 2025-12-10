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

async def get_gridfs_bucket():
	"""Retorna una instancia cacheada de AsyncIOMotorGridFSBucket.

	Crear la instancia al importar puede fallar porque Motor necesita un
	event loop. Esta función debe llamarse desde código async (handlers,
	startup events, etc.).
	"""
	if not hasattr(get_gridfs_bucket, "_bucket") or get_gridfs_bucket._bucket is None:
		get_gridfs_bucket._bucket = AsyncIOMotorGridFSBucket(database, bucket_name="invoicesPdf")
	return get_gridfs_bucket._bucket
