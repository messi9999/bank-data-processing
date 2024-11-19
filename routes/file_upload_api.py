from fastapi import File, UploadFile, HTTPException, APIRouter
from pathlib import Path
import shutil
import uuid

api_router = APIRouter()

# Ensure the excels directory exists
EXCELS_DIR = Path("excels")
EXCELS_DIR.mkdir(exist_ok=True)

@api_router.post("/upload-multiple-excel/")
async def upload_multiple_excel(files: list[UploadFile] = File(...)):
    file_names = []
    for file in files:
        # Generate a unique file name
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        try:
            file_location = EXCELS_DIR / unique_filename
            with file_location.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
        finally:
            await file.close()
        
        file_names.append(unique_filename)
    
    return {"file_names": file_names}