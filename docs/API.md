# Action1 REST API mapping and data-quality rules

The integration uses Action1 REST API 3.x over HTTPS with OAuth 2.0 client credentials. The host is selected from a fixed allowlist, not constructed from account-provided URLs. Authentication posts to `/api/3.0/oauth2/token`; monitoring uses read-only GET endpoints.

The table below summarizes the read endpoints verified structurally from a **sanitized, multi-organization Action1 API probe**. Exact return values for every tenant and model have not been verified.

| Scope | Relative endpoint | Data extracted |
|---|---|---|
| Tenant | `/organizations` | Organizations accessible to the API client |
| Organization | `/endpoints/managed/{orgId}?fields=*` | Device ID/name, `online_status`, OS, CPU, last seen, reboot, agent and inventory |
| Endpoint | `/endpoints/managed/{orgId}/{endpointId}/missing-updates` | `total_items`, update count |
| Organization | `/vulnerabilities/{orgId}` | `total_items`; `cvss_score`; `cisa_kev` |
| Organization | `/updates/{orgId}` | `total_items`; update catalog |
| Organization | `/installed-software/{orgId}/data` | Software report totals; **not** unique installed program totals |
| Organization | `/endpoints/groups/{orgId}` | Endpoint group count |
| Organization | `/automations/schedules/{orgId}` | Schedule count |
| Organization | `/automations/instances/{orgId}` | Automation execution count |
| Organization | `/logs/{orgId}` | Log entry count |
| Organization | `/endpoints/deployers/{orgId}` | Deployment agent count |
| Organization | `/installed-software/{orgId}/errors` | Inventory error count |
| Organization | `/subscription/usage/organizations/{orgId}` | Active/inactive/monthly-average endpoint counts |
| Enterprise | `/subscription/enterprise` | License status/type/expiry and licensed, free, actual counts |
| Enterprise | `/subscription/usage/enterprise` | Active/inactive/monthly-average endpoint counts |
| Enterprise | `/reports/all`, `/audit/events`, `/scripts/all` | Aggregate counts only; never retain script text or audit bodies |

## Scalar fields

Known endpoint inventory field names include `OS`, `CPU_name`, `CPU_size`, `RAM`, `architecture`, `manufacturer`, `agent_version`, `agent_install_date`, `last_seen`, `last_boot_time`, `online_status`, `reboot_required`, `update_status`, `vulnerability_status`, `missing_updates`, `vulnerabilities`.

The API may return nested records for some fields. These are **not** converted to stringified dictionaries or incorrectly interpreted as zero. Only safe scalar fields become Home Assistant sensor states. Source fields such as serial and user name are sensitive and optional/disabled by default.

## Counts and completeness

- `total_items` is authoritative where provided. A page containing one row with `total_items: 79` represents **79** items, not one.
- Missing/unavailable API reports produce unknown/unavailable values rather than a false zero.
- CVSS classification uses critical **≥9.0** and high **≥7.0 and <9.0**. Only explicit true `cisa_kev` markers are counted as known-exploited.
- Detailed vulnerability scans are limited to **1,000** records per organization per deep refresh. When the report exceeds this cap or pages are incomplete, detailed severity/KEV sensors remain unknown; the report total can still be displayed with **Partial** coverage.
- Action1 officially documents extended endpoint fields `missing_critical_updates` and `missing_other_updates` for `fields=*`. The corresponding per-endpoint sensors read those explicit, nonnegative integer counts whenever returned. Missing or nonnumeric values stay unknown.
- The sampled organization update catalog includes `classification`, `reboot_needed` and `update_type`, but no consistently verified `security_severity` field. **Organization-wide** critical/important patch count remains unknown. Never derive it from unrelated classifications.
- Two separate fields, `status` and `online_status`, are not interchangeable. Only explicitly known online/offline values drive the connectivity binary sensor.
- Cloud timestamps and online state can lag behind the endpoint. No SLA for real-time visibility is implied.

## Performance, privacy and polling

- One 5-minute coordinator discovers organizations, endpoints and up to five per-endpoint update totals.
- Organization, subscription, CVE, inventory and automation summaries refresh about every 30 minutes, starting on the second cycle.
- GET requests are paced by at least about **2.25 seconds** per configured API client, with rate-limit retry/backoff.
- Pagination uses explicit offsets and maximum record limits, never follows untrusted `next_page` URLs.
- Detailed reporting stores only privacy-safe aggregate totals and CVSS/KEV summaries, not audit descriptions, script bodies, software rows or raw CVE lists.
- Home Assistant recorder can persist entity states; protect dashboard access, diagnostics, backup files and configuration secrets.

## Live-validation boundary

The earlier sanitized diagnostics confirmed four accessible organizations, seven managed endpoints in two of them, CVE and patch catalog structures, audit totals and software/automation report schemas. They did **not** supply complete real payload values or validate the new version on a running Home Assistant installation. Real-tenant verification remains necessary before claiming complete device and subscription support.
