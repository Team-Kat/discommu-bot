from pymongo.collection import Collection as CollectionType
from pymongo import MongoClient
from bson.objectid import ObjectId


class Collection:
    def __init__(self, collection: CollectionType):
        self._col = collection

    def __len__(self) -> int:
        return len(self.get())

    def IDStringfy(self, record: dict):
        record['_id'] = str(record['_id'])
        return record

    def get(self, filter: dict = None):
        return list(map(self.IDStringfy, self._col.find(filter)))

    def getOne(self, filter: dict = None):
        return self.IDStringfy(self._col.find_one(filter))

    def getByID(self, id: str):
        return self.getOne({'_id': ObjectId(id)})
