import os

from pymongo import MongoClient

# آدرس اتصال به MongoDB
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://localhost:27017/",
)

# اتصال به دیتابیس
client = MongoClient(MONGODB_URL)

# انتخاب دیتابیس پروژه
db = client["fastapi_db"]

# مجموعه کاربران
students_collection = db["students"]

# مجموعه حساب‌های مدیران
admins_collection = db["admins"]
