from typing import List
from pydantic import BaseModel, Field


class MedicationEntity(BaseModel):
    original_text: str = Field(..., description="Original medication text")
    quantity: List[str] = Field(
        default_factory=list, description="List of quantities found"
    )
    drug_name: List[str] = Field(
        default_factory=list, description="List of drug names found"
    )
    dosage: List[str] = Field(default_factory=list, description="List of dosages found")
    administration_type: List[str] = Field(
        default_factory=list, description="List of administration types found"
    )
    brand: List[str] = Field(default_factory=list, description="List of brands found")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_text": "Acetaminophen 325 MG Oral Tablet",
                    "quantity": [],
                    "drug_name": ["Acetaminophen"],
                    "dosage": ["325 MG"],
                    "administration_type": ["Oral Tablet"],
                    "brand": [],
                }
            ]
        }
    }


class MedicationRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of medication texts to process",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"texts": ["Acetaminophen 325 MG Oral Tablet"]}]
        }
    }


class MedicationResponse(BaseModel):
    results: List[MedicationEntity] = Field(
        ..., description="List of extracted medication entities"
    )
    processing_time: float = Field(..., description="Total processing time in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "results": [
                        {
                            "original_text": "Acetaminophen 325 MG Oral Tablet",
                            "quantity": [],
                            "drug_name": ["Acetaminophen"],
                            "dosage": ["325 MG"],
                            "administration_type": ["Oral Tablet"],
                            "brand": [],
                        }
                    ],
                    "processing_time": 0.15,
                }
            ]
        }
    }


class MedicationIndexRequest(BaseModel):
    medications: List[MedicationEntity] = Field(
        ..., min_length=1, description="List of medications to index"
    )


class MedicationIndexResponse(BaseModel):
    message: str = Field(
        ..., description="Message indicating the success or failure of the operation"
    )
    processing_time: float = Field(..., description="Total processing time in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Successfully indexed 1 entity",
                    "processing_time": 0.05,
                }
            ]
        }
    }
