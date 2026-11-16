# Action1 Monitor v1.0.0

First stable-labelled release candidate of the independent, read-only Action1 Home Assistant integration.

## Highlights

- Original Marketplace branding: light/dark icons and logos, high-DPI variants and a visual header.
- Multi-organization endpoint discovery and dedicated devices with online status, reboot requirement, OS, CPU, missing critical update counts and other patch data.
- Organization vulnerability summaries with **exact report totals**, CVSS critical/high classifications, explicit CISA KEV flags and a coverage status that prevents partial reports from showing false confidence.
- Enterprise subscription/license/usage sensors, automation/group counts, software-report metadata and audit/script totals.
- Optimized API polling: bounded pages and request pacing, rotating per-device updates, postponed detailed reporting and no retention of raw script/audit bodies.
- Home Assistant privacy-safe downloadable diagnostics, conservative unknown/offline handling and disabled-by-default optional personal/hardware diagnostics.
- English and German setup, streamlined Marketplace-first README and dedicated API, branding and troubleshooting references.

## Upgrade and known boundaries

The previous `action1_monitor` integration domain and existing entity unique IDs remain unchanged. Install the update from Marketplace/HACS and restart Home Assistant; keep the existing configuration entry.

This integration does not install patches, run Action1 scripts or change endpoint configuration. Action1 cloud reports are delayed and tenant-dependent. Per-endpoint **missing critical/other update counts** use Action1's documented extended inventory fields when available. Organization-wide critical patch severity cannot be reliably derived from the sampled update catalog, so its sensor remains unknown. Large vulnerability reports display the catalog total but leave detailed severity breakdowns unknown when coverage is incomplete.

Automated Python regression tests, Ruff, Home Assistant hassfest, HACS validation and brand dimensions gate the stable release. Passing CI does not replace live account and Home Assistant compatibility verification.
