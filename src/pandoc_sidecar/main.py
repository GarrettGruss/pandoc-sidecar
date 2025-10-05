from typing import Annotated
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pandoc-sidecar"}

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload multiple files and save them to the upload directory"""
    saved_files = []

    for file in files:
        if not file.filename:
            continue

        file_path = UPLOAD_DIR / file.filename

        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        saved_files.append({
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        })

    return {
        "message": f"Successfully uploaded {len(saved_files)} file(s)",
        "files": saved_files
    }