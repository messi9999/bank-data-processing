from fastapi import FastAPI, HTTPException
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

from config import database

import uvicorn
from routes import file_upload_api, bank_api, invoice_api, reconciliation_api, db_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run when starts the server.
    print("Starting server...")
    print("Connecting database...")
    await database.database.connect()
    database.drop_all_tables()
    database.create_tables()
    yield
    # Run when shutdown the server.
    print("Shutdown server..")
    await database.database.disconnect()


app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(file_upload_api.api_router, prefix="/api")
app.include_router(bank_api.api_router, prefix="/api")
app.include_router(invoice_api.api_router, prefix="/api")
app.include_router(reconciliation_api.api_router, prefix="/api")
app.include_router(db_api.api_router, prefix="/api")



@app.get("/api-test")
async def root():
    try:
        return {"message": "Welcome to the Backend API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    
app.mount("/exports", StaticFiles(directory="exports"), name="result")
app.mount("/", StaticFiles(directory="build", html=True), name="static")
app.mount("/static", StaticFiles(directory="build/static"), name="static-resources")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)