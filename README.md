# Action1 Monitor for Home Assistant

[![Validate](https://github.com/c-a-r-s-t-e-n/action1-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/c-a-r-s-t-e-n/action1-homeassistant/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/c-a-r-s-t-e-n/action1-homeassistant?include_prereleases&label=version)](https://github.com/c-a-r-s-t-e-n/action1-homeassistant/releases)
[![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%E2%89%A52025.1-blue)](https://www.home-assistant.io/)
[![HACS integration](https://img.shields.io/badge/HACS-custom%20integration-41BDF5)](https://hacs.xyz/)

**Independent, read-only Action1 cloud monitoring for Home Assistant.** Monitor managed Windows endpoints, update lists, vulnerabilities, inventory reporting, endpoint groups and automation activity using Action1's official REST API. No local network/VPN connection to the managed computers is required.

> **EXPERIMENTAL ALPHA — v0.1.0-alpha.2.** First live Home Assistant runtime validation is still required. Do **not** rely on this integration alone for security remediation, business-critical health checks or emergency alerts. Available report fields depend on Action1 permissions and tenant data.

## Installation using HACS

[![Open Action1 custom repository in Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=c-a-r-s-t-e-n&repository=action1-homeassistant&category=integration)

1. Install [HACS](https://hacs.xyz/) first, if needed.
2. Click the badge or select **HACS → Custom repositories → Add** and enter `https://github.com/c-a-r-s-t-e-n/action1-homeassistant` with category **Integration**.
3. Download the integration, selecting the **v0.1.0-alpha.2 pre-release** if HACS asks for a version.
4. **Restart Home Assistant** (reloading the integration alone is insufficient after Python code changes).
5. Select **Settings → Devices & services → Add integration → Action1 Monitor**.
6. Choose the correct Action1 region (for an EU account: **Europe**) and enter your own **Client ID** and **Client Secret**.

**Manual installation:** Copy only the `custom_components/action1_monitor` directory to `/config/custom_components/action1_monitor`, restart Home Assistant and add the integration through the UI.

**Requirements:** Home Assistant 2025.1+ is the declared target (backwards compatibility is not exhaustively verified); API access in Action1; outbound HTTPS to the selected Action1 region; dedicated API credentials with least-privilege read permissions where available.

## Tested API route coverage

Real anonymized diagnostic schema tests found **four organizations** (two populated), **seven managed endpoints** and **93 organization-level vulnerability entries** in a sampled tenant. These figures are diagnostic findings, **not sample data embedded in the integration**. API routes below were tested for successful read responses, but sensor runtime mapping is still alpha-quality.

| Domain | Relative GET API route | Integration use |
|---|---|---|
| Organizations | `/organizations` | Discover all accessible organizations |
| Managed endpoints | `/endpoints/managed/{orgId}?fields=*` | Discover devices, CPU/OS/agent/patch attributes |
| Endpoint missing updates | `/endpoints/managed/{orgId}/{endpointId}/missing-updates` | Count missing update records per device |
| Endpoint groups | `/endpoints/groups/{orgId}` | Group count |
| Vulnerabilities | `/vulnerabilities/{orgId}` | CVE counts, CVSS and CISA KEV when provided |
| Update catalog | `/updates/{orgId}` | Missing update catalog and counts |
| Installed software | `/installed-software/{orgId}/data` | Report row count; software product mapping not verified |
| Automation schedules | `/automations/schedules/{orgId}` | Count |
| Automation runs | `/automations/instances/{orgId}` | Count |
| Logs | `/logs/{orgId}` | Count |
| Deployers | `/endpoints/deployers/{orgId}` | Count |
| Software inventory errors | `/installed-software/{orgId}/errors` | Count |
| Endpoint status report | `/endpoints/status/{orgId}` | Cached for future scalar mapping |
| Organization usage | `/subscription/usage/organizations/{orgId}` | Collected; scalar sensors not mapped |
| Enterprise usage and subscription | `/subscription/usage/enterprise`, `/subscription/enterprise` | Collected; scalar sensors not mapped |
| Report catalog | `/reports/all` | Count |
| Audit log | `/audit/events` | Count |
| Script catalog | `/scripts/all` | Count (never execute scripts) |

**Read-only guarantee:** Only authentication uses POST to obtain an access token. The integration otherwise only makes GET requests. It never installs patches, reboots hosts, runs scripts, changes policies or executes automations.

## Home Assistant entities

Each managed endpoint is a device. The integration also creates one summary device per organization, plus a global Action1 Enterprise summary. **Entity IDs are generated by Home Assistant** from the device/label; verify them under **Developer tools → States** or **Settings → Devices & services** before using automations.

Example entity IDs (illustrative only): `binary_sensor.my_windows_pc_agent_connected`, `binary_sensor.my_windows_pc_reboot_required`, `sensor.my_windows_pc_missing_update_records`, `sensor.action1_my_organization_critical_cves_cvss_9`. User renames and conflicts can change the exact IDs. Internal unique identifiers use the Action1 organization and endpoint IDs.

| Endpoint entity | Source |
|---|---|
| Agent connected (binary sensor) | `online_status`, only known true/false values |
| Reboot required (binary sensor) | `reboot_required`, unknown if ambiguous |
| Last seen, Last boot, Agent install date | `last_seen`, `last_boot_time`, `agent_install_date` |
| Operating system, Platform | `OS`, `platform` |
| Agent version, Device name, Manufacturer | Inventory |
| CPU, CPU cores, Architecture, Memory | Inventory; structured values remain unknown |
| Online status, Agent status | `online_status`, `status` (not equivalent) |
| Update status, Vulnerability status | `update_status`, `vulnerability_status` |
| Missing update records | Per-device missing update listing |
| Missing critical updates, Missing other updates | **Unimplemented severity mapping:** remain unknown |
| Serial number, Last reported user, Comment | Inventory; diagnostic/private data |

**Organization summaries** include managed, online, offline and unknown-state endpoint counts; groups; known vulnerabilities; critical CVEs by CVSS 9+; explicitly flagged CISA KEV entries; update catalog; software report rows; automation instances/schedules; log entries and deployers.

**Enterprise summaries:** count of accessible organizations, report catalog entries, audit entries, script library entries.

Unknown values mean the API did not provide an applicable scalar or the field could not yet be interpreted. A missing metric is **not zero**. The CVE catalog can include multiple findings per endpoint; catalog counts and affected-device counts are not interchangeable.

## Polling, pagination and scale

- Organization and managed-endpoint inventory: every **5 minutes**.
- Optional deep queries (vulnerabilities, patches, software, automations, audits and catalog): initial refresh then every **six coordinator cycles**, approximately **30 minutes**.
- Per-endpoint missing update queries: rotate through up to **five endpoints per refresh**.
- GET calls are paced approximately **2.25 seconds apart** per configured Action1 client (around 27/minute).
- Results are paginated with capped request/record counts; extremely large organizations are not exhaustively covered by the first alpha. Home Assistant refresh duration increases with the number of organizations and available reports.

**Known scaling limitation:** The initial full deep refresh can take several minutes on larger tenants and will block initial integration setup until completed. This needs optimisation before stable release.

## Example: endpoint offline for ten minutes

Find the correct binary sensor ID in Home Assistant and replace the placeholders.

```yaml
alias: "Action1: Windows endpoint offline"
triggers:
  - trigger: state
    entity_id: binary_sensor.REPLACE_WITH_ENDPOINT_AGENT_CONNECTED
    to: "off"
    for: "00:10:00"
actions:
  - action: notify.mobile_app_REPLACE_WITH_YOUR_PHONE
    data:
      title: "Action1 endpoint offline"
      message: "Action1 has reported the endpoint as disconnected for 10 minutes."
mode: single
```

## Example: reboot required

```yaml
alias: "Action1: Windows reboot required"
triggers:
  - trigger: state
    entity_id: binary_sensor.REPLACE_WITH_ENDPOINT_REBOOT_REQUIRED
    to: "on"
    for: "00:30:00"
actions:
  - action: notify.mobile_app_REPLACE_WITH_YOUR_PHONE
    data:
      title: "Windows reboot required"
      message: "Action1 is reporting a pending reboot."
mode: single
```

These examples require enabling a Home Assistant notification destination. The API can report stale statuses; cross-check Action1 before operational decisions.

## Security and privacy

- API Client ID and Secret live in Home Assistant's private config entry storage. **Never include them in GitHub issues, logs or diagnostics.** Rotate exposed credentials immediately.
- HTTPS access is limited to a configured Action1 region; arbitrary user-provided API URLs are rejected.
- The Python API client spaces requests and backs off on rate limiting. It never logs tokens or API response bodies.
- Home Assistant Recorder and backups may retain endpoint names, installed software details and other inventory information. Protect dashboards, backups and configuration storage.
- The integration queries Action1 cloud data only. It does not send commands to managed endpoints.
- Do **not** upload original Action1 JSON response bodies, serial numbers, device names, user names, IP addresses, organization IDs or credentials to public issues. Report only sanitized field names and anonymous counts.

## Troubleshooting and limitations

- **Integration missing after HACS install:** restart Home Assistant fully and inspect **Settings → System → Logs**.
- **Authentication failure:** verify cloud region, API credential lifetime and permissions; Europe requires the European region.
- **No devices:** verify organization assignment and managed endpoint visibility in Action1; API access to an empty organization is not an error.
- **Unknown agent connectivity:** `online_status` may contain an API-specific value not yet tested. Never interpret ambiguous values as offline.
- **Missing update totals:** per-endpoint detail polling rotates; some devices initially have an unknown count.
- **Unknown update severity:** the `classification` property is present, but has not yet been calibrated with sanitized actual values.
- **Security and software counts:** may be incomplete on high-volume tenants due to record caps. Software report rows are not necessarily distinct installed programs.
- **HACS 'not validated':** community custom integrations are not officially supported by Home Assistant or Action1; review the Actions tab for exact CI results.

## Versioning, support and contributing

The public repository contains source code, documentation, tests, and build validation; **one-off PowerShell diagnostics remain outside GitHub** by design.

- [Releases](https://github.com/c-a-r-s-t-e-n/action1-homeassistant/releases)
- [Issues](https://github.com/c-a-r-s-t-e-n/action1-homeassistant/issues)
- [Changelog](CHANGELOG.md)
- [MIT license](LICENSE)
- [Official Action1 API documentation](https://app.action1.com/apidocs/)

## Disclaimer and trademarks

Independent community software; **not affiliated with, sponsored by or endorsed by Action1**. Product and company names remain the property of their respective owners. This integration is provided **without warranty**. Use Action1's official product to confirm patch/CVE remediation and operational state.

## License

Released under the [MIT License](LICENSE).

Copyright (c) 2026 c-a-r-s-t-e-n and contributors.
