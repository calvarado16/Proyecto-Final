import re
from pydantic import BaseModel, Field

class Profession(BaseModel): 
    id: str = Field(
        default=None,
        description="ID de MongoDB"
    )
    
    name: str = Field(
        description="Nombre de la profesión"
    )
    
    active: bool = Field(
        default=True,
        description="Estado de la profesion (activo/desactivo)"
    )
