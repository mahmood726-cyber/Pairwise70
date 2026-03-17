"""
TruthCert Validation Gates (B3, B4, B5)

B3: Structural validation (logical constraints)
B4: Anti-mixing detection (arm swap detection)
B5: Semantic validation (domain-specific rules)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import math

from ..core.primitives import GateOutcome, ScopeLock
from .witness_gates import BaseGate


class StructuralGate(BaseGate):
    """
    Gate B3 - Structural Validation

    Validates logical constraints that must hold regardless of content:
    - CI lower <= point estimate <= CI upper
    - Sample sizes are positive integers
    - Proportions are between 0 and 1
    - Percentages are between 0 and 100
    - Risk ratios/hazard ratios are positive
    """

    def __init__(self):
        super().__init__("B3")

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Validate structural constraints on extracted values.
        """
        consensus = getattr(context, 'consensus_values', {})

        if not consensus:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"message": "No values to validate"},
            )

        violations = []

        # Check CI containment
        ci_violations = self._check_ci_containment(consensus)
        violations.extend(ci_violations)

        # Check value ranges
        range_violations = self._check_value_ranges(consensus)
        violations.extend(range_violations)

        # Check logical relationships
        logic_violations = self._check_logical_relationships(consensus)
        violations.extend(logic_violations)

        if violations:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Structural validation failed: {len(violations)} violations",
                details={"violations": violations},
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "fields_validated": len(consensus),
                "checks_passed": True,
            },
        )

    def _check_ci_containment(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check that confidence intervals contain point estimates."""
        violations = []

        # Find point estimate / CI triplets
        point_patterns = ["_point", "_estimate", "_mean", "_hr", "_or", "_rr"]
        lower_patterns = ["_ci_lower", "_lower", "_ci_lo", "_lo"]
        upper_patterns = ["_ci_upper", "_upper", "_ci_hi", "_hi"]

        for key, value in values.items():
            if not isinstance(value, (int, float)):
                continue

            # Check if this is a point estimate
            is_point = any(p in key.lower() for p in point_patterns)
            if not is_point:
                continue

            # Find corresponding CI bounds
            base = key
            for pattern in point_patterns:
                if pattern in key.lower():
                    base = key.lower().replace(pattern, "")
                    break

            # Look for lower bound
            lower_key = None
            lower_val = None
            for lp in lower_patterns:
                candidate = f"{base}{lp}"
                for vk, vv in values.items():
                    if vk.lower() == candidate and isinstance(vv, (int, float)):
                        lower_key = vk
                        lower_val = vv
                        break
                if lower_val is not None:
                    break

            # Look for upper bound
            upper_key = None
            upper_val = None
            for up in upper_patterns:
                candidate = f"{base}{up}"
                for vk, vv in values.items():
                    if vk.lower() == candidate and isinstance(vv, (int, float)):
                        upper_key = vk
                        upper_val = vv
                        break
                if upper_val is not None:
                    break

            # Validate if we have all three
            if lower_val is not None and upper_val is not None:
                # Allow small tolerance for rounding
                tolerance = 0.001
                if value < lower_val - tolerance or value > upper_val + tolerance:
                    violations.append({
                        "type": "ci_containment",
                        "field": key,
                        "point": value,
                        "lower": lower_val,
                        "upper": upper_val,
                        "message": f"Point estimate {value} not in CI [{lower_val}, {upper_val}]",
                    })

                # Also check CI order
                if lower_val > upper_val:
                    violations.append({
                        "type": "ci_order",
                        "lower_field": lower_key,
                        "upper_field": upper_key,
                        "lower": lower_val,
                        "upper": upper_val,
                        "message": f"CI lower ({lower_val}) > upper ({upper_val})",
                    })

        return violations

    def _check_value_ranges(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check that values are in valid ranges based on field names."""
        violations = []

        for key, value in values.items():
            if not isinstance(value, (int, float)):
                continue

            key_lower = key.lower()

            # Sample size must be positive integer
            if any(p in key_lower for p in ["sample_size", "n_", "_n", "count", "subjects"]):
                if value < 0:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"Sample size cannot be negative: {value}",
                    })
                if isinstance(value, float) and not value.is_integer():
                    violations.append({
                        "type": "invalid_type",
                        "field": key,
                        "value": value,
                        "message": f"Sample size must be integer: {value}",
                    })

            # Proportions between 0 and 1
            if any(p in key_lower for p in ["proportion", "probability", "rate"]):
                if value < 0 or value > 1:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"Proportion must be between 0 and 1: {value}",
                    })

            # Percentages between 0 and 100
            if "percent" in key_lower or key.endswith("%"):
                if value < 0 or value > 100:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"Percentage must be between 0 and 100: {value}",
                    })

            # Risk ratios, hazard ratios, odds ratios must be positive
            if any(p in key_lower for p in ["hr", "or", "rr", "hazard", "odds", "risk_ratio"]):
                if value <= 0:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"Ratio must be positive: {value}",
                    })

            # Standard errors must be positive
            if any(p in key_lower for p in ["se", "std_err", "standard_error"]):
                if value < 0:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"Standard error cannot be negative: {value}",
                    })

            # P-values between 0 and 1
            if any(p in key_lower for p in ["p_value", "pvalue", "p-value"]):
                if value < 0 or value > 1:
                    violations.append({
                        "type": "invalid_range",
                        "field": key,
                        "value": value,
                        "message": f"P-value must be between 0 and 1: {value}",
                    })

        return violations

    def _check_logical_relationships(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check logical relationships between fields."""
        violations = []

        # Total events <= total sample size
        event_keys = [k for k in values if "event" in k.lower()]
        n_keys = [k for k in values if any(p in k.lower() for p in ["sample_size", "_n", "subjects"])]

        for ek in event_keys:
            ev = values[ek]
            if not isinstance(ev, (int, float)):
                continue

            # Find corresponding sample size
            for nk in n_keys:
                nv = values[nk]
                if not isinstance(nv, (int, float)):
                    continue

                # Check if they're for the same arm/group
                if self._same_group(ek, nk):
                    if ev > nv:
                        violations.append({
                            "type": "logical_constraint",
                            "event_field": ek,
                            "n_field": nk,
                            "events": ev,
                            "n": nv,
                            "message": f"Events ({ev}) > sample size ({nv})",
                        })

        return violations

    def _same_group(self, key1: str, key2: str) -> bool:
        """Check if two keys refer to the same group/arm."""
        # Extract group identifiers
        groups = ["treatment", "control", "intervention", "placebo", "arm1", "arm2", "group1", "group2"]

        for g in groups:
            if g in key1.lower() and g in key2.lower():
                return True

        return False


class AntiMixingGate(BaseGate):
    """
    Gate B4 - Anti-Mixing Detection

    Detects if treatment arm values have been swapped or mixed.
    Critical for meta-analysis where arm mixing inverts effect direction.

    Detection strategies:
    1. Label-value consistency checking
    2. Effect direction plausibility
    3. Cross-reference with source text
    """

    def __init__(self):
        super().__init__("B4")

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Detect potential arm mixing/swapping.
        """
        consensus = getattr(context, 'consensus_values', {})
        scope_lock: Optional[ScopeLock] = getattr(context, 'scope_lock', None)

        if not consensus:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"message": "No values to check for mixing"},
            )

        mixing_signals = []

        # Check for suspicious patterns
        label_issues = self._check_label_consistency(consensus, scope_lock)
        mixing_signals.extend(label_issues)

        # Check effect direction plausibility
        direction_issues = self._check_effect_direction(consensus, scope_lock)
        mixing_signals.extend(direction_issues)

        # Check for arm value swaps
        swap_issues = self._detect_arm_swaps(consensus)
        mixing_signals.extend(swap_issues)

        if mixing_signals:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Potential arm mixing detected: {len(mixing_signals)} signals",
                details={"mixing_signals": mixing_signals},
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={"mixing_checked": True, "no_issues": True},
        )

    def _check_label_consistency(
        self,
        values: Dict[str, Any],
        scope_lock: Optional[ScopeLock],
    ) -> List[Dict[str, Any]]:
        """Check that arm labels are consistent with expected entities."""
        issues = []

        if not scope_lock:
            return issues

        expected_entities = set(e.lower() for e in scope_lock.entities)

        # Find arm-labeled fields
        arm_fields = {}
        for key, value in values.items():
            key_lower = key.lower()

            # Extract arm label from key
            for entity in expected_entities:
                if entity in key_lower:
                    arm_fields.setdefault(entity, []).append((key, value))

        # Check if we found fields for all expected entities
        missing_entities = expected_entities - set(arm_fields.keys())
        if missing_entities and len(expected_entities) > 1:
            issues.append({
                "type": "missing_arm",
                "missing": list(missing_entities),
                "found": list(arm_fields.keys()),
                "message": f"Missing data for arms: {missing_entities}",
            })

        return issues

    def _check_effect_direction(
        self,
        values: Dict[str, Any],
        scope_lock: Optional[ScopeLock],
    ) -> List[Dict[str, Any]]:
        """Check if effect direction is plausible."""
        issues = []

        # Find effect size estimates
        effect_patterns = ["hr", "or", "rr", "hazard", "odds", "risk_ratio", "effect"]

        for key, value in values.items():
            if not isinstance(value, (int, float)):
                continue

            key_lower = key.lower()
            if not any(p in key_lower for p in effect_patterns):
                continue

            # Look for corresponding p-value
            base = re.sub(r'_(hr|or|rr|effect|estimate)$', '', key_lower)
            p_value = None
            for pk, pv in values.items():
                if pk.lower().startswith(base) and "p" in pk.lower():
                    if isinstance(pv, (int, float)) and 0 <= pv <= 1:
                        p_value = pv
                        break

            # If effect is significant but magnitude is implausible
            if p_value is not None and p_value < 0.05:
                # Very large or very small effects are suspicious
                if value > 10 or (value > 0 and value < 0.1):
                    issues.append({
                        "type": "implausible_effect",
                        "field": key,
                        "value": value,
                        "p_value": p_value,
                        "message": f"Significant effect with implausible magnitude: {value}",
                    })

        return issues

    def _detect_arm_swaps(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect if treatment and control values might be swapped."""
        issues = []

        # Look for paired treatment/control values
        treatment_patterns = ["treatment", "intervention", "active", "experimental", "arm1"]
        control_patterns = ["control", "placebo", "comparator", "arm2"]

        treatment_values = {}
        control_values = {}

        for key, value in values.items():
            if not isinstance(value, (int, float)):
                continue

            key_lower = key.lower()

            # Classify as treatment or control
            is_treatment = any(p in key_lower for p in treatment_patterns)
            is_control = any(p in key_lower for p in control_patterns)

            # Extract metric type
            metric = re.sub(r'(treatment|control|intervention|placebo|arm\d)_?', '', key_lower)
            metric = metric.strip('_')

            if is_treatment:
                treatment_values[metric] = (key, value)
            elif is_control:
                control_values[metric] = (key, value)

        # Check for suspicious patterns
        for metric in set(treatment_values.keys()) & set(control_values.keys()):
            t_key, t_val = treatment_values[metric]
            c_key, c_val = control_values[metric]

            # For event counts/rates, usually expect treatment <= control for beneficial effect
            if "event" in metric or "death" in metric or "mortality" in metric:
                # If treatment has MORE events, flag for review
                if t_val > c_val * 1.5:  # 50% more events in treatment
                    issues.append({
                        "type": "potential_swap",
                        "metric": metric,
                        "treatment_field": t_key,
                        "treatment_value": t_val,
                        "control_field": c_key,
                        "control_value": c_val,
                        "message": f"Treatment has significantly more events - verify arm labels",
                    })

        return issues


class SemanticGate(BaseGate):
    """
    Gate B5 - Semantic Validation

    Domain-specific validation rules for medical/clinical data:
    - Endpoint-specific constraints
    - Unit consistency
    - Timepoint alignment
    """

    def __init__(self):
        super().__init__("B5")

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Validate semantic consistency of extracted values.
        """
        consensus = getattr(context, 'consensus_values', {})
        scope_lock: Optional[ScopeLock] = getattr(context, 'scope_lock', None)

        if not consensus:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"message": "No values for semantic validation"},
            )

        violations = []

        # Endpoint-specific validation
        if scope_lock:
            endpoint_violations = self._validate_endpoint_constraints(
                consensus, scope_lock.endpoint
            )
            violations.extend(endpoint_violations)

        # Unit consistency
        unit_violations = self._check_unit_consistency(consensus)
        violations.extend(unit_violations)

        # Timepoint alignment
        if scope_lock:
            timepoint_violations = self._check_timepoint_alignment(
                consensus, scope_lock.timepoint
            )
            violations.extend(timepoint_violations)

        if violations:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Semantic validation failed: {len(violations)} issues",
                details={"violations": violations},
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={"semantic_validation": "passed"},
        )

    def _validate_endpoint_constraints(
        self,
        values: Dict[str, Any],
        endpoint: str,
    ) -> List[Dict[str, Any]]:
        """Apply endpoint-specific validation rules."""
        violations = []
        endpoint_lower = endpoint.lower()

        # Mortality endpoints
        if any(term in endpoint_lower for term in ["mortality", "death", "survival"]):
            for key, value in values.items():
                if not isinstance(value, (int, float)):
                    continue

                # Mortality rates should be 0-100% (or 0-1)
                if "rate" in key.lower() or "proportion" in key.lower():
                    if value > 1:  # Assuming percentage
                        if value > 100:
                            violations.append({
                                "type": "endpoint_constraint",
                                "endpoint": endpoint,
                                "field": key,
                                "value": value,
                                "message": f"Mortality rate > 100%: {value}",
                            })
                    else:  # Assuming proportion
                        if value > 1 or value < 0:
                            violations.append({
                                "type": "endpoint_constraint",
                                "endpoint": endpoint,
                                "field": key,
                                "value": value,
                                "message": f"Mortality proportion not in [0,1]: {value}",
                            })

        # Time-to-event endpoints
        if any(term in endpoint_lower for term in ["time to", "progression-free", "pfs", "os"]):
            for key, value in values.items():
                if not isinstance(value, (int, float)):
                    continue

                # Hazard ratios should be positive
                if "hr" in key.lower() or "hazard" in key.lower():
                    if value <= 0:
                        violations.append({
                            "type": "endpoint_constraint",
                            "endpoint": endpoint,
                            "field": key,
                            "value": value,
                            "message": f"Hazard ratio must be positive: {value}",
                        })

                # Median survival times should be positive
                if "median" in key.lower():
                    if value <= 0:
                        violations.append({
                            "type": "endpoint_constraint",
                            "endpoint": endpoint,
                            "field": key,
                            "value": value,
                            "message": f"Median time must be positive: {value}",
                        })

        return violations

    def _check_unit_consistency(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for unit inconsistencies."""
        violations = []

        # Group related fields
        field_groups = {}
        for key in values:
            # Extract base name
            base = re.sub(r'_(treatment|control|arm\d|ci_\w+|point|lower|upper)$', '', key.lower())
            field_groups.setdefault(base, []).append(key)

        # Check for magnitude inconsistencies within groups
        for base, keys in field_groups.items():
            numeric_values = [(k, values[k]) for k in keys if isinstance(values[k], (int, float))]

            if len(numeric_values) < 2:
                continue

            # Check if magnitudes are wildly different (suggesting unit mismatch)
            magnitudes = [abs(v) for _, v in numeric_values if v != 0]
            if magnitudes:
                max_mag = max(magnitudes)
                min_mag = min(magnitudes)

                # More than 3 orders of magnitude difference is suspicious
                if min_mag > 0 and max_mag / min_mag > 1000:
                    violations.append({
                        "type": "unit_inconsistency",
                        "field_group": base,
                        "values": dict(numeric_values),
                        "message": f"Possible unit inconsistency in {base}: magnitude range {min_mag:.2e} to {max_mag:.2e}",
                    })

        return violations

    def _check_timepoint_alignment(
        self,
        values: Dict[str, Any],
        expected_timepoint: str,
    ) -> List[Dict[str, Any]]:
        """Check that extracted values align with expected timepoint."""
        violations = []

        # Extract numeric timepoint from expected
        expected_time = self._parse_timepoint(expected_timepoint)

        # Check time-related fields
        time_patterns = ["month", "week", "year", "day", "time", "follow"]

        for key, value in values.items():
            if not isinstance(value, (int, float)):
                continue

            key_lower = key.lower()
            if not any(p in key_lower for p in time_patterns):
                continue

            # Parse the unit from key
            extracted_time = self._parse_timepoint(f"{value} {key}")

            if expected_time and extracted_time:
                # Normalize to months for comparison
                expected_months = self._to_months(expected_time)
                extracted_months = self._to_months(extracted_time)

                if expected_months and extracted_months:
                    # Allow 20% tolerance
                    if abs(expected_months - extracted_months) / expected_months > 0.2:
                        violations.append({
                            "type": "timepoint_mismatch",
                            "field": key,
                            "expected": expected_timepoint,
                            "extracted": value,
                            "message": f"Timepoint mismatch: expected ~{expected_timepoint}, found {value}",
                        })

        return violations

    def _parse_timepoint(self, text: str) -> Optional[Tuple[float, str]]:
        """Parse a timepoint string into (value, unit)."""
        text = text.lower()

        patterns = [
            (r'(\d+\.?\d*)\s*month', 'month'),
            (r'(\d+\.?\d*)\s*week', 'week'),
            (r'(\d+\.?\d*)\s*year', 'year'),
            (r'(\d+\.?\d*)\s*day', 'day'),
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, text)
            if match:
                return (float(match.group(1)), unit)

        return None

    def _to_months(self, time_tuple: Tuple[float, str]) -> Optional[float]:
        """Convert a time tuple to months."""
        value, unit = time_tuple

        conversions = {
            'month': 1,
            'week': 1/4.33,
            'year': 12,
            'day': 1/30,
        }

        if unit in conversions:
            return value * conversions[unit]

        return None
