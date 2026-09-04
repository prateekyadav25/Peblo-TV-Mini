from pydantic import BaseModel
from typing import List, Optional

class ValidationErrorItem(BaseModel):
    entity_type: str
    entity_id: str
    field: str
    problem: str
    why_it_matters: str
    remediation: str

class ValidationReport(BaseModel):
    can_publish: bool
    errors: List[ValidationErrorItem]
    warnings: List[ValidationErrorItem]
    summary: dict
