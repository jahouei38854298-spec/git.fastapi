
import getpass

from database import admins_collection
from security import hash_password


USERNAME = "javad"


def main():
    admin = admins_collection.find_one({
        "username": USERNAME
    })

    if admin is None:
        print("خطا: مدیر با نام کاربری admin پیدا نشد.")
        return

    password = getpass.getpass("رمز عبور جدید را وارد کن: ")
    confirm_password = getpass.getpass("رمز عبور جدید را دوباره وارد کن: ")

    if not password:
        print("خطا: رمز عبور نمی‌تواند خالی باشد.")
        return

    if password != confirm_password:
        print("خطا: دو رمز عبور یکسان نیستند.")
        return

    hashed_password = hash_password(password)

    result = admins_collection.update_one(
        {"_id": admin["_id"]},
        {"$set": {"hashed_password": hashed_password}}
    )

    if result.modified_count == 1:
        print("رمز عبور مدیر با موفقیت تغییر کرد.")
    else:
        print("رمز جدید با مقدار قبلی یکسان است یا تغییری ثبت نشد.")


if __name__ == "__main__":
    main()
