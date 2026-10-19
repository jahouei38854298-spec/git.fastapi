
import re
from datetime import date

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field, ValidationError

from database import students_collection


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# تبدیل شناسه دریافتی به ObjectId
def parse_student_id(student_id: str) -> ObjectId:
    try:
        return ObjectId(student_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid student ID",
        )


# تبدیل سند MongoDB به داده قابل نمایش یا ارسال در JSON
def serialize_student(student: dict) -> dict:
    return {**student, "_id": str(student["_id"])}


# مدل اطلاعات کاربر
class Student(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=0, le=120)
    birth_date: date
    father_name: str = Field(min_length=2, max_length=50)
    birth_place: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^09\d{9}$")
    email: EmailStr
    address: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )


# تبدیل خطاهای اعتبارسنجی به پیام فارسی
def get_persian_errors(exc: ValidationError) -> list[str]:
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


# صفحه اصلی و جست‌وجوی کاربران
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    message: str | None = None,
    name: str = "",
    phone: str = "",
    email: str = "",
):
    search_filter = {}

    if name.strip():
        search_filter["name"] = {
            "$regex": re.escape(name.strip()),
            "$options": "i",
        }

    if phone.strip():
        search_filter["phone"] = {
            "$regex": re.escape(phone.strip()),
        }

    if email.strip():
        search_filter["email"] = {
            "$regex": re.escape(email.strip()),
            "$options": "i",
        }

    students = [
        serialize_student(student)
        for student in students_collection.find(search_filter)
    ]

    messages = {
        "added": {
            "text": "کاربر جدید اضافه شد.",
            "type": "success",
        },
        "deleted": {
            "text": "کاربر با موفقیت حذف شد.",
            "type": "error",
        },
        "updated": {
            "text": "اطلاعات کاربر با موفقیت اصلاح شد.",
            "type": "warning",
        },
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "students": students,
            "notification": messages.get(message),
            "search_name": name,
            "search_phone": phone,
            "search_email": email,
            "search_performed": any(
                value.strip() for value in (name, phone, email)
            ),
        },
    )


# نمایش فرم افزودن کاربر
@app.get("/add", response_class=HTMLResponse)
def show_add_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={
            "student": None,
            "page_title": "افزودن کاربر جدید",
            "form_action": "/add",
            "submit_text": "ثبت کاربر",
        },
    )


# نمایش فرم ویرایش کاربر
@app.get("/add/{student_id}", response_class=HTMLResponse)
def show_edit_form(request: Request, student_id: str):
    mongo_id = parse_student_id(student_id)
    student = students_collection.find_one({"_id": mongo_id})

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="student not found",
        )

    student = serialize_student(student)

    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={
            "student": student,
            "page_title": "ویرایش اطلاعات کاربر",
            "form_action": f"/add?student_id={student_id}",
            "submit_text": "ذخیره تغییرات",
        },
    )


