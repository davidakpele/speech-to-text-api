import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import audio
from app.config import settings
from app.database import Base, engine  
from app.models.users import User      

# Initialize FastAPI app
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# Mount the static directory for CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the audio routes
app.include_router(audio.router, prefix="", tags=["audio"])

# Create tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)   

# Main entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
