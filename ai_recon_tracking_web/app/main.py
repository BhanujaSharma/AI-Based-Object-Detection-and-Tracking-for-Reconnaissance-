from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles  # ✅ Add this
from app.routes import router

app = FastAPI()

# Add session middleware for login sessions
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# ✅ Mount static files (so /static/styles.css can be served)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include the API router
app.include_router(router)
