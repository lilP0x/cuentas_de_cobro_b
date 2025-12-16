from app.db.mongo import db
from pymongo import ReturnDocument

async def get_next_sequence(name: str) -> int:
    doc = await db["counters"].find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(doc["seq"])
