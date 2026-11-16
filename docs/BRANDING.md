# Original Action1 Monitor community branding

The identity uses a shield, monitoring pulse and connected endpoint markers. It is a new community-designed visual language, **not** the corporate Action1 logo and not a claim of affiliation.

The dark navy, cyan and orange palette follows the clarity and contrast principles used in the author's Testo Smart Connect project without reusing the same mark.

## Asset inventory

| File | Dimensions | Usage |
|---|---:|---|
| `brand/icon.png`, `brand/dark_icon.png` | 256×256 | Integration and Marketplace icon |
| `brand/icon@2x.png`, `brand/dark_icon@2x.png` | 512×512 | High-DPI integration icon |
| `brand/logo.png`, `brand/dark_logo.png` | 1000×256 | Wide integration logo |
| `brand/logo@2x.png`, `brand/dark_logo@2x.png` | 2000×512 | High-DPI logo |
| `docs/assets/header.png` | 1600×480 | README and Marketplace presentation header |

Brand assets are transparent PNG files where appropriate; colors adapt to light/dark Home Assistant themes.

## Reproducibility

Run `python scripts/build_branding.py` with Pillow installed. GitHub's **Generate branding** workflow regenerates the artwork and checks its dimensions. Pillow is a **development dependency only**; Home Assistant does not need it.

On Home Assistant 2026.3+, local `brand/` assets are supported by installed custom integrations. Marketplace artwork from a new release may take time to populate the Marketplace brand image cache. Older standalone HACS versions may use their own image sources.

Licensing: Artwork is independently designed and included under the repository's MIT License. *Action1* is a trademark of its respective owner.
