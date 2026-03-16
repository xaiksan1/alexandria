# EFVP — Évaluation des facteurs relatifs à la vie privée
## Privacy Impact Assessment — Agentic-Ads Platform

**Date**: 2026-03-12
**Version**: 1.0
**Prepared by**: Alexandria Systems
**Jurisdiction**: Québec, Canada (Loi 25)

---

## 1. System Description

Agentic-Ads is a machine-to-machine (M2M) advertising bidding platform that
enables AI agents to purchase and serve contextually relevant sponsored
recommendations without human supervision.

## 2. Personal Information Assessment

| Data Field | Collected? | Justification |
|---|---|---|
| IP Address | ❌ No | Not captured at any layer |
| User ID / Account | ❌ No | No user accounts exist |
| Cookie / Session | ❌ No | No session tracking |
| Device Fingerprint | ❌ No | Not computed |
| Geolocation (precise) | ❌ No | Only coarse region code used |
| `product_vertical` | ✅ Yes | Category string, not personal |
| `geo_region_code` | ✅ Yes | Coarse region (e.g. "QC-CA"), not personal |
| `device_class` | ✅ Yes | Device category, not personal |

**Conclusion**: The system does not process personal information as defined
under Loi 25, Article 2. The `cohorte_id` (SHA256 hash of non-personal fields)
is a pseudonymous aggregate cohort identifier, not a personal identifier.

## 3. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Re-identification via cohorte_id | Very Low | Medium | SHA256 is one-way; 3 coarse fields → enormous hash space |
| Data breach of bid cache | Low | Low | AES-256-GCM encryption at rest; ephemeral TTL (3600s) |
| Cross-system PII leak | Very Low | High | No PII accepted at any API endpoint; validated at ingress |
| Revenue misattribution | Low | Medium | `payment_confirmed = TRUE` gate before revenue credit |

## 4. Technical Controls

- **Encryption**: AES-256-GCM (256-bit keys, PBKDF2-HMAC-SHA256, 100k iterations)
- **Hashing**: SHA256 for cohorte_id (one-way, collision-resistant)
- **TTL**: Automatic cache expiry (default 3600s)
- **Atomic writes**: `pending_revenue.json` uses `.tmp` → `os.replace()` pattern
- **Revenue gate**: `payment_confirmed = TRUE` required before any revenue credit

## 5. Loi 25 Obligations

| Obligation | Status | Notes |
|---|---|---|
| Désignation d'un responsable | ✅ | See officer.json |
| Politique de confidentialité | ✅ | See privacy.md |
| EFVP pour nouveaux systèmes | ✅ | This document |
| Consentement | N/A | No PII processed |
| Droit d'accès | N/A | No PII stored |
| Incidents de confidentialité | Planned | Phase 3 incident response |

## 6. Approval

This EFVP was reviewed and approved as part of the Agentic-Ads platform
design review (spec v3, 2026-03-12).
