import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Pandoc Sidecar Service",
    description="A FastAPI sidecar service for pandoc document conversion",
    version="0.1.0"
)

class ConversionRequest(BaseModel):
    content: str
    from_format: str
    to_format: str
    extra_args: Optional[List[str]] = None

class ConversionResponse(BaseModel):
    converted_content: str
    input_format: str
    output_format: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pandoc-sidecar"}

@app.post("/convert", response_model=ConversionResponse)
async def convert_document(request: ConversionRequest):
    """Convert document content from one format to another using pandoc"""
    try:
        extra_args = request.extra_args or []

        cmd = [
            "pandoc",
            "--from", request.from_format,
            "--to", request.to_format
        ] + extra_args

        process = subprocess.run(
            cmd,
            input=request.content,
            text=True,
            capture_output=True,
            check=True
        )

        return ConversionResponse(
            converted_content=process.stdout,
            input_format=request.from_format,
            output_format=request.to_format
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Pandoc conversion failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")

@app.post("/convert-file")
async def convert_file(
    file: UploadFile = File(...),
    to_format: str = Form(...),
    from_format: Optional[str] = Form(None),
    extra_args: Optional[str] = Form(None)
):
    """Convert an uploaded file from one format to another"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / file.filename
            output_path = Path(temp_dir) / f"output.{to_format}"

            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)

            extra_args_list = extra_args.split() if extra_args else []

            cmd = ["pandoc", str(input_path), "-o", str(output_path)]
            if from_format:
                cmd.extend(["--from", from_format])
            cmd.extend(["--to", to_format])
            cmd.extend(extra_args_list)

            process = subprocess.run(cmd, capture_output=True, text=True, check=True)

            with open(output_path, "rb") as f:
                output_content = f.read()

            return Response(
                content=output_content,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename=converted.{to_format}"}
            )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Pandoc file conversion failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File conversion failed: {str(e)}")

@app.get("/formats")
async def get_supported_formats():
    """Get list of supported input and output formats"""
    try:
        input_process = subprocess.run(
            ["pandoc", "--list-input-formats"],
            capture_output=True,
            text=True,
            check=True
        )
        output_process = subprocess.run(
            ["pandoc", "--list-output-formats"],
            capture_output=True,
            text=True,
            check=True
        )

        input_formats = input_process.stdout.strip().split('\n')
        output_formats = output_process.stdout.strip().split('\n')

        return {
            "input_formats": input_formats,
            "output_formats": output_formats
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get formats: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get formats: {str(e)}")

@app.get("/version")
async def get_pandoc_version():
    """Get pandoc version information"""
    try:
        process = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_output = process.stdout.strip()
        version_line = version_output.split('\n')[0]
        version = version_line.split()[1] if len(version_line.split()) > 1 else "unknown"

        return {
            "pandoc_version": version,
            "full_version_info": version_output
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to get version: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")

def main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
