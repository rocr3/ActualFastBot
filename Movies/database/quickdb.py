import pymongo
from config import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]


async def add_all_file(fileid, name):
    try:
        collection = mydb["all_file_files"]
        item = {"fileid": str(fileid), "name": str(name)}
        result = collection.insert_one(item)
        logger.info("Added file with ID: %s", result.inserted_id)
        return result.inserted_id
    except Exception as e:
        logger.error("Error adding file to database: %s", e)


async def find_all_file(fileid):
    try:
        collection = mydb["all_file_files"]
        result = collection.find_one({"fileid": str(fileid)})
        if result:
            return result
        else:
            logger.info("No file found with ID: %s", fileid)
            return None
    except Exception as e:
        logger.error("Error finding file in database: %s", e)


async def add_verify_user(userid, time):
    try:
        collection = mydb["verify_user"]
        existing_doc = collection.find({"userid": str(userid)})
        if existing_doc:
            collection.delete_many({"userid": str(userid)})
            logger.info("Removed existing user with ID: %s", str(userid))
        new_doc = {"userid": str(userid), "time": int(time)}
        result = collection.insert_one(new_doc)
        logger.info("Added user with ID: %s", result.inserted_id)
        return result.inserted_id
    except Exception as e:
        logger.error("Error adding verify to database: %s", e)


async def find_verify_user(userid):
    try:
        collection = mydb["verify_user"]
        result = collection.find_one({"userid": str(userid)})
        if result:
            return result
        else:
            logger.info("No file found with ID: %s", userid)
            return None
    except Exception as e:
        logger.error("Error finding file in database: %s", e)
      
