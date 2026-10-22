from datetime import date

from pydantic import BaseModel, EmailStr, Field, ValidationError


# ==========================================
# مدل اعتبارسنجی اطلاعات کاربر
# ==========================================

class Student(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )

    age: int = Field(
        ge=0,
        le=120,
    )

    birth_date: date

    father_name: str = Field(
        min_length=2,
        max_length=50,
    )

    birth_place: str = Field(
        min_length=2,
        max_length=100,
    )

    phone: str = Field(
        pattern=r"^09\d{9}$",
    )

    email: EmailStr

    address: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )


# ==========================================
# تبدیل خطاهای اعتبارسنجی به فارسی
# ==========================================

def get_persian_errors(
    exc: ValidationError,
) -> list[str]:

    messages = {
        "name": "نام باید بین ۲ تا ۵۰ کاراکتر باشد.",
        "age": "سن باید عددی بین ۰ تا ۱۲۰ باشد.",
        "birth_date": "تاریخ تولد معتبر نیست.",
        "father_name": "نام پدر باید بین ۲ تا ۵۰ کاراکتر باشد.",
        "birth_place": "محل تولد باید بین ۲ تا ۱۰۰ کاراکتر باشد.",
        "phone": "شماره تلفن باید با 09 شروع شود و ۱۱ رقم داشته باشد.",
        "email": "لطفاً یک ایمیل معتبر وارد کنید.",
        "address": "آدرس باید بین ۲ تا ۲۰۰ کاراکتر باشد.",
    }

    errors = []

    for error in exc.errors():
        field = str(error["loc"][-1])

        message = messages.get(
            field,
            "یکی از اطلاعات واردشده معتبر نیست.",
        )

        if message not in errors:
            errors.append(message)

    return errors
