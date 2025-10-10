from pathlib import Path
import subprocess
import os

from fastapi import File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import uuid


class PandocService:
    """Service for handling Pandoc conversions"""

    def __init__(self):
        # Configure upload directory
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

        # Create a unique job ID for this instance
        self.job_id = str(uuid.uuid4())

    def cleanup_files(self, *file_paths: Path):
        """Remove files after response is sent"""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

    def save_latex_string(self, latex_content: str, filename: str = "document") -> Path:
        """Save a LaTeX string as a .tex file"""
        # Create filename with job ID
        new_filename = f"{filename}_{self.job_id}.tex"
        file_path = self.upload_dir / new_filename

        # Write the LaTeX content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        return file_path

    async def save_uploaded_files(self, files: list[UploadFile]) -> list[dict]:
        """Save uploaded files to the upload directory"""
        saved_files = []

        # Save the files
        for file in files:
            if not file.filename:
                continue

            # Append job ID to filename
            file_stem = Path(file.filename).stem
            file_suffix = Path(file.filename).suffix
            new_filename = f"{file_stem}_{self.job_id}{file_suffix}"
            file_path = self.upload_dir / new_filename

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

        if not saved_files:
            raise HTTPException(status_code=400, detail="No files were uploaded")

        return saved_files

    async def convert_to_pdf(self, background_tasks: BackgroundTasks, input_path: Path):
        """Convert input file to PDF using Pandoc"""
        # Generate output filename (convert to PDF)
        output_filename = f"{input_path.stem}.pdf"
        output_path = self.upload_dir / output_filename

        # Get absolute workspace path
        workspace = os.path.abspath(str(self.upload_dir))

        cmd = ['docker-compose', 'run', '--rm',
               '-v', f'{workspace}:/workspace',
               'pandoc-extra',
               f'/workspace/{input_path.name}',
               '-o', f'/workspace/{output_filename}',
               '--pdf-engine=pdflatex']

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Return the generated PDF file
            if output_path.exists():
                # Schedule cleanup of all files (input and output)
                files_to_cleanup = [input_path, output_path]
                background_tasks.add_task(self.cleanup_files, *files_to_cleanup)

                return FileResponse(
                    path=str(output_path),
                    filename=output_filename,
                    media_type='application/pdf'
                )
            else:
                # Cleanup input file even if output failed
                self.cleanup_files(input_path)
                raise HTTPException(status_code=500, detail="PDF generation failed - output file not found")

        except subprocess.CalledProcessError as e:
            # Cleanup input file on error
            self.cleanup_files(input_path)
            error_details = e.stderr if e.stderr else str(e)
            raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {error_details}")

    async def upload_files(self, background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
        """Upload multiple files and convert the first one to PDF"""
        saved_files = await self.save_uploaded_files(files)

        # Use the first file as input
        input_file = saved_files[0]
        input_path = Path(input_file["path"])

        return await self.convert_to_pdf(background_tasks, input_path)