# افزودن یا ویرایش کاربر با یک تابع مشترک
@app.post("/add")
def save_student_from_page(
    request: Request,
    student_id: str | None = None,
    name: str = Form(""),
    age: str = Form(""),
    birth_date: str = Form(""),
    father_name: str = Form(""),
    birth_place: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
):
    existing_student = None
    mongo_id = None

    # بررسی اینکه عملیات افزودن است یا ویرایش
    if student_id:
        mongo_id = parse_student_id(student_id)
        existing_student = students_collection.find_one(
            {"_id": mongo_id}
        )

        if existing_student is None:
            raise HTTPException(
                status_code=404,
                detail="کاربر پیدا نشد.",
            )

    form_data = {
        "name": name,
        "age": age,
        "birth_date": birth_date,
        "father_name": father_name,
        "birth_place": birth_place,
        "phone": phone,
        "email": email,
        "address": address,
    }

    is_editing = existing_student is not None

    page_title = (
        "ویرایش اطلاعات کاربر"
        if is_editing
        else "افزودن کاربر جدید"
    )

    form_action = (
        f"/add?student_id={student_id}"
        if is_editing
        else "/add"
    )

    submit_text = (
        "ذخیره تغییرات"
        if is_editing
        else "ثبت کاربر"
    )

    # اعتبارسنجی اطلاعات برای هر دو عملیات
    try:
        student = Student(
            name=name,
            age=age,
            birth_date=birth_date,
            father_name=father_name,
            birth_place=birth_place,
            phone=phone,
            email=email,
            address=address.strip() or None,
        )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="add.html",
            context={
                "student": (
                    serialize_student(existing_student)
                    if existing_student
                    else None
                ),
                "page_title": page_title,
                "form_action": form_action,
                "submit_text": submit_text,
                "errors": get_persian_errors(exc),
                "form_data": form_data,
            },
            status_code=422,
        )

    student_data = student.model_dump(mode="json")

    # ذخیره اطلاعات جدید یا اصلاح اطلاعات موجود
    if is_editing:
        students_collection.update_one(
            {"_id": mongo_id},
            {"$set": student_data},
        )
        message = "updated"
    else:
        students_collection.insert_one(student_data)
        message = "added"

    return RedirectResponse(
        url=f"/?message={message}",
        status_code=303,
    )


# حذف کاربر از صفحه
@app.post("/students/{student_id}/delete")
def delete_student_from_page(student_id: str):
    mongo_id = parse_student_id(student_id)

    result = students_collection.delete_one(
        {"_id": mongo_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found",
        )

    return RedirectResponse(
        url="/?message=deleted",
        status_code=303,
    )


# API: فهرست، جست‌وجو، مرتب‌سازی و صفحه‌بندی
@app.get("/students")
def get_students(
    name: str | None = None,
    age: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str | None = Query(
        default=None,
        pattern="^(name|name_desc|age|age_desc)$",
    ),
):
    # دریافت مستقیم کاربران از MongoDB
    result = [
        serialize_student(student)
        for student in students_collection.find({})
    ]

    if name is not None:
        result = [
            student
            for student in result
            if name.lower() in student["name"].lower()
        ]

    if age is not None:
        result = [
            student
            for student in result
            if student["age"] == age
        ]

    if sort == "name":
        result = sorted(
            result,
            key=lambda student: student["name"].lower(),
        )
    elif sort == "name_desc":
        result = sorted(
            result,
            key=lambda student: student["name"].lower(),
            reverse=True,
        )
    elif sort == "age":
        result = sorted(
            result,
            key=lambda student: student["age"],
        )
    elif sort == "age_desc":
        result = sorted(
            result,
            key=lambda student: student["age"],
            reverse=True,
        )

    total = len(result)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "students": result[skip:skip + limit],
    }


# API: دریافت کاربر با شناسه MongoDB
@app.get("/students/{student_id}")
def get_student(student_id: str):
    mongo_id = parse_student_id(student_id)

    student = students_collection.find_one(
        {"_id": mongo_id}
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="student not found",
        )

    return serialize_student(student)


# API: افزودن کاربر
@app.post("/students")
def create_student(student: Student):
    student_data = student.model_dump(mode="json")
    result = students_collection.insert_one(student_data)

    return {
        "_id": str(result.inserted_id),
        **student_data,
    }


# API: ویرایش کاربر
@app.put("/students/{student_id}")
def update_student(student_id: str, student: Student):
    mongo_id = parse_student_id(student_id)

    result = students_collection.update_one(
        {"_id": mongo_id},
        {"$set": student.model_dump(mode="json")},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found",
        )

    updated_student = students_collection.find_one(
        {"_id": mongo_id}
    )

    return serialize_student(updated_student)


# API: حذف کاربر
@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    mongo_id = parse_student_id(student_id)

    result = students_collection.delete_one(
        {"_id": mongo_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found",
        )

    return {
        "message": "student deleted",
        "_id": student_id,
    }
