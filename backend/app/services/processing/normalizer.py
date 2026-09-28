import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Dict, Any


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

    def normalize_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for key, val in record_data.items():
            if val is None:
                normalized[key] = ""
                continue

            k_lower = key.lower()
            if "url" in k_lower or "website" in k_lower or "link" in k_lower:
                normalized[key] = self.normalize_url(str(val))
            elif "email" in k_lower:
                normalized[key] = self.normalize_email(str(val))
            elif "phone" in k_lower or "mobile" in k_lower or "tel" in k_lower:
                normalized[key] = self.normalize_phone(str(val))
            else:
                normalized[key] = self.clean_text(val)
        return normalized
