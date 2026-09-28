from app.services.processing.deduplicator import SimilarityDeduplicator


def test_similarity_deduplication():
    deduplicator = SimilarityDeduplicator()

    records = [
        {
            "company_name": "Tata Consultancy Services Ltd",
            "website": "https://www.tcs.com",
            "public_business_email": "campus@tcs.com",
            "phone": "+91 522 666 4000"
        },
        {
            "company_name": "Tata Consultancy Services (Lucknow)",  # Fuzzy duplicate
            "website": "http://tcs.com/about",  # Domain match
            "public_business_email": "",
            "phone": "05226664000"
        },
        {
            "company_name": "HCL Technologies Ltd",
            "website": "https://www.hcltech.com",
            "public_business_email": "partners@hcltech.com",
            "phone": "+91 522 710 1000"
        }
    ]

    unique_records, dups = deduplicator.deduplicate_records(records, ["company_name", "website"])

    assert len(unique_records) == 2, f"Expected 2 unique records, got {len(unique_records)}"
    assert len(dups) == 1, f"Expected 1 duplicate identified, got {len(dups)}"

    # Check that merged attributes were preserved
    tcs = next(r for r in unique_records if "tcs" in r["website"])
    assert tcs["public_business_email"] == "campus@tcs.com"
