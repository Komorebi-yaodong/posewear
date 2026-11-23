#!/usr/bin/env python3
"""Prepare WaveSpeed expressions and public CharaDB hair for build.py."""
import json
import os
import re
import runpy
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

RAW = Path(os.environ.get('POSEWEAR_RAW', 'assets-raw'))
EMOTION = 'https://wavespeed.ai/free-tools/ai-emotion-gallery'
EMOTION_IMAGES = 'https://static.wavespeed.ai/media/images'
CHARADB = 'https://charadb-2fi.pages.dev'
ID = re.compile(r'[a-zA-Z0-9_-]+')
WEBP = re.compile(r'[a-zA-Z0-9_-]+\.webp')


def fetch(url):
    for attempt in range(3):
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (PoseWear asset importer)'})
            with urlopen(req, timeout=30) as response:
                return response.read()
        except OSError as error:
            if attempt == 2 or (isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504)):
                raise RuntimeError(f'Download failed: {url}: {error}') from error
            time.sleep(2 ** attempt)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def expression_rows(html, category):
    # Read the public gallery props as JSON rather than executing its scripts.
    chunks = (json.loads(m[1]) for m in re.finditer(
        r'self\.__next_f\.push\((\[.*?\])\)\s*</script>', html, re.S))
    payload = ''.join(v[1] for v in chunks if len(v) >= 2 and v[0] == 1 and isinstance(v[1], str))
    for m in re.finditer(r'"initial"\s*:\s*(?=\[)', payload):
        rows, _ = json.JSONDecoder().raw_decode(payload[m.end():])
        if rows and all(isinstance(row, dict) and row.get('category') == category and 'img' in row for row in rows):
            return rows
    raise ValueError(f'WaveSpeed: missing public data for {category}')


def fetch_expression_image(job):
    source, destination = job
    with Image.open(BytesIO(fetch(f'{EMOTION_IMAGES}/{source}'))) as im:
        if im.format != 'WEBP':
            raise ValueError(f'Unexpected image format: {source}')
        im.load()
        for tier, width in (('w300', 300), ('w900', 900)):
            folder = RAW / 'expression' / 'files' / tier
            folder.mkdir(parents=True, exist_ok=True)
            variant = im.copy()
            variant.thumbnail((width, width * 2))
            variant.save(folder / destination, 'WEBP', quality=86)


def import_expressions(labels):
    out, jobs, seen = [], [], set()
    for category, title in labels['EMO_ZH'].items():
        html = fetch(f'{EMOTION}/{category}').decode('utf-8')
        for row in expression_rows(html, category):
            iid = row['id']
            if not ID.fullmatch(iid) or iid in seen:
                raise ValueError(f'WaveSpeed: invalid or duplicate ID: {iid}')
            seen.add(iid)
            name = row['name']
            intensity = row['intensity']
            images = row['img']
            if not isinstance(images, list) or len(images) != 2 or not all(WEBP.fullmatch(i) for i in images):
                raise ValueError(f'WaveSpeed: expected two WebP views for {iid}')
            views = {'front': f'{iid}_front.webp', 'tq': f'{iid}_three-quarter.webp'}
            jobs.extend(zip(images, views.values(), strict=True))
            out.append({
                'id': iid, 'cat': title, 'line': title, 'lineEn': category,
                'ti': labels['NAME_ZH'].get(iid, name), 'zh': labels['DESC_ZH'].get(iid, name),
                'en': row.get('desc') or labels['DESC_EN_FILL'].get(iid, name), 'ja': '',
                'views': views,
                'extra': {'emo': title, 'emoEn': category, 'int': labels['INT_ZH'].get(intensity, intensity),
                          'intEn': intensity, 'code': row.get('code', '')},
            })
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch_expression_image, jobs))
    dump(RAW / 'expression' / 'data.json', out)
    print(f'WaveSpeed: {len(out)} expressions, {len(jobs)} source images', flush=True)


def import_hair(labels):
    js = fetch(f'{CHARADB}/data.js').decode('utf-8-sig')
    match = re.fullmatch(r'\s*window\.DB\s*=\s*(\{.*\})\s*;?\s*', js, re.S)
    if not match:
        raise ValueError('CharaDB: public catalog format changed')
    data = json.loads(match[1])
    if data['tier'] != 'public':
        raise ValueError('CharaDB: expected public catalog')
    items = [row for row in data['items'] if row.get('set') == 'hair' and row.get('tier') == 'public']
    children = defaultdict(list)
    for row in items:
        if not ID.fullmatch(row['id']):
            raise ValueError(f"CharaDB: invalid ID: {row['id']}")
        if row.get('sub') == 'style_color':
            children[row['parent']].append(row)

    def urls(iid):
        return {'t': f'{CHARADB}/thumb/{iid}.webp', 'i': f'{CHARADB}/img/{iid}.jpg', 'o': ''}

    out = []
    kinds = {'style': '发型', 'bangs': '刘海', 'color': '发色', 'acc': '发饰', 'eye': '瞳型'}
    for row in items:
        sub, iid = row.get('sub'), row['id']
        if sub not in kinds:
            continue
        cat = '瞳色' if sub == 'eye' and row.get('cat') == '目の色' else kinds[sub]
        name, tags = row['jp'], row['tags']
        entry = {'id': iid, 'cat': cat, 'ti': name, 'zh': name, 'ja': name,
                 'en': tags, 'kw': tags, 'no': iid, 'ext': 1, 'site': f'{CHARADB}/'}
        if sub == 'style':
            entry.update(line=cat, lineEn='hairstyle')
            angles = [{'zh': '默认', 'en': 'Default', **urls(iid)}]
            for variant in sorted(children[iid], key=lambda v: v['id']):
                color = variant['id'].rsplit('-', 1)[-1]
                zh = labels['COLOR_ZH'].get(color)
                angles.append({'zh': f'{zh}发' if zh else color, 'en': color, **urls(variant['id'])})
            entry['angles'] = angles
        else:
            entry.update(urls(iid), m=f'{CHARADB}/img/{iid}.jpg')
        out.append(entry)
    if not out:
        raise ValueError('CharaDB: no public hair entries')
    dump(RAW / 'charadb' / 'hair.json', out)
    print(f'CharaDB: {len(out)} public entries (metadata only; images stay at source)', flush=True)


if __name__ == '__main__':
    labels = runpy.run_path(str(Path(__file__).with_name('prep-modules.py')))
    import_hair(labels)
    import_expressions(labels)
