
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr, ValidationError
from bson import ObjectId
from bson.errors import InvalidId
from database import students_collection
from datetime import date

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


# تبدیل شناسهٔ دریافتی به ObjectId
def parse_student_id(student_id: str) -> ObjectId:
    try:
        return ObjectId(student_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid student ID"
        )


# تبدیل سند MongoDB به دادهٔ قابل نمایش یا ارسال در JSON
def serialize_student(student: dict) -> dict:
    student["_id"] = str(student["_id"])
    return student


def get_students_from_db():
    students = list(students_collection.find({}))

    for student in students:
        serialize_student(student)

    return students


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
        max_length=200
    )



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
            "یکی از اطلاعات واردشده معتبر نیست."
        )

        if message not in errors:
            errors.append(message)

    return errors



# --------------------------------------------------
# صفحهٔ اصلی
# --------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request, message: str | None = None):
    students = get_students_from_db()

    messages = {
        "added": {
            "text": "کاربر جدید اضافه شد.",
            "type": "success"
        },
        "deleted": {
            "text": "کاربر با موفقیت حذف شد.",
            "type": "error"
        },
        "updated": {
            "text": "اطلاعات کاربر با موفقیت اصلاح شد.",
            "type": "warning"
        }
    }

    notification = messages.get(message)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "students": students,
            "notification": notification
        }
    )


# --------------------------------------------------
# نمایش فرم افزودن کاربر
# --------------------------------------------------

@app.get("/add", response_class=HTMLResponse)
def show_add_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={
            "student": None,
            "page_title": "افزودن کاربر جدید",
            "form_action": "/add",
            "submit_text": "ثبت کاربر"
        }
    )


# --------------------------------------------------
# نمایش فرم ویرایش کاربر با شناسهٔ MongoDB
# --------------------------------------------------

@app.get("/add/{student_id}", response_class=HTMLResponse)
def show_edit_form(request: Request, student_id: str):
    mongo_id = parse_student_id(student_id)

    student = students_collection.find_one(
        {"_id": mongo_id}
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )

    serialize_student(student)

    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={
            "student": student,
            "page_title": "ویرایش اطلاعات کاربر",
            "form_action": f"/add/{student_id}",
            "submit_text": "ذخیره تغییرات"
        }
    )


# --------------------------------------------------
# افزودن کاربر جدید
# --------------------------------------------------

@app.post("/add")
def add_student_from_page(
    request: Request,
    name: str = Form(""),
    age: str = Form(""),
    birth_date: str = Form(""),
    father_name: str = Form(""),
    birth_place: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form("")
):
    form_data = {
        "name": name,
        "age": age,
        "birth_date": birth_date,
        "father_name": father_name,
        "birth_place": birth_place,
        "phone": phone,
        "email": email,
        "address": address
    }

    try:
        student = Student(
            name=name,
            age=age,
            birth_date=birth_date,
            father_name=father_name,
            birth_place=birth_place,
            phone=phone,
            email=email,
            address=address.strip() or None
        )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="add.html",
            context={
                "student": None,
                "page_title": "افزودن کاربر جدید",
                "form_action": "/add",
                "submit_text": "ثبت کاربر",
                "errors": get_persian_errors(exc),
                "form_data": form_data
            },
            status_code=422
        )

    students_collection.insert_one(
        student.model_dump(mode="json")
    )

    return RedirectResponse(
        url="/?message=added",
        status_code=303
    )


# --------------------------------------------------
# ذخیرهٔ تغییرات کاربر
# --------------------------------------------------

@app.post("/add/{student_id}")
def edit_student_from_page(
    request: Request,
    student_id: str,
    name: str = Form(""),
    age: str = Form(""),
    birth_date: str = Form(""),
    father_name: str = Form(""),
    birth_place: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form("")
):
    mongo_id = parse_student_id(student_id)

    existing_student = students_collection.find_one(
        {"_id": mongo_id}
    )

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="کاربر پیدا نشد."
        )

    form_data = {
        "name": name,
        "age": age,
        "birth_date": birth_date,
        "father_name": father_name,
        "birth_place": birth_place,
        "phone": phone,
        "email": email,
        "address": address
    }

    try:
        student = Student(
            name=name,
            age=age,
            birth_date=birth_date,
            father_name=father_name,
            birth_place=birth_place,
            phone=phone,
            email=email,
            address=address.strip() or None
        )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="add.html",
            context={
                "student": serialize_student(existing_student),
                "page_title": "ویرایش کاربر",
                "form_action": f"/add/{student_id}",
                "submit_text": "ذخیره تغییرات",
                "errors": get_persian_errors(exc),
                "form_data": form_data
            },
            status_code=422
        )

    students_collection.update_one(
        {"_id": mongo_id},
        {"$set": student.model_dump(mode="json")}
    )

    return RedirectResponse(
        url="/?message=updated",
        status_code=303
    )


# --------------------------------------------------
# حذف کاربر از صفحه
# --------------------------------------------------

@app.post("/students/{student_id}/delete")
def delete_student_from_page(student_id: str):
    mongo_id = parse_student_id(student_id)

    result = students_collection.delete_one(
        {"_id": mongo_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )

    return RedirectResponse(
        url="/?message=deleted",
        status_code=303
    )


# --------------------------------------------------
# API: فهرست، جست‌وجو، مرتب‌سازی و صفحه‌بندی
# --------------------------------------------------

@app.get("/students")
def get_students(
    name: str | None = None,
    age: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str | None = Query(
        default=None,
        pattern="^(name|name_desc|age|age_desc)$"
    )
):
    result = get_students_from_db()

    if name is not None:
        result = [
            student for student in result
            if name.lower() in student["name"].lower()
        ]

    if age is not None:
        result = [
            student for student in result
            if student["age"] == age
        ]

    if sort == "name":
        result = sorted(
            result,
            key=lambda student: student["name"].lower()
        )

    elif sort == "name_desc":
        result = sorted(
            result,
            key=lambda student: student["name"].lower(),
            reverse=True
        )

    elif sort == "age":
        result = sorted(
            result,
            key=lambda student: student["age"]
        )

    elif sort == "age_desc":
        result = sorted(
            result,
            key=lambda student: student["age"],
            reverse=True
        )

    total = len(result)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "students": result[skip:skip + limit]
    }


# --------------------------------------------------
# API: دریافت کاربر با شناسهٔ MongoDB
# --------------------------------------------------

@app.get("/students/{student_id}")
def get_student(student_id: str):
    mongo_id = parse_student_id(student_id)

    student = students_collection.find_one(
        {"_id": mongo_id}
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )

    return serialize_student(student)


# --------------------------------------------------
# API: افزودن کاربر
# --------------------------------------------------

@app.post("/students")
def create_student(student: Student):
    student_data = student.model_dump(mode="json")

    result = students_collection.insert_one(student_data)

    return {
        "_id": str(result.inserted_id),
        **student_data
    }


# --------------------------------------------------
# API: ویرایش کاربر
# --------------------------------------------------

@app.put("/students/{student_id}")
def update_student(student_id: str, student: Student):
    mongo_id = parse_student_id(student_id)

    result = students_collection.update_one(
        {"_id": mongo_id},
        {"$set": student.model_dump(mode="json")}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )

    updated_student = students_collection.find_one(
        {"_id": mongo_id}
    )

    return serialize_student(updated_student)


# --------------------------------------------------
# API: حذف کاربر
# --------------------------------------------------

@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    mongo_id = parse_student_id(student_id)

    result = students_collection.delete_one(
        {"_id": mongo_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="student not found"
        )

    return {
        "message": "student deleted",
        "_id": student_id
    }
