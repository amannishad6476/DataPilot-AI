import re
from typing import List, Dict, Any, Tuple, Optional
from app.services.processing.normalizer import DataNormalizer


class SimilarityDeduplicator:
    """
    Deduplicates similar records using:
    1. Root domain matching (e.g., 'tcs.com' vs 'www.tcs.com/careers')
    2. Phone number exact digit matching
    3. Fuzzy token similarity & Levenshtein-based similarity on entity names
    """

    GENERIC_DOMAINS = {
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "linkedin.com",
        "facebook.com", "twitter.com", "instagram.com", "github.com"
    }

    @staticmethod
    def _clean_tokens(text: str) -> set:
        """Strip punctuation, common corporate suffixes, and split into tokens."""
        text = text.lower()
        # Remove common corporate suffixes that distort name matching
        for suffix in ["private limited", "pvt ltd", "ltd", "inc", "corp", "corporation", "llc", "technologies", "tech"]:
            text = re.sub(rf'\b{suffix}\b', '', text)
        tokens = re.findall(r'\b[a-z0-9]{2,}\b', text)
        return set(tokens)

    @classmethod
    def jaro_winkler_similarity(cls, s1: str, s2: str) -> float:
        """Calculates Jaro-Winkler distance between two strings."""
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        match_distance = max(len1, len2) // 2 - 1
        matches = 0
        s1_matches = [False] * len1
        s2_matches = [False] * len2

        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)
            for j in range(start, end):
                if not s2_matches[j] and s1[i] == s2[j]:
                    s1_matches[i] = True
                    s2_matches[j] = True
                    matches += 1
                    break

        if matches == 0:
            return 0.0

        transpositions = 0
        k = 0
        for i in range(len1):
            if s1_matches[i]:
                while not s2_matches[k]:
                    k += 1
                if s1[i] != s2[k]:
                    transpositions += 1
                k += 1

        transpositions //= 2
        jaro = (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0

        # Winkler prefix bonus (up to 4 chars)
        prefix = 0
        for i in range(min(len1, len2, 4)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break

        return jaro + prefix * 0.1 * (1.0 - jaro)

    @classmethod
    def token_jaccard_similarity(cls, s1: str, s2: str) -> float:
        t1 = cls._clean_tokens(s1)
        t2 = cls._clean_tokens(s2)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        return len(intersection) / len(union)

    def are_records_similar(
        self,
        r1: Dict[str, Any],
        r2: Dict[str, Any],
        key_fields: List[str]
    ) -> Tuple[bool, str]:
        """
        Determines if two records represent the same real-world entity.
        Returns (is_duplicate, reason).
        """
        # 1. Compare web domains
        for web_key in ["website", "url", "apply_link"]:
            u1 = r1.get(web_key, "")
            u2 = r2.get(web_key, "")
            if u1 and u2:
                d1 = DataNormalizer.extract_root_domain(u1)
                d2 = DataNormalizer.extract_root_domain(u2)
                if d1 and d2 and d1 not in self.GENERIC_DOMAINS and d1 == d2:
                    return True, f"Identical canonical root domain: {d1}"

        # 2. Compare phone numbers
        for phone_key in ["phone", "mobile", "contact_number"]:
            p1 = re.sub(r'[^\d]', '', str(r1.get(phone_key, "")))
            p2 = re.sub(r'[^\d]', '', str(r2.get(phone_key, "")))
            if len(p1) >= 10 and p1 == p2:
                return True, f"Identical contact phone number: {p1}"

        # 3. Compare email addresses
        for email_key in ["business_email", "public_business_email", "contact_email", "email"]:
            e1 = str(r1.get(email_key, "")).strip().lower()
            e2 = str(r2.get(email_key, "")).strip().lower()
            if e1 and e2 and e1 == e2 and "@" in e1:
                return True, f"Identical public contact email: {e1}"

        # 4. Compare entity / company names with fuzzy & token matching
        for name_key in ["company_name", "entity_name", "job_title", "title"]:
            n1 = str(r1.get(name_key, "")).strip()
            n2 = str(r2.get(name_key, "")).strip()
            if n1 and n2:
                # Direct string equality (case-insensitive)
                if n1.lower() == n2.lower():
                    return True, f"Exact name match on {name_key}: '{n1}'"

                # Token set overlap
                jaccard = self.token_jaccard_similarity(n1, n2)
                if jaccard >= 0.75:
                    return True, f"High token overlap ({jaccard:.2f}) on {name_key}: '{n1}' vs '{n2}'"

                # Jaro-Winkler similarity
                jw = self.jaro_winkler_similarity(n1.lower(), n2.lower())
                if jw >= 0.90:
                    return True, f"High phonetic/string similarity ({jw:.2f}) on {name_key}: '{n1}' vs '{n2}'"

        return False, ""

    def deduplicate_records(
        self,
        records: List[Dict[str, Any]],
        key_fields: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], int, str]]]:
        """
        Deduplicates a list of records.
        Returns:
            - unique_records: List of consolidated unique records
            - duplicate_records_info: List of (duplicate_record, merged_into_index, reason)
        """
        unique_records: List[Dict[str, Any]] = []
        duplicates_info: List[Tuple[Dict[str, Any], int, str]] = []

        for candidate in records:
            matched_index = None
            match_reason = ""

            for idx, existing in enumerate(unique_records):
                is_dup, reason = self.are_records_similar(candidate, existing, key_fields)
                if is_dup:
                    matched_index = idx
                    match_reason = reason
                    break

            if matched_index is not None:
                # Merge: enrich the existing record with any missing fields from candidate
                existing = unique_records[matched_index]
                for k, v in candidate.items():
                    if v and not existing.get(k):
                        existing[k] = v
                duplicates_info.append((candidate, matched_index, match_reason))
            else:
                unique_records.append(dict(candidate))

        return unique_records, duplicates_info
