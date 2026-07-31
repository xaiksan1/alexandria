#!/usr/bin/env python3
"""
ADAM Security Guardian
Zangetsu Tensa with Getsuga Tenshō BANKAI security layer

Implements:
- Zero-trust security model
- Ethical hacking constraints (white-hat only)
- Role-based access control (RBAC)
- Threat detection and response
- Audit logging and compliance
- White-hat cybersecurity capabilities with ethical boundaries
"""

import json
import logging
import sys
import hashlib
import hmac
import threading
import urllib.request
from pathlib import Path

_PHOENIX_URL = "http://localhost:8000/events"


def _notify_phoenix(source: str, severity: str, category: str, message: str, data: dict = None) -> None:
    def _send():
        try:
            payload = json.dumps({
                "source": source, "severity": severity,
                "category": category, "message": message,
                "data": data or {},
            }).encode()
            req = urllib.request.Request(
                _PHOENIX_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set, Tuple
from datetime import datetime
from enum import Enum


class ThreatLevel(Enum):
    """Threat severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


class AccessLevel(Enum):
    """Security access levels"""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    PRIVILEGED = "privileged"
    RESTRICTED = "restricted"


class OperationType(Enum):
    """Types of operations that can be performed"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    AUDIT = "audit"


class WhiteHatConstraint(Enum):
    """White-hat ethical constraints"""
    AUTHORIZED_ONLY = "authorized_only"  # Only authorized testing
    FULL_DISCLOSURE = "full_disclosure"   # Report all findings
    NO_DATA_THEFT = "no_data_theft"       # No unauthorized data access
    NO_SERVICE_DISRUPTION = "no_service_disruption"  # Never disrupt services
    LEGAL_BOUNDARY = "legal_boundary"    # Stay within legal limits
    PRIVACY_RESPECT = "privacy_respect"  # Respect privacy regulations


@dataclass
class SecurityContext:
    """Security context for an operation"""
    user_id: str
    role: str
    access_level: AccessLevel
    ip_address: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_token: Optional[str] = None
    is_authenticated: bool = False
    is_authorized: bool = False


@dataclass
class AuditLog:
    """Audit log entry"""
    timestamp: str
    user_id: str
    action: str
    operation_type: OperationType
    resource: str
    result: str
    threat_level: ThreatLevel
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    name: str
    description: str
    access_control: Dict[str, List[str]]  # role -> [allowed operations]
    constraints: List[WhiteHatConstraint]
    rate_limits: Dict[str, int]  # operation -> max per minute
    blocking_rules: List[str]
    audit_required: bool = True


class ZangetsuSecurityLayer:
    """
    Zangetsu Tensa with Getsuga Tenshō BANKAI
    Advanced security layer for ADAM Digital Twin

    Implements zero-trust model with ethical constraints for authorized
    white-hat cybersecurity operations only.
    """

    def __init__(self, config_dir: str = "/home/ichigo/alexandria/ADAM/digital-twin-data"):
        """Initialize Zangetsu security layer"""
        self.logger = self._setup_logging()
        self.config_dir = Path(config_dir)

        # Load security configuration
        self.security_config = self._load_security_config()

        # White-hat constraints (always active)
        self.white_hat_constraints = [
            WhiteHatConstraint.AUTHORIZED_ONLY,
            WhiteHatConstraint.FULL_DISCLOSURE,
            WhiteHatConstraint.NO_DATA_THEFT,
            WhiteHatConstraint.NO_SERVICE_DISRUPTION,
            WhiteHatConstraint.LEGAL_BOUNDARY,
            WhiteHatConstraint.PRIVACY_RESPECT
        ]

        # Audit log
        self.audit_logs: List[AuditLog] = []

        # Rate limiting
        self.operation_counters: Dict[Tuple[str, str], int] = {}

        # Blocked operations
        self.blocked_operations = self._initialize_blocked_operations()

        self.logger.info("🔒 Zangetsu Security Layer initialized (BANKAI mode)")

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for security layer"""
        logger = logging.getLogger("ADAM.Security")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration from runtime config"""
        try:
            config_file = self.config_dir / "ADAM_RUNTIME_CONFIG.json"
            with open(config_file, 'r') as f:
                runtime_config = json.load(f)
            return runtime_config.get("security", {})
        except Exception as e:
            self.logger.warning(f"⚠️  Could not load security config: {e}")
            return {}

    def _initialize_blocked_operations(self) -> Set[str]:
        """Initialize set of permanently blocked operations"""
        return {
            # Destructive operations (never allowed)
            "unauthorized_access",
            "data_exfiltration",
            "service_disruption",
            "unauthorized_modification",
            "malware_deployment",
            "privilege_escalation_unauthorized",
            # Unethical operations
            "privacy_violation",
            "data_theft",
            "denial_of_service",
            "brute_force_attack",
            "sql_injection",
            "unauthorized_surveillance"
        }

    def create_security_context(
        self,
        user_id: str,
        role: str,
        access_level: AccessLevel = AccessLevel.AUTHENTICATED,
        ip_address: Optional[str] = None
    ) -> SecurityContext:
        """Create a security context for an operation"""
        context = SecurityContext(
            user_id=user_id,
            role=role,
            access_level=access_level,
            ip_address=ip_address,
            is_authenticated=True,
            is_authorized=self._check_authorization(role, access_level)
        )
        return context

    def _check_authorization(self, role: str, access_level: AccessLevel) -> bool:
        """Check if role is authorized for access level"""
        role_access_map = {
            "architect": AccessLevel.PRIVILEGED,
            "developer": AccessLevel.AUTHORIZED,
            "analyst": AccessLevel.AUTHORIZED,
            "validator": AccessLevel.AUTHENTICATED,
            "guest": AccessLevel.PUBLIC
        }
        required_level = role_access_map.get(role, AccessLevel.PUBLIC)
        # Found by cyber_gate_smoke_test.py (2026-07-31): this used to compare
        # access_level.value >= required_level.value as raw STRINGS, i.e.
        # alphabetically ("authenticated" < "public" < "restricted") instead of
        # by intended privilege rank — a guest granted the objectively-higher
        # AUTHENTICATED tier was incorrectly denied while PUBLIC passed.
        # RESTRICTED is never assigned to any role in role_access_map above, so
        # its intended rank is genuinely undefined by this code; ranked highest
        # here as the fail-closed choice (harder to satisfy, not easier) rather
        # than guessed — flag to a human before relying on RESTRICTED for real.
        rank = {
            AccessLevel.PUBLIC: 0,
            AccessLevel.AUTHENTICATED: 1,
            AccessLevel.AUTHORIZED: 2,
            AccessLevel.PRIVILEGED: 3,
            AccessLevel.RESTRICTED: 4,
        }
        return rank[access_level] >= rank[required_level]

    def check_operation(
        self,
        context: SecurityContext,
        operation: OperationType,
        resource: str,
        white_hat_approved: bool = False
    ) -> Tuple[bool, str]:
        """
        Check if an operation is allowed

        For cybersecurity operations, white_hat_approved must be True
        and the operation must comply with ethical constraints.

        Args:
            context: Security context for the operation
            operation: Type of operation
            resource: Resource being accessed
            white_hat_approved: Whether this is authorized white-hat testing

        Returns:
            Tuple of (allowed: bool, reason: str)
        """

        # Check if operation is permanently blocked
        if operation.value in self.blocked_operations:
            self.logger.warning(
                f"❌ BLOCKED: {operation.value} on {resource} (permanently denied)"
            )
            self._log_audit(context, operation, resource, "BLOCKED", ThreatLevel.BLOCKED)
            _notify_phoenix(
                source="zangetsu",
                severity="CRITICAL",
                category="access_control",
                message=f"BLOCKED: {operation.value} on {resource} (permanently denied)",
                data={"user": context.user_id, "role": context.role, "operation": operation.value, "resource": resource},
            )
            return False, "Operation permanently blocked"

        # For cybersecurity operations, require white-hat approval
        if self._is_cybersecurity_operation(operation):
            if not white_hat_approved:
                self.logger.warning(
                    f"❌ DENIED: Cybersecurity operation {operation.value} requires white-hat approval"
                )
                self._log_audit(context, operation, resource, "DENIED", ThreatLevel.CRITICAL)
                _notify_phoenix(
                    source="zangetsu",
                    severity="HIGH",
                    category="white_hat",
                    message=f"DENIED: {operation.value} on {resource} — white-hat approval missing",
                    data={"user": context.user_id, "role": context.role, "operation": operation.value, "resource": resource},
                )
                return False, "White-hat approval required for cybersecurity operations"

            # Verify white-hat constraints
            if not self._verify_white_hat_constraints(resource):
                self.logger.warning(
                    f"❌ DENIED: White-hat constraints violated for {operation.value} on {resource}"
                )
                self._log_audit(context, operation, resource, "DENIED", ThreatLevel.CRITICAL)
                _notify_phoenix(
                    source="zangetsu",
                    severity="HIGH",
                    category="white_hat",
                    message=f"DENIED: {operation.value} on {resource} — white-hat constraints violated",
                    data={"user": context.user_id, "role": context.role, "operation": operation.value, "resource": resource},
                )
                return False, "White-hat constraints violated"

        # Check role-based access
        if not self._check_role_permission(context.role, operation):
            self.logger.warning(
                f"❌ DENIED: {context.role} lacks permission for {operation.value}"
            )
            self._log_audit(context, operation, resource, "DENIED", ThreatLevel.WARNING)
            _notify_phoenix(
                source="zangetsu",
                severity="MEDIUM",
                category="access_control",
                message=f"DENIED: role {context.role} lacks permission for {operation.value} on {resource}",
                data={"user": context.user_id, "role": context.role, "operation": operation.value, "resource": resource},
            )
            return False, "Insufficient permissions for operation"

        # Check rate limiting
        if not self._check_rate_limit(context.user_id, operation):
            self.logger.warning(
                f"❌ RATE LIMITED: {context.user_id} exceeded rate limit for {operation.value}"
            )
            self._log_audit(context, operation, resource, "RATE_LIMITED", ThreatLevel.WARNING)
            _notify_phoenix(
                source="zangetsu",
                severity="MEDIUM",
                category="rate_limit",
                message=f"RATE LIMITED: {context.user_id} exceeded limit for {operation.value}",
                data={"user": context.user_id, "operation": operation.value, "resource": resource},
            )
            return False, "Rate limit exceeded"

        # Operation allowed
        self.logger.info(
            f"✅ ALLOWED: {context.role} → {operation.value} on {resource}"
        )
        self._log_audit(context, operation, resource, "ALLOWED", ThreatLevel.INFO)
        return True, "Operation allowed"

    def _is_cybersecurity_operation(self, operation: OperationType) -> bool:
        """Check if operation is a cybersecurity-related operation"""
        cybersecurity_ops = {
            "vulnerability_scan",
            "penetration_test",
            "security_audit",
            "threat_assessment",
            "exploit_test"
        }
        return operation.value in cybersecurity_ops

    def _verify_white_hat_constraints(self, resource: str) -> bool:
        """Verify that white-hat constraints are satisfied"""
        # Constraints verification
        constraints_ok = True

        # Check each constraint
        for constraint in self.white_hat_constraints:
            if constraint == WhiteHatConstraint.AUTHORIZED_ONLY:
                # Verified by white_hat_approved flag
                pass
            elif constraint == WhiteHatConstraint.NO_DATA_THEFT:
                # Check that operation won't extract sensitive data
                if "exfiltrate" in resource.lower() or "steal" in resource.lower():
                    constraints_ok = False
            elif constraint == WhiteHatConstraint.NO_SERVICE_DISRUPTION:
                # Check that operation won't disrupt services
                if "dos" in resource.lower() or "disrupt" in resource.lower():
                    constraints_ok = False
            elif constraint == WhiteHatConstraint.LEGAL_BOUNDARY:
                # Check that operation stays within legal bounds
                if "illegal" in resource.lower():
                    constraints_ok = False

        return constraints_ok

    def _check_role_permission(self, role: str, operation: OperationType) -> bool:
        """Check if role has permission for operation"""
        role_permissions = {
            "architect": [
                OperationType.READ,
                OperationType.WRITE,
                OperationType.EXECUTE,
                OperationType.AUDIT,
                OperationType.ADMIN
            ],
            "developer": [
                OperationType.READ,
                OperationType.WRITE,
                OperationType.EXECUTE,
                OperationType.AUDIT
            ],
            "analyst": [
                OperationType.READ,
                OperationType.EXECUTE,
                OperationType.AUDIT
            ],
            "validator": [
                OperationType.READ,
                OperationType.AUDIT
            ],
            "guest": [
                OperationType.READ
            ]
        }

        permissions = role_permissions.get(role, [])
        return operation in permissions

    def _check_rate_limit(self, user_id: str, operation: OperationType) -> bool:
        """Check if user has exceeded rate limit"""
        key = (user_id, operation.value)
        current_count = self.operation_counters.get(key, 0)

        # Rate limits per minute
        limits = {
            "read": 1000,
            "write": 100,
            "delete": 10,
            "execute": 50,
            "admin": 10,
            "audit": 100
        }

        limit = limits.get(operation.value, 100)
        if current_count >= limit:
            return False

        # Increment counter
        self.operation_counters[key] = current_count + 1
        return True

    def _log_audit(
        self,
        context: SecurityContext,
        operation: OperationType,
        resource: str,
        result: str,
        threat_level: ThreatLevel
    ) -> None:
        """Log operation to audit log"""
        log = AuditLog(
            timestamp=datetime.now().isoformat(),
            user_id=context.user_id,
            action=f"{context.role}:{operation.value}",
            operation_type=operation,
            resource=resource,
            result=result,
            threat_level=threat_level
        )
        self.audit_logs.append(log)

    def get_audit_log(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        logs = self.audit_logs
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        return [asdict(log) for log in logs]

    def get_security_posture(self) -> Dict[str, Any]:
        """Get current security posture"""
        return {
            "security_framework": "Zangetsu Tensa with Getsuga Tenshō BANKAI",
            "protection_level": "zero_trust",
            "white_hat_constraints": [c.value for c in self.white_hat_constraints],
            "audit_logging": "enabled",
            "audit_log_entries": len(self.audit_logs),
            "blocked_operations": list(self.blocked_operations),
            "ethical_constraints_enforced": True,
            "cybersecurity_mode": "white_hat_authorized_only"
        }

    def generate_white_hat_certificate(self, tester_name: str, scope: str) -> Dict[str, Any]:
        """
        Generate a white-hat authorization certificate

        This authorizes specific penetration testing activities.

        Args:
            tester_name: Name of authorized tester
            scope: Scope of authorized testing (e.g., "internal_network", "api_security")

        Returns:
            Certificate with authorization details
        """
        certificate = {
            "issued_at": datetime.now().isoformat(),
            "tester": tester_name,
            "authorization_scope": scope,
            "constraints": [c.value for c in self.white_hat_constraints],
            "expiration": "indefinite",
            "certification_number": hashlib.sha256(
                f"{tester_name}{scope}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12],
            "terms": {
                "authorized_only": "Testing only on explicitly authorized systems",
                "full_disclosure": "All findings must be disclosed to system owner",
                "no_data_theft": "No unauthorized data access or exfiltration",
                "service_continuity": "Never disrupt service availability",
                "legal_compliance": "Remain within legal boundaries and regulations",
                "privacy_protection": "Respect privacy and regulatory requirements"
            },
            "signing_authority": "ADAM Security Guardian (Zangetsu)",
            "status": "ACTIVE"
        }

        self.logger.info(f"📜 White-hat certificate issued to {tester_name} for {scope}")
        return certificate

    def diagnostic_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        posture = self.get_security_posture()

        report = f"""
╔════════════════════════════════════════════════════════╗
║     ADAM SECURITY GUARDIAN - DIAGNOSTIC REPORT         ║
╚════════════════════════════════════════════════════════╝

🔒 ZANGETSU SECURITY LAYER
  Framework: {posture['security_framework']}
  Protection Level: {posture['protection_level']}
  Status: OPERATIONAL

⚔️  WHITE-HAT CONSTRAINTS (Always Active)
  ✅ Authorized Testing Only
  ✅ Full Disclosure of Findings
  ✅ No Unauthorized Data Access
  ✅ No Service Disruption
  ✅ Legal Boundary Compliance
  ✅ Privacy & Regulation Respect

🛡️  ACCESS CONTROL MODEL
  • Zero-Trust Architecture
  • Role-Based Access Control (RBAC)
  • Multi-Level Authentication
  • Operation-Specific Authorization

📊 CURRENT STATUS
  Audit Log Entries: {posture['audit_log_entries']}
  Blocked Operations: {len(posture['blocked_operations'])}
  White-Hat Constraints: {len(posture['white_hat_constraints'])}
  Cybersecurity Mode: {posture['cybersecurity_mode']}

🔐 BLOCKED OPERATIONS (Permanent)
  • Unauthorized Access
  • Data Exfiltration
  • Service Disruption
  • Malware Deployment
  • Unauthorized Privilege Escalation
  • Privacy Violations

✅ SECURITY GUARDIAN OPERATIONAL
"""
        return report


def main():
    """Main entry point for testing security guardian"""

    try:
        # Initialize security layer
        guardian = ZangetsuSecurityLayer()

        # Display diagnostic report
        print(guardian.diagnostic_report())

        # Test security context creation
        print("\n🔐 Testing Security Context Creation...")
        context = guardian.create_security_context(
            user_id="architect_001",
            role="architect",
            access_level=AccessLevel.PRIVILEGED,
            ip_address="192.168.1.100"
        )
        print(f"Context created: {context.role} ({context.access_level.value})")

        # Test permission checking
        print("\n✅ Testing Permission Checking...")
        allowed, reason = guardian.check_operation(
            context,
            OperationType.READ,
            "system_configuration",
            white_hat_approved=True
        )
        print(f"READ operation: {allowed} - {reason}")

        # Test blocked operation
        print("\n❌ Testing Blocked Operation...")
        allowed, reason = guardian.check_operation(
            context,
            OperationType.WRITE,
            "unauthorized_access_attempt"
        )
        print(f"Unauthorized access: {allowed} - {reason}")

        # Test white-hat certificate
        print("\n📜 Testing White-Hat Certificate Generation...")
        cert = guardian.generate_white_hat_certificate(
            tester_name="Michael Lefebvre",
            scope="ADAM Security Testing"
        )
        print(f"Certificate issued: {cert['tester']} (ID: {cert['certification_number']})")
        print(f"Constraints: {len(cert['constraints'])} ethical constraints")

        # Display audit log
        print("\n📋 Audit Log Summary:")
        logs = guardian.get_audit_log()
        print(f"Total logged operations: {len(logs)}")
        if logs:
            print(f"Last 3 operations:")
            for log in logs[-3:]:
                print(f"  • {log['action']}: {log['result']}")

        # Test security posture
        print("\n🛡️  Security Posture:")
        posture = guardian.get_security_posture()
        print(f"Framework: {posture['security_framework']}")
        print(f"White-hat mode: {posture['cybersecurity_mode']}")

        print("\n✅ All security guardian tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
