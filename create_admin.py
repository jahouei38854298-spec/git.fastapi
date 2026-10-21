
import getpass

from database import admins_collection
from security import hash_password


# دریافت نام کاربری مدیر
username = input("نام کاربری مدیر را وارد کنید: ").strip()

# دریافت رمز عبور بدون نمایش آن در ترمینال
password = getpass.getpass("رمز عبور مدیر را وارد کنید: ")

# بررسی خالی نبودن اطلاعات
if not username or not password:
    print("نام کاربری و رمز عبور نمی‌توانند خالی باشند.")

else:
    # بررسی تکراری نبودن نام کاربری
    existing_admin = admins_collection.find_one(
        {"username": username}
    )

    if existing_admin:
        print("این نام کاربری قبلاً ثبت شده است.")

    else:
        # تبدیل رمز عبور به هش
        hashed_password = hash_password(password)

        # ذخیره حساب مدیر در MongoDB
        admins_collection.insert_one({
            "username": username,
            "hashed_password": hashed_password
        })

        print("حساب مدیر با موفقیت ساخته شد.")
