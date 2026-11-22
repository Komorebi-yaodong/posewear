"""Import public CC0 Shisei catalogs into PoseWear's build input."""
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

SITE = "https://shisei.indaloop.app"
MEDIA = "https://shisei-media.indaloop.app/images"
RAW = Path(os.environ.get("POSEWEAR_RAW", "assets-raw"))

# 原站目录 JSON、PoseWear 输入目录、原站媒体目录
LIBRARIES = (
    ("costumes", "dynasty", "costume/grey"),
    ("scenes", "scene", "scene/plain"),
    ("lights", "light", "light/plain"),
    ("props", "prop", "prop/grey"),
    ("furniture", "furn", "furniture/grey"),
)
VIEWS = {"front", "diag", "side", "back", "above", "below", "eye", "tq"}


def fetch(url):
    request = Request(url, headers={"User-Agent": "PoseWear-Shisei-Importer/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read()
        except OSError as error:
            if attempt == 2:
                raise RuntimeError(f"Download failed: {url}") from error
            time.sleep(2 ** attempt)


def download(job):
    url, path = job
    if path.is_file() and path.stat().st_size:
        return
    content = fetch(url)
    with Image.open(BytesIO(content)) as image:
        if image.format != "WEBP":
            raise ValueError(f"Expected WebP: {url}")
        image.verify()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def import_library(source, target, media_dir):
    catalog = json.loads(fetch(f"{SITE}/{source}.json"))
    if catalog["dir"] != media_dir:
        raise ValueError(f"{source}: upstream media directory changed")

    view_names = catalog["views"]
    if not view_names or not set(view_names) <= VIEWS:
        raise ValueError(f"{source}: unexpected view names: {view_names}")

    categories = {c["key"]: c["name"] for c in catalog["cats"]}
    retired = set(catalog.get("retired") or [])
    out, jobs = [], {}

    for item in catalog["items"]:
        if item["id"] in retired or item.get("r") != "general":
            continue
        if target == "dynasty" and item["cat"] != "HC":
            continue

        views = {}
        for view, filename in zip(view_names, item["v"], strict=True):
            if not filename:
                continue
            if not re.fullmatch(r"[A-Za-z0-9_-]+\.webp", filename):
                raise ValueError(f"Unexpected filename: {filename}")
            views[view] = filename

        if not views:
            continue

        name = item["n"]
        category = categories[item["cat"]]
        group = item.get("sub") or category
        extra = {}
        if target == "dynasty":
            extra = {
                "era": group["zh"],
                "eraEn": group["en"],
                "gender": item.get("g", "U"),
            }

        out.append({
            "id": item["id"],
            "cat": "历代服饰" if target == "dynasty" else category["zh"],
            "ti": name["zh"],
            "zh": name["zh"],
            "en": item.get("desc") or name["en"],
            "ja": name.get("ja", ""),
            "line": group["zh"],
            "lineEn": group["en"],
            "views": views,
            "extra": extra,
        })
        for filename in views.values():
            for tier in ("w300", "w900"):
                path = RAW / target / "files" / tier / filename
                jobs[path] = f"{MEDIA}/{media_dir}/{tier}/{filename}"

    if not out:
        raise RuntimeError(f"{source}: no entries imported")

    with ThreadPoolExecutor(max_workers=4) as pool:
        for _ in pool.map(download, ((url, path) for path, url in jobs.items())):
            pass

    output = RAW / target / "data.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"Shisei {target}: {len(out)} entries, {len(jobs)} images", flush=True)


if __name__ == "__main__":
    for library in LIBRARIES:
        import_library(*library)
