# Contributing

Pull requests and reproducible issue reports are welcome.

- Preserve **read-only** monitoring behavior. Changes that issue actions, scripts, deployments or reboot commands require explicit separate product review and must not be silently added.
- Do not add local test scripts, real tenant responses, API keys or device-specific information to the repository.
- Add unit tests for new response schemas, especially when treating null/unknown as offline or zero.
- Run `python -m compileall -q custom_components tests` and `python -m unittest discover -s tests -v` with `aiohttp` available.
- Prefer documented, paginated endpoints with bounded memory and conservative polling.
- Distinguish public report totals from sampled record counts.
- Document new entities and limitations in the README and CHANGELOG.
