from fastapi import FastAPI
from controllers.orchestrator import router as orchestrator_router
from database.db import init_db

app = FastAPI(title="Traffic Control Service")

app.include_router(orchestrator_router)  # ← CRITICAL

@app.get("/")
def root():
    return {"message": "Traffic Control Service is running"}

@app.get("/healthcheck")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
