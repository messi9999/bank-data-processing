from fastapi import FastAPI, HTTPException
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

import uvicorn
from routes import file_upload_api, bank_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run when starts the server.
    print("Starting server...")
   
    yield
    # Run when shutdown the server.
    print("Shutdown server..")


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

app.include_router(file_upload_api.api_router)
app.include_router(bank_api.api_router)



@app.get("/")
async def root():
    try:
        return {"message": "Welcome to the Backend API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")