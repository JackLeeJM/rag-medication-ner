MEDICATION_NER = """
    Given the following examples of medication entities:

    {% for document in documents %}
        Query: {{ document.content }}
        Answer: {{ document.meta }}
    {% endfor %}

    Using the examples as context, extrapolate and extract the medication entities from the following text:
    {{ query }}

    Provide the output in the following JSON format:
    {
        "original_text": "<input_text>",
        "quantity": ["<quantity>"],
        "drug_name": ["<drug_name>"],
        "dosage": ["<dosage>"],
        "administration_type": ["<administration_type>"],
        "brand": ["<brand>"]
    }
    For keys without any values, provide an empty list.
    Respond only with valid JSON. Do not write an introduction or summary.
    """
