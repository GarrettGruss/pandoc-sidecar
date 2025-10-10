from fastapi import FastAPI, File, UploadFile, BackgroundTasks
import uvicorn

from pandoc_sidecar.service import PandocService
from pandoc_sidecar.models import LatexRequest

app = FastAPI()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pandoc-sidecar"}


@app.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)
):
    """Upload multiple files and convert to PDF using Pandoc"""
    service = PandocService()
    return await service.upload_files(background_tasks, files)


@app.post("/latex")
async def convert_latex(background_tasks: BackgroundTasks, request: LatexRequest):
    """Convert LaTeX string to PDF"""
    service = PandocService()

    # Save the LaTeX content to a .tex file
    tex_file_path = service.save_latex_string(request.latex_content, request.filename)

    # Convert to PDF
    return await service.convert_to_pdf(background_tasks, tex_file_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
