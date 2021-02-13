from pymongo.collection import Collection as CollectionType
from pymongo import MongoClient
from bson.objectid import ObjectId


class Collection(CollectionType):
    def __init__(self, database: MongoClient, name: str):
        super().__init__(database, name)

    def __len__(self) -> int:
        return len(self.get())

    def IDStringfy(self, record: dict):
        if not record:
            return None

        record['_id'] = str(record['_id'])
        return record

    def get(self, filter: dict = None):
        return list(map(self.IDStringfy, self.find(filter)))

    def getOne(self, filter: dict = None):
        return self.IDStringfy(self.find_one(filter))

    def getByID(self, id: str):
        return self.getOne({'_id': ObjectId(id)})

    def deleteByID(self, id: str):
        return self.delete_one({'_id': ObjectId(id)})

    def updateByID(self, id: str, setVal: dict):
        return self.update_one({'_id': ObjectId(id)}, {'$set': setVal})
