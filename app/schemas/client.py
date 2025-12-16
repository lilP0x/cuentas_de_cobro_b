
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional, Literal
from typing import Literal


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, example="EOBO CAFÉ", not_none=True)
    client_type: Literal["COMPANY", "PERSON"] = Field(..., example="COMPANY")
    
class ClientCreate(ClientBase):
    name: str = Field(..., min_length=1, example="EOBO CAFÉ", not_none=True)
    client_type: Literal["COMPANY", "PERSON"] = Field(..., example="COMPANY")
    

class ClientResponse(ClientBase):
    client_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")