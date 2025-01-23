from haystack.dataclasses import Document
from app.schemas.medication import MedicationEntity
from app.utils.common import create_index_documents


def test_create_index_documents():
    medications = [
        MedicationEntity(original_text="Drug1"),
        MedicationEntity(original_text="Drug2"),
    ]
    result = create_index_documents(medications)

    assert isinstance(result, list), "The result should be a list."
    assert all(
        isinstance(doc, Document) for doc in result
    ), "All items in the result should be Document objects."
    assert (
        len(result) == 2
    ), "The length of the result does not match the number of medications."
