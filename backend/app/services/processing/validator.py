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

    def validate_record_detailed(
        self,
        record: Dict[str, Any],
        rules: List[ValidationRuleSpec]
    ) -> Tuple[bool, List[str], float, Dict[str, str], str]:
        """
        Validates a single record against the specified rules.
        Returns:
            - is_strictly_valid: True if no 'error' severity violations occurred
            - errors: List of validation issue descriptions
            - confidence_score: Float between 0.50 and 0.99
            - field_validations: Dict[str, str] ("VALID", "INVALID", "MISSING", "NEEDS_REVIEW")
            - confidence_level: "HIGH" | "MEDIUM" | "LOW"
        """
        errors: List[str] = []
        is_strictly_valid = True
        total_checks = 0
        passed_checks = 0

        # Initialize field statuses based on presence
        field_validations: Dict[str, str] = {}
        for k, v in record.items():
            if k.startswith("_"):
                continue
            if v is None or str(v).strip() == "":
                field_validations[k] = "MISSING"
            else:
                field_validations[k] = "VALID"

        for rule in rules:
            field_val = record.get(rule.field)
            val_str = str(field_val).strip() if field_val is not None else ""
            total_checks += 1

            if rule.rule_type == "non_empty":
                if not val_str:
                    msg = f"Field '{rule.field}' is required and cannot be empty"
                    errors.append(msg)
                    field_validations[rule.field] = "MISSING" if rule.severity != "error" else "INVALID"
                    if rule.severity == "error":
                        is_strictly_valid = False
                else:
                    passed_checks += 1
                    if field_validations.get(rule.field) != "INVALID":
                        field_validations[rule.field] = "VALID"

            elif rule.rule_type == "email_rfc":
                if val_str:
                    if not self.validate_email(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' fails standard email format validation"
                        errors.append(msg)
                        field_validations[rule.field] = "INVALID" if rule.severity == "error" else "NEEDS_REVIEW"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    passed_checks += 0.5
                    field_validations[rule.field] = "MISSING"

            elif rule.rule_type in ["phone_format", "phone_e164"]:
                if val_str:
                    if not self.validate_phone(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' fails phone format validation (insufficient digits)"
                        errors.append(msg)
                        field_validations[rule.field] = "INVALID" if rule.severity == "error" else "NEEDS_REVIEW"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    passed_checks += 0.5
                    field_validations[rule.field] = "MISSING"

            elif rule.rule_type == "url_format":
                if val_str:
                    if not self.validate_url(val_str):
                        msg = f"Field '{rule.field}' value '{val_str}' is not a valid accessible URL format"
                        errors.append(msg)
                        field_validations[rule.field] = "INVALID" if rule.severity == "error" else "NEEDS_REVIEW"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    if rule.severity == "error":
                        is_strictly_valid = False
                        field_validations[rule.field] = "INVALID"
                        errors.append(f"Mandatory URL '{rule.field}' is missing")
                    else:
                        field_validations[rule.field] = "MISSING"

            elif rule.rule_type == "domain_format":
                if val_str:
                    from app.services.processing.normalizer import DataNormalizer
                    domain = DataNormalizer.extract_root_domain(val_str) or val_str.lower()
                    if "." not in domain or len(domain.split(".")[-1]) < 2:
                        msg = f"Field '{rule.field}' value '{val_str}' is not a valid domain"
                        errors.append(msg)
                        field_validations[rule.field] = "INVALID" if rule.severity == "error" else "NEEDS_REVIEW"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    passed_checks += 0.5
                    field_validations[rule.field] = "MISSING"

            elif rule.rule_type == "numeric_range":
                if val_str:
                    try:
                        num = float(re.sub(r'[^\d.-]', '', val_str))
                        min_val = rule.params.get("min")
                        max_val = rule.params.get("max")
                        if (min_val is not None and num < float(min_val)) or (max_val is not None and num > float(max_val)):
                            msg = f"Field '{rule.field}' value {num} is outside permitted range [{min_val}, {max_val}]"
                            errors.append(msg)
                            field_validations[rule.field] = "INVALID"
                            if rule.severity == "error":
                                is_strictly_valid = False
                        else:
                            passed_checks += 1
                            field_validations[rule.field] = "VALID"
                    except ValueError:
                        errors.append(f"Field '{rule.field}' value '{val_str}' is not numeric")
                        field_validations[rule.field] = "INVALID"
                        if rule.severity == "error":
                            is_strictly_valid = False
                else:
                    passed_checks += 0.5
                    field_validations[rule.field] = "MISSING"

            elif rule.rule_type == "date_iso":
                if val_str:
                    date_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}', val_str))
                    if not date_valid:
                        errors.append(f"Field '{rule.field}' value '{val_str}' is not an ISO date (YYYY-MM-DD)")
                        field_validations[rule.field] = "INVALID"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    passed_checks += 0.5
                    field_validations[rule.field] = "MISSING"

            elif rule.rule_type == "regex":
                pattern = rule.params.get("pattern", "")
                if pattern and val_str:
                    if not re.search(pattern, val_str):
                        msg = f"Field '{rule.field}' did not match required pattern {pattern}"
                        errors.append(msg)
                        field_validations[rule.field] = "INVALID" if rule.severity == "error" else "NEEDS_REVIEW"
                        if rule.severity == "error":
                            is_strictly_valid = False
                    else:
                        passed_checks += 1
                        field_validations[rule.field] = "VALID"
                else:
                    passed_checks += 1


        confidence = round(passed_checks / max(total_checks, 1), 2)
        confidence = max(0.50, min(0.99, confidence))
        if not is_strictly_valid:
            confidence = min(confidence, 0.65)

        if confidence >= 0.85 and is_strictly_valid:
            confidence_level = "HIGH"
        elif confidence >= 0.70 and is_strictly_valid:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        return is_strictly_valid, errors, confidence, field_validations, confidence_level

    def validate_record(
        self,
        record: Dict[str, Any],
        rules: List[ValidationRuleSpec]
    ) -> Tuple[bool, List[str], float]:
        """Backward-compatible validation returning (is_valid, errors, confidence)."""
        valid, errors, conf, _, _ = self.validate_record_detailed(record, rules)
        return valid, errors, conf
