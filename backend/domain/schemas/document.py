from pydantic import BaseModel, Field


class IndexResponse(BaseModel):
    filename: str = Field(..., description="Nom du fichier indexé")
    chunks_indexed: int = Field(..., description="Nombre de chunks ajoutés au vector store")
    message: str = "Document indexé avec succès"
