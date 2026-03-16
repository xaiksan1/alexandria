# Agentic-Ads Privacy Policy

**Effective date**: 2026-03-12
**Jurisdiction**: Québec, Canada (Loi 25 / Law 25)
**Last reviewed**: 2026-03-12

## Data We Collect

Agentic-Ads does **not** collect personally identifiable information (PII).

Bid targeting uses only:
- `product_vertical` — category of product being advertised (e.g. "cloud", "crypto")
- `geo_region_code` — coarse geographic region code (e.g. "QC-CA", "ON-CA")
- `device_class` — device category (e.g. "desktop", "mobile", "tablet")

These three fields are combined into a `cohorte_id` via:
```
cohorte_id = SHA256(product_vertical + "|" + geo_region_code + "|" + device_class)
```

**No user identifiers are stored or transmitted**: no IP address, no cookie, no
fingerprint, no user account ID.

## Data Retention

Bid cache entries expire after 3600 seconds (configurable via `ttl` parameter).
Bid history records are retained for 90 days for financial reconciliation.

## Data Security

All cached bid responses are encrypted at rest using AES-256-GCM with keys
derived from a BIP-39 mnemonic vault (PBKDF2-HMAC-SHA256, 100,000 iterations).

## Privacy Officer

See `officer.json` for contact information.

## Loi 25 Compliance Statement

This system was designed from inception to comply with Québec's Act respecting
the protection of personal information in the private sector (Loi 25). The
cohorte_id mechanism ensures that no personal information as defined under
Loi 25 is processed, stored, or transmitted.
