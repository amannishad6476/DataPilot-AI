import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Dict, Any, Tuple, List


class DataNormalizer:
    @staticmethod
    def clean_text(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).strip()
        # Collapse multiple spaces into single space
        return re.sub(r'\s+', ' ', s)

    @staticmethod
    def normalize_url(url: str) -> str:
        if not url:
            return ""
        u = url.strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            u = "https://" + u

        try:
            parsed = urlparse(u)
            # Normalize scheme to https if http
            scheme = "https" if parsed.scheme in ["http", "https"] else parsed.scheme
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Filter out marketing tracking parameters (utm_*, ref, fbclid, etc.)
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items()
                if not k.startswith("utm_") and k not in ["ref", "fbclid", "gclid", "source"]
            }
            new_query = urlencode(filtered_params, doseq=True)
            path = parsed.path.rstrip('/')
            if not path and not new_query:
                path = ""

            return urlunparse((scheme, netloc, path, parsed.params, new_query, ""))
        except Exception:
            return u

    @staticmethod
    def extract_root_domain(url: str) -> str:
        if not url:
            return ""
        try:
            u = url.strip()
            if not (u.startswith("http://") or u.startswith("https://")):
                u = "https://" + u
            parsed = urlparse(u)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc.split(":")[0]
        except Exception:
            return ""

    @staticmethod
    def normalize_email(email: str) -> str:
        if not email:
            return ""
        e = email.strip().lower()
        if e.startswith("mailto:"):
            e = e[7:]
        return e.strip()

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        p = phone.strip()
        # Clean unwanted punctuation but preserve leading +
        has_plus = p.startswith("+")
        digits = re.sub(r'[^\d]', '', p)
        if not digits:
            return ""
        if has_plus:
            return f"+{digits}"
        # Standard Indian / 10-digit number handling
        if len(digits) == 10:
            return f"+91 {digits[:5]} {digits[5:]}"
        elif len(digits) == 11 and digits.startswith("0"):
            return f"+91 {digits[1:6]} {digits[6:]}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits[:2]} {digits[2:7]} {digits[7:]}"
        return digits

    def normalize_record_with_audit(self, record_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
        """
        Normalizes a record and returns:
            - normalized record dict
            - field_transformations: Dict[field_name, List[transformation_tags]]
        """
        normalized = {}
        transformations: Dict[str, List[str]] = {}

        for key, val in record_data.items():
            if key.startswith("_"):
                normalized[key] = val
                continue

            if val is None:
                normalized[key] = ""
                transformations[key] = ["coerced_empty_string"]
                continue

            raw_str = str(val)
            k_lower = key.lower()
            field_transforms: List[str] = []

            if "url" in k_lower or "website" in k_lower or "link" in k_lower:
                clean_url = self.normalize_url(raw_str)
                normalized[key] = clean_url
                if raw_str != clean_url:
                    if not raw_str.startswith("http"):
                        field_transforms.append("added_https_scheme")
                    if "utm_" in raw_str:
                        field_transforms.append("stripped_tracking_parameters")
                    if "www." in raw_str and "www." not in clean_url:
                        field_transforms.append("canonicalized_hostname")
                    if not field_transforms:
                        field_transforms.append("standardized_url")
                else:
                    field_transforms.append("valid_syntax_preserved")

            elif "email" in k_lower:
                clean_email = self.normalize_email(raw_str)
                normalized[key] = clean_email
                if raw_str != clean_email:
                    if raw_str.lower().startswith("mailto:"):
                        field_transforms.append("stripped_mailto_prefix")
                    if raw_str != raw_str.lower():
                        field_transforms.append("lowercased")
                    if raw_str.strip() != raw_str:
                        field_transforms.append("trimmed_whitespace")
                    if not field_transforms:
                        field_transforms.append("sanitized_email")
                else:
                    field_transforms.append("rfc_compliant")

            elif "phone" in k_lower or "mobile" in k_lower or "tel" in k_lower:
                clean_phone = self.normalize_phone(raw_str)
                normalized[key] = clean_phone
                if raw_str != clean_phone:
                    field_transforms.append("stripped_punctuation")
                    if clean_phone.startswith("+"):
                        field_transforms.append("e164_standardized")
                else:
                    field_transforms.append("valid_phone_format")

            else:
                clean_s = self.clean_text(val)
                normalized[key] = clean_s
                if raw_str != clean_s:
                    field_transforms.append("collapsed_whitespace")
                else:
                    field_transforms.append("exact_match")

            transformations[key] = field_transforms

        return normalized, transformations

    def normalize_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized, _ = self.normalize_record_with_audit(record_data)
        return normalized
