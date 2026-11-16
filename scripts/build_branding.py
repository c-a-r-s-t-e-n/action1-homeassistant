"""Generate original Action1 Monitor community branding assets.

Requires Pillow. Run: python scripts/build_branding.py
Brand artwork is independent and does not reproduce Action1's corporate logo.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "custom_components/action1_monitor/brand"
ASSETS = ROOT / "docs/assets"
BRAND.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

NAVY = (13, 28, 54)
BLUE = (39, 108, 184)
CYAN = (29, 207, 211)
ORANGE = (255, 164, 80)
WHITE = (248, 252, 255)
MUTED = (169, 194, 219)


def font(size, bold=False):
    names = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ) if bold else (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def emblem(size=512, dark=False):
    """Security shield + monitoring pulse + endpoint nodes, no borrowed marks."""
    scale = size / 512
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def pt(seq):
        return [(round(x * scale), round(y * scale)) for x, y in seq]
    def box(coords):
        return tuple(round(v * scale) for v in coords)
    color = WHITE if dark else NAVY
    outline = (120, 212, 233) if dark else BLUE
    shield = [(256, 35), (419, 98), (415, 275), (380, 359),
              (322, 425), (256, 470), (190, 425), (132, 359),
              (97, 275), (93, 98)]
    d.polygon(pt(shield), fill=outline)
    inner = [(256, 69), (390, 121), (385, 270), (355, 341),
             (303, 396), (256, 431), (209, 396), (157, 341),
             (127, 270), (122, 121)]
    d.polygon(pt(inner), fill=NAVY)
    # Pulse motif: availability and telemetry through a secured endpoint.
    line = [(147, 261), (201, 261), (227, 211),
            (260, 326), (290, 238), (315, 261), (366, 261)]
    d.line(pt(line), fill=CYAN, width=max(7, round(14*scale)), joint="curve")
    d.ellipse(box((186, 246, 215, 275)), fill=ORANGE)
    d.ellipse(box((301, 246, 330, 275)), fill=ORANGE)
    d.ellipse(box((245, 147, 267, 169)), fill=WHITE)
    d.line(pt([(256, 157), (256, 201)]), fill=WHITE, width=max(4,round(7*scale)))
    return im


def save_icon(name, size, dark):
    im = emblem(size, dark)
    im.save(BRAND / name, optimize=True)


def logo(size=(1000, 256), dark=False):
    w, h = size
    im = Image.new("RGBA", size, (0,0,0,0))
    mark = emblem(round(h * .84), dark)
    im.alpha_composite(mark, (0, (h-mark.height)//2))
    d = ImageDraw.Draw(im)
    x = round(h*0.95)
    primary = WHITE if dark else NAVY
    d.text((x, round(h*.16)), "ACTION1", font=font(round(h*.36), True), fill=primary)
    d.text((x+5, round(h*.58)), "MONITOR", font=font(round(h*.20), True), fill=CYAN if dark else BLUE)
    d.line([(x+4, round(h*.86)), (min(w-20,x+round(h*2.5)), round(h*.86))],
           fill=ORANGE, width=max(2,round(h*.012)))
    return im


def header():
    w,h = 1600,480
    im=Image.new("RGB",(w,h),NAVY)
    pix=im.load()
    for y in range(h):
        for x in range(w):
            k=x/w
            pix[x,y]=(round(NAVY[0]+7*k),round(NAVY[1]+18*k),round(NAVY[2]+29*k))
    d=ImageDraw.Draw(im)
    # Quiet network mesh accents on the right, not text behind the mark.
    positions=[(1070,115),(1220,70),(1400,140),(1120,290),(1310,340),(1480,295),(1510,75)]
    links=[(0,1),(0,3),(1,2),(1,4),(2,5),(3,4),(4,5),(2,6)]
    for a,b in links:
        d.line([positions[a],positions[b]], fill=(41,95,134), width=3)
    for i,(x,y) in enumerate(positions):
        color=CYAN if i%3==0 else ORANGE if i%4==0 else (55,138,177)
        d.ellipse((x-8,y-8,x+8,y+8),fill=color)
    icon=emblem(336, True)
    im.paste(icon,(72,68),icon)
    d.text((430,124),"ACTION1 MONITOR",font=font(69,True),fill=WHITE)
    d.text((437,225),"CLOUD ENDPOINT INTELLIGENCE",font=font(31,True),fill=CYAN)
    d.text((439,306),"Patch visibility  •  Vulnerabilities  •  Device health",font=font(21),fill=MUTED)
    d.rectangle((437,361,854,367),fill=ORANGE)
    im.save(ASSETS/"header.png",optimize=True)


for dark_prefix in ("", "dark_"):
    dark = bool(dark_prefix)
    save_icon(dark_prefix+"icon.png",256,dark)
    save_icon(dark_prefix+"icon@2x.png",512,dark)
    logo((1000,256),dark).save(BRAND/(dark_prefix+"logo.png"),optimize=True)
    logo((2000,512),dark).save(BRAND/(dark_prefix+"logo@2x.png"),optimize=True)
header()
print("Generated 8 integration brand assets and docs/assets/header.png")
