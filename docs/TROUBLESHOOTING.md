# Action1 Monitor troubleshooting

## Account connects but no endpoints appear

Check that **all relevant organizations** are accessible to your API client, rather than only the first organization. The integration discovers organizations independently. Confirm that the device appears under Action1 managed endpoints, and reload the Home Assistant integration if needed. Check whether API credentials have been revoked or organization permissions changed.

## Agent connected is unknown

The API may return a status not in the known online/offline values. Unknown is intentionally not shown as offline. Compare `online_status` in Action1's own console and provide only a **sanitized status example** without names, IDs or other device data when reporting a mapping issue.

## Missing updates are unknown

The integration rotates API requests across up to five endpoints per refresh. Large tenants need additional cycles to populate every device. The endpoint's `missing_updates` inventory field may also be structured rather than a scalar. Do not interpret unknown as patched/fully compliant.

## CVE count is available but severity counts are unknown

Inspect **CVE detail coverage**. If the report is larger than 1,000 rows or cannot be completely enumerated, the exact catalog total may still display, but severity and KEV summaries remain unknown. Counts refer to findings, not necessarily unique affected computers. Action1 remains the authoritative remediation system.

## License or enterprise metrics are unknown

Some subscription API data depends on the plan and permissions. Confirm actual values in Action1 and check the **Last detailed report** timestamp. The initial integration setup does not run the expensive report refresh immediately.

## Marketplace icon missing

Home Assistant 2026.3+ supports locally shipped `brand/` images, including the light/dark and Retina versions in this repository. The built-in Marketplace starts with 2026.11. Verify that the **installed tagged release** contains the `brand` files, restart Home Assistant, and allow the Marketplace image cache to update. Earlier HACS versions may load artwork from a different CDN.

## Diagnostic export

Open **Settings → Devices & services → Action1 Monitor → Download diagnostics** (wording depends on your Home Assistant version). The export includes counts, report categories, sync timestamps and generic failures; it intentionally omits access tokens, Client Secrets, names, IPs, endpoint identifiers, raw audit records and software lists.

For support, create an issue with Home Assistant version, integration version, selected region, error category and sanitized diagnostics. Do not upload raw API JSON or `/config/.storage` files.

## Safe rollback

Open Marketplace/HACS, select the last working version and restart Home Assistant. Preserve your integration entry to retain unique IDs, credentials and dashboard customizations. If the custom integration is completely removed, revoke unused API credentials in Action1.
