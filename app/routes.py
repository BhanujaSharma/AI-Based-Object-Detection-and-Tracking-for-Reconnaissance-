from fastapi import APIRouter, Request, Form, Path
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from bson import ObjectId
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.auth import authenticate_user, hash_password
from app.detection_stream import generate_frames
from app.database import (
    collection as detection_logs_col,
    users_col,
    fs,
)

router = APIRouter()

# Jinja2 Environment with template caching disabled
jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)

templates = Jinja2Templates(directory="app/templates")
templates.env = jinja_env


# -----------------------------
# Landing Page
# -----------------------------
@router.get("/")
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


# -----------------------------
# Live Feed UI (Dynamic camera)
# -----------------------------
@router.get("/live/{cam_id}")
def live_page(request: Request, cam_id: str = Path(...)):
    return templates.TemplateResponse("live.html", {"request": request, "cam_id": cam_id})


@router.get("/live")
def redirect_to_default_camera():
    return RedirectResponse(url="/live/phone")


# -----------------------------
# Live MJPEG Streaming Endpoint
# -----------------------------
@router.get("/video_feed/{cam_id}")
def video_feed(cam_id: str = Path(...)):
    return StreamingResponse(generate_frames(cam_id), media_type="multipart/x-mixed-replace; boundary=frame")


# -----------------------------
# Login Page (GET)
# -----------------------------
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -----------------------------
# Login Form Submission (POST)
# -----------------------------
@router.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if user:
        request.session["user"] = {
            "username": user["username"],
            "zone": user.get("zone", "none"),
            "role": user.get("role", "viewer")
        }
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid credentials"
    })


# -----------------------------
# Dashboard (GET)
# -----------------------------
@router.get("/dashboard")
def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    zone = user["zone"]
    role = user.get("role", "viewer")

    # 🔐 Restrict logs if not admin
    if role == "admin":
        logs = list(detection_logs_col.find().sort("timestamp", -1))
    else:
        logs = list(detection_logs_col.find({"zone": zone}).sort("timestamp", -1))

    for log in logs:
        log["image_id"] = str(log["image_id"])
        if isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M")


    context = {
        "request": request,
        "username": user["username"],
        "zone": zone,
        "logs": logs,
        "is_admin": role == "admin"
    }

    if role == "admin":
        context["users"] = list(users_col.find({}, {"_id": 0, "password": 0}))

    return templates.TemplateResponse("dashboard.html", context)


# -----------------------------
# Dashboard (POST) - Create New User
# -----------------------------
@router.post("/dashboard")
def register_user(
    request: Request,
    new_username: str = Form(...),
    new_password: str = Form(...),
    new_role: str = Form(...),
    new_zone: str = Form(...)
):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    existing = users_col.find_one({"username": new_username})
    if existing:
        # Re-fetch dashboard context
        logs = list(detection_logs_col.find().sort("timestamp", -1))
        for log in logs:
            log["image_id"] = str(log["image_id"])
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M")

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "username": user["username"],
            "zone": user["zone"],
            "logs": logs,
            "users": list(users_col.find({}, {"_id": 0, "password": 0})),
            "is_admin": True,
            "error": f"User '{new_username}' already exists."
        })

    users_col.insert_one({
        "username": new_username,
        "password": hash_password(new_password),
        "role": new_role,
        "zone": new_zone
    })

    return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)


# -----------------------------
# Serve Image from GridFS
# -----------------------------
@router.get("/image/{image_id}")
def get_image(image_id: str):
    try:
        grid_out = fs.get(ObjectId(image_id))
        return Response(content=grid_out.read(), media_type="image/jpeg")
    except Exception as e:
        return Response(content=f"Image not found: {e}", media_type="text/plain")


# -----------------------------
# Delete User (Admin Only)
# -----------------------------
@router.post("/delete_user")
def delete_user(request: Request, username: str = Form(...)):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    if username == user["username"]:
        # Prevent self-deletion
        return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)

    users_col.delete_one({"username": username})
    return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)


# -----------------------------
# Edit User (Admin Only)
# -----------------------------
@router.post("/edit_user")
def edit_user(
    request: Request,
    old_username: str = Form(...),
    updated_role: str = Form(...),
    updated_zone: str = Form(...)
):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    # Prevent editing own account role/zone for now
    if old_username == user["username"]:
        return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)

    users_col.update_one(
        {"username": old_username},
        {"$set": {"role": updated_role, "zone": updated_zone}}
    )

    return RedirectResponse("/dashboard", status_code=HTTP_302_FOUND)


# -----------------------------
# Logout
# -----------------------------
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)
