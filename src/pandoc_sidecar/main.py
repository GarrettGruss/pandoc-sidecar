from typing import Annotated
from pathlib import Path
import subprocess
import os

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
import uuid
import uvicorn

app = FastAPI()

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pandoc-sidecar"}

def cleanup_files(*file_paths: Path):
    """Remove files after response is sent"""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

@app.post("/upload")
async def upload_files(background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
    """Upload multiple files and save them to the upload directory"""
    saved_files = []
    id = str(uuid.uuid4())

    # Save the files
    for file in files:
        if not file.filename:
            continue

        # Append UUID to filename
        file_stem = Path(file.filename).stem
        file_suffix = Path(file.filename).suffix
        new_filename = f"{file_stem}_{id}{file_suffix}"
        file_path = UPLOAD_DIR / new_filename

        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        saved_files.append({
            "filename": new_filename,
            "original_filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        })

    # Perform Pandoc Action
    if not saved_files:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    # Use the first file as input
    input_file = saved_files[0]
    input_path = Path(input_file["path"])

    # Generate output filename (convert to PDF)
    output_filename = f"{input_path.stem}.pdf"
    output_path = UPLOAD_DIR / output_filename

    # Get absolute workspace path
    workspace = os.path.abspath(str(UPLOAD_DIR))

    cmd = ['docker-compose', 'run', '--rm',
           '-v', f'{workspace}:/workspace',
           'pandoc-extra',
           f'/workspace/{input_path.name}',
           '-o', f'/workspace/{output_filename}',
           '--pdf-engine=pdflatex']

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Return the generated PDF file
        if output_path.exists():
            # Schedule cleanup of all files (input and output)
            files_to_cleanup = [input_path, output_path]
            background_tasks.add_task(cleanup_files, *files_to_cleanup)

            return FileResponse(
                path=str(output_path),
                filename=output_filename,
                media_type='application/pdf'
            )
        else:
            # Cleanup input file even if output failed
            cleanup_files(input_path)
            raise HTTPException(status_code=500, detail="PDF generation failed - output file not found")

    except subprocess.CalledProcessError as e:
        # Cleanup input file on error
        cleanup_files(input_path)
        error_details = e.stderr if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {error_details}")
    
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)