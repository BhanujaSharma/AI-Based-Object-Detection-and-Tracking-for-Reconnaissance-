from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from bson import ObjectId
from datetime import datetime

from app.auth import authenticate_user
from app.detection_stream import generate_frames
from app.database import collection as detection_logs_col, fs


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Landing Page
@router.get("/")
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


# Live webcam feed page
@router.get("/live")
def live_page(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})


# Login Page
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Login Form POST
@router.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if user:
        request.session["user"] = {
            "username": user["username"],
            "zone": user.get("zone", "all")
        }
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


# Dashboard Page (requires login)
@router.get("/dashboard")
def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    zone = user["zone"]
    # You can use zone filtering here if your detection_logs_col has a zone field
    logs = list(detection_logs_col.find().sort("timestamp", -1))

    for log in logs:
        log["image_id"] = str(log["image_id"])
        log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["username"],
        "zone": zone,
        "logs": logs
    })


# Live video feed
@router.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


# Serve image from GridFS
@router.get("/image/{image_id}")
def get_image(image_id: str):
    try:
        grid_out = fs.get(ObjectId(image_id))
        return Response(content=grid_out.read(), media_type="image/jpeg")
    except Exception as e:
        return Response(content=f"Image not found: {e}", media_type="text/plain")

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)
