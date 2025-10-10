from pydantic import BaseModel, Field


class LatexRequest(BaseModel):
    """Request model for LaTeX string input"""
    latex_content: str = Field(..., description="LaTeX content to convert to PDF")
    filename: str = Field(default="document", description="Base filename for the generated file")
