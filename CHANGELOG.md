# Changelog

## 1.0.0 — 2026-11-16

- Full original Marketplace branding with 256/512 px light/dark icons, 1000/2000 px logos and a 1600×480 header; deterministic artwork generator and CI dimension checks.
- Reworked Marketplace-first English README, new API reference, branding and troubleshooting documents, and privacy-safe diagnostics export.
- Replaced large raw Action1 reporting caches with aggregate page totals and exact paginated `total_items` where available.
- Staggered expensive reports behind the initial endpoint discovery; preserved 5-minute endpoint refresh, rotating update totals and 30-minute deep refresh.
- Added enterprise licensing and usage sensors, organization subscription usage, CVSS critical/high, CISA KEV and explicit vulnerability coverage.
- Expose per-endpoint **Missing critical updates** and **Missing other updates** from Action1's documented extended inventory fields when available, with conservative nonnegative count parsing.
- Never report a partial CVE sample as a complete severity breakdown. Do not silently convert API errors or unknown endpoint state to zero/offline.
- Optional sensitive or low-value hardware sensors default to disabled; existing domain and entity unique-ID keys remain stable.
- Added URL security, pagination, data-model, missing-data and rate-boundary regression tests.
- Added strict v1 release workflow gating on Python, Ruff, tests, hassfest, HACS metadata and branding before publishing a tagged ZIP archive.
- Temporary tenant-specific PowerShell diagnostic scripts remain outside the public repository.

**Limitations:** Report types and scalar field values vary by tenant. Organization-wide patch severity classification and exhaustive installed software inventory remain unverified; these are not fabricated. Explicit per-endpoint extended patch counts are supported. Full live testing is still required for all Home Assistant and Action1 account combinations.


## 0.1.0-alpha.2 — 2026-11-10

**Public experimental alpha. Production use not yet validated.**

- Action1 API OAuth 2.0 client with selectable cloud region, HTTPS-only fixed hosts and read-only resource calls.
- Discover organizations, endpoints and device data across multiple organizations.
- Per-endpoint online and pending-reboot binary sensors; distinguish `online_status` from generic agent `status`.
- Endpoint operating system, hardware, last-contact and update-state sensors.
- Rotating per-endpoint missing update lists; organization-level update and vulnerability reports.
- CVSS >=9 and explicit CISA KEV summary counts from reported records. Unknown severity remains unknown.
- Organization and enterprise summaries for groups, automations, software report rows, audit and script catalog counts.
- Sensitive scripts and audit records are **not** retained as raw coordinator reports.
- Defer expensive organization and enterprise reports until after initial endpoint discovery to avoid prolonged integration setup.
- Built-in request pacing and bounded pagination; no privileged remote actions.
- HACS integration structure, English/German configuration flow, Python tests, GitHub Actions, README and MIT license.

### Known limitations

- No real Home Assistant installation test yet; API schemas were sampled without sensitive values.
- Some Action1 fields may be structured objects and remain unknown instead of incorrectly becoming text.
- Software inventory is surfaced as report rows, not a verified inventory of unique installed applications.
- Security summaries can be incomplete in very large tenants because of record caps.
- Online/offline boolean parsing and update severity mapping need live-value validation.
- No patch deployment, remote reboot, script execution or automations control.
- Custom HACS repository installation is required; this repository is not in the HACS default catalog.

## 0.1.0-alpha.1 — 2026-11-10

- Initial local-only exploratory prototype. Not publicly released.
