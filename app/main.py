from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routes import router
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# Include router
app.include_router(router)

print("Registered routes:")
for route in app.routes:
    print(route.path)
