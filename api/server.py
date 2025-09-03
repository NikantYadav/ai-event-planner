from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mongo import app, get_db
from fastapi import Depends
from pymongo.database import Database
from routes import auth_router
from event_routes import event_router

app = FastAPI(title="ai-event-planner API")

# Enable CORS for all origins (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Include event planning routes
app.include_router(event_router)


class HealthResponse(BaseModel):
    status: str

@app.get("/db-check")
def db_check(db: Database = Depends(get_db)):
    """Check if MongoDB connection is alive."""
    try:
        db.command("ping")
        return {"status": "ok", "message": "MongoDB connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Run with: uvicorn server:app --reload
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
