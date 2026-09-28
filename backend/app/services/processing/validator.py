import re
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
from app.schemas.planner import ValidationRuleSpec


class DataValidator:
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    @classmethod
    def validate_email(cls, email: str) -> bool:
        if not email:
            return False
        return bool(cls.EMAIL_REGEX.match(email.strip()))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        if not phone:
            return False
        digits = re.sub(r'[^\d]', '', phone)
        # Valid international/national phone number typically between 7 and 15 digits
        return 7 <= len(digits) <= 15

    @classmethod
    def validate_url(cls, url: str) -> bool:
        if not url:
            return False
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ["http", "https"] and parsed.netloc and "." in parsed.netloc)
        except Exception:
            return False

    def validate_record(
        self,
        record: Dict[str, Any],
        rules: List[ValidationRuleSpec]
    ) -> Tuple[bool, List[str], float]:
        """
        Validates a single record against the specified rules.
        Returns:
            - is_valid: True if no 'error' severity violations occurred
            - errors: List of validation issue descriptions
            - confidence_score: Float between 0.0 and 1.0 based on quality checks
        """
        errors: List[str] = []
        is_strictly_valid = True
        total_checks = 0
        passed_checks = 0

        for rule in rules:
            field_val = record.get(rule.field)
            val_str = str(field_val).strip() if field_val is not None else ""
            total_checks += 1

            if rule.rule_type == "non_empty":
                if not val_str:
                    msg = f"Field '{rule.field}' is required and cannot be empty"
                    errors.append(msg)
                    if rule.severity == "error":
                        is_strictly_valid = False
                else:
                    passed_checks += 1

            elif rule.rule_type == "email_rfc":
                if val_str:
                    if not self.validate_email(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' fails standard email format validation"
                        errors.append(msg)
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                else:
                    # Optional field left blank
                    passed_checks += 0.5

            elif rule.rule_type in ["phone_format", "phone_e164"]:
                if val_str:
                    if not self.validate_phone(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' fails phone format validation (insufficient digits)"
                        errors.append(msg)
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                else:
                    passed_checks += 0.5

            elif rule.rule_type == "url_format":
                if val_str:
                    if not self.validate_url(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' is not a valid accessible URL format"
                        errors.append(msg)
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                else:
                    if rule.severity == "error":
                        is_strictly_valid = False
                        errors.append(f"Mandatory URL '{rule.field}' is missing")

            elif rule.rule_type == "regex":
                pattern = rule.params.get("pattern", "")
                if pattern and val_str:
                    if not re.search(pattern, val_str):
                        msg = f"Field '{rule.field}' did not match required pattern {pattern}"
                        errors.append(msg)
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                else:
                    passed_checks += 1

        confidence = round(passed_checks / max(total_checks, 1), 2)
        # Cap confidence between 0.50 and 0.99
        confidence = max(0.50, min(0.99, confidence))
        if not is_strictly_valid:
            confidence = min(confidence, 0.65)

        return is_strictly_valid, errors, confidence
