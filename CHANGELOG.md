# Changelog

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
