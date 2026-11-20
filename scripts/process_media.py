"""Turn downloaded Wikimedia photos into web images and the two looping background videos.
Usage: python3 scripts/process_media.py <raw_dir>
Reads the photo catalogue in data/photos.json, writes media/*.jpg, media/hero.mp4, media/what.mp4,
and marks which photos and videos now exist locally (photos without a local copy load from Wikimedia)."""
import json, os, subprocess, sys
from PIL import Image

RAW = sys.argv[1]
os.makedirs("media", exist_ok=True)
credits = json.load(open("data/photos.json"))


def save(img, path, width, q):
    im = img.copy()
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.convert("RGB").save(path, "JPEG", quality=q, optimize=True, progressive=True)


have = {}
for key in [k for k in credits if not k.startswith("_")]:
    src = os.path.join(RAW, key + ".jpg")
    if not os.path.exists(src):
        continue
    with Image.open(src) as im:
        save(im, f"media/{key}.jpg", 1280, 80)
        save(im, f"media/{key}-sm.jpg", 640, 76)
    have[key] = credits[key]


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an"]

def loop_zoom(src, out, crop, size, z=0.12, secs=28, ay=0.5):
    """Slow zoom in and back out with a cosine ease, so the loop point is seamless."""
    F = 25 * secs
    ffmpeg("-loop", "1", "-i", src, "-vf",
           f"{crop},scale=3840:-2,zoompan=z='1+{z}*(1-cos(2*PI*on/{F}))/2':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*{ay}':d={F}:s={size}:fps=25,setsar=1",
           "-frames:v", str(F), *ENC, out)


def loop_pan(src, out, secs=30):
    """Pan a 16:9 window across a wide photo and back, cosine-eased for a seamless loop."""
    w, h = Image.open(src).size
    cw = int(h * 16 / 9) // 2 * 2
    ffmpeg("-loop", "1", "-framerate", "25", "-t", str(secs), "-i", src, "-vf",
           f"crop={cw}:{h // 2 * 2}:x='({w}-{cw})*(1-cos(2*PI*t/{secs}))/2':y=0,scale=1280:-2,setsar=1", *ENC, out)


bridge, kokapet = os.path.join(RAW, "loc-raidurg.jpg"), os.path.join(RAW, "loc-kokapet.jpg")
if os.path.exists(bridge):
    loop_zoom(bridge, "media/hero.mp4", "crop=iw:iw*9/16:0:30", "1280x720", ay=0.3)
    ffmpeg("-i", "media/hero.mp4", "-frames:v", "1", "-q:v", "3", "media/hero-poster.jpg")
if os.path.exists(kokapet):
    loop_pan(kokapet, "media/what.mp4")
    ffmpeg("-i", "media/what.mp4", "-frames:v", "1", "-q:v", "3", "media/what-poster.jpg")

for key in credits:
    if not key.startswith("_"):
        credits[key]["local"] = os.path.exists(f"media/{key}.jpg")
credits["_videos"] = {"hero": os.path.exists("media/hero.mp4"), "what": os.path.exists("media/what.mp4")}
json.dump(credits, open("data/photos.json", "w"), indent=1)
sizes = {f: os.path.getsize("media/" + f) // 1024 for f in sorted(os.listdir("media"))}
print(json.dumps(sizes))
assert all(v < 15000 for v in sizes.values()), "a file is over the 15 MB artifact limit"
