from app.services.processing.deduplicator import SimilarityDeduplicator


def test_deterministic_deduplication():
    dedup = SimilarityDeduplicator()
    records = [
        {"company_name": "Acme Corp", "website": "https://acme.com", "phone": "+1-800-555-0199"},
        {"company_name": "Acme Inc", "website": "http://www.acme.com/about", "phone": "800-555-0199", "email": "info@acme.com"}
    ]
    unique, dups = dedup.deduplicate_records(records, key_fields=["company_name", "website", "phone"])
    assert len(unique) == 1
    assert len(dups) == 1

    canonical = unique[0]
    # Check that missing fields were merged
    assert canonical["email"] == "info@acme.com"
    # Check duplicate group ID
    assert canonical["_duplicate_group_id"] is not None
    # Check merge history
    assert len(canonical["_merge_history"]) == 1
    assert "email" in canonical["_merge_history"][0]["merged_fields"]

    dup_record, matched_idx, reason, match_method, score = dups[0]
    assert matched_idx == 0
    assert match_method in ["deterministic_domain", "deterministic_phone"]
    assert score == 1.0


def test_fuzzy_deduplication():
    dedup = SimilarityDeduplicator()
    records = [
        {"company_name": "DeepMind Technologies Ltd", "location": "London"},
        {"company_name": "Deepmind Tech", "location": "London, UK", "website": "https://deepmind.google"}
    ]
    unique, dups = dedup.deduplicate_records(records, key_fields=["company_name"])
    assert len(unique) == 1
    assert len(dups) == 1

    canonical = unique[0]
    assert canonical["website"] == "https://deepmind.google"
    assert len(canonical["_merge_history"]) == 1
    assert canonical["_merge_history"][0]["match_method"] in ["token_jaccard", "jaro_winkler", "exact_name"]


def test_no_false_positive_deduplication():
    dedup = SimilarityDeduplicator()
    records = [
        {"company_name": "Apple Inc", "website": "https://apple.com"},
        {"company_name": "Google LLC", "website": "https://google.com"},
        {"company_name": "Microsoft Corp", "website": "https://microsoft.com"}
    ]
    unique, dups = dedup.deduplicate_records(records, key_fields=["company_name", "website"])
    assert len(unique) == 3
    assert len(dups) == 0
