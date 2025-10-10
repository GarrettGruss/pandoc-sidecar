from fastmcp import FastMCP
from fastapi import BackgroundTasks
from pandoc_sidecar.service import PandocService

mcp = FastMCP("pandoc-sidecar")


@mcp.resource("latex://convert")
async def convert_latex_resource(latex_content: str, filename: str = "output"):
    """Convert LaTeX string to PDF and return as binary data"""
    background_tasks = BackgroundTasks()
    service = PandocService()

    # Save the LaTeX content to a .tex file
    tex_file_path = service.save_latex_string(latex_content, filename)

    # Convert to PDF
    return await service.convert_to_pdf(background_tasks, tex_file_path)


if __name__ == "__main__":
    mcp.run()
