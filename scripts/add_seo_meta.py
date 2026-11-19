#!/usr/bin/env python3
"""Add Open Graph, Twitter Card and self-canonical tags to every page.

Run from anywhere: python3 scripts/add_seo_meta.py
Idempotent: re-running replaces the tags it wrote instead of duplicating them.
"""
from html import escape as esc
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://jinyou1129-bit.github.io/seoul-bites-guide/'
SITE = 'Seoul Bites Guide'

# Pages that are not guides (website) rather than articles.
NON_ARTICLE = {'index.html', 'about.html', 'advertise.html', 'contact.html', 'privacy.html'}

# Redirect stub: canonical points elsewhere and noindex is set by hand.
SKIP = {'seoul-cafe-hopping-seongsu-guide.html'}

# Unsplash images cropped to the 1200x630 sharing size (imgix parameters).
U = 'https://images.unsplash.com/{id}?auto=format&fit=crop&w=1200&h=630&q=80'
IMAGES = {
    'index.html': U.format(id='photo-1538485399081-7191377e8241'),          # Seoul street at night
    'about.html': U.format(id='photo-1546833999-b9f581a1996d'),             # Korean barbecue
    'advertise.html': U.format(id='photo-1546833999-b9f581a1996d'),
    'contact.html': U.format(id='photo-1546833999-b9f581a1996d'),
    'privacy.html': U.format(id='photo-1546833999-b9f581a1996d'),
    'food-tour-vs-cooking-class.html': U.format(id='photo-1590301157890-4810ed352733'),
    'gwangjang-market-food-guide.html': U.format(id='photo-1541696432-82c6da8ce7bf'),
    'han-river-chimaek-picnic-guide.html': U.format(id='photo-1612927601601-6638404737ce'),
    'hongdae-late-night-food-guide.html': U.format(id='photo-1517154421773-0529f29ea451'),
    'insadong-traditional-tea-and-snacks.html': U.format(id='photo-1576092768241-dec231879fc3'),
    'korean-convenience-store-snacks.html': U.format(id='photo-1612927601601-6638404737ce'),
    'majang-meat-market-hanwoo-guide.html': U.format(id='photo-1546833999-b9f581a1996d'),
    'mangwon-market-food-guide.html': U.format(id='photo-1553163147-622ab57be1c7'),
    'myeongdong-korean-bbq-guide.html': U.format(id='photo-1546833999-b9f581a1996d'),
    'myeongdong-street-food-guide.html': U.format(id='photo-1538485399081-7191377e8241'),
    'seongsu-cafe-and-bakeries-guide.html': U.format(id='photo-1554118811-1e0d58224f24'),
    'seoul-food-culture-and-etiquette-guide.html': U.format(id='photo-1590301157890-4810ed352733'),
    'seoul-halal-and-vegetarian-guide.html': U.format(id='photo-1590301157890-4810ed352733'),
    'seoul-must-eat-dishes-index.html': U.format(id='photo-1590301157890-4810ed352733'),
}
DEFAULT_IMAGE = U.format(id='photo-1538485399081-7191377e8241')

TITLE_FIX = {'index.html': 'Seoul Bites Guide — Honest Seoul Food Travel Guide'}

REMOVE = [
    re.compile(r'<link[^>]+rel="canonical"[^>]*>', re.I),
    re.compile(r'<meta[^>]+property="og:[^"]*"[^>]*>', re.I),
    re.compile(r'<meta[^>]+name="twitter:[^"]*"[^>]*>', re.I),
]


def build_block(name: str, title: str, description: str, image: str) -> str:
    url = BASE + ('' if name == 'index.html' else name)
    og_type = 'website' if name in NON_ARTICLE else 'article'
    canonical = BASE if name == 'index.html' else url
    lines = [
        f'<link rel="canonical" href="{esc(canonical, quote=True)}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{esc(SITE, quote=True)}">',
        f'<meta property="og:locale" content="en_US">',
        f'<meta property="og:title" content="{esc(title, quote=True)}">',
        f'<meta property="og:description" content="{esc(description, quote=True)}">',
        f'<meta property="og:url" content="{esc(url, quote=True)}">',
        f'<meta property="og:image" content="{esc(image, quote=True)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{esc(title, quote=True)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title, quote=True)}">',
        f'<meta name="twitter:description" content="{esc(description, quote=True)}">',
        f'<meta name="twitter:image" content="{esc(image, quote=True)}">',
    ]
    return ''.join(lines)


def main() -> None:
    changed = 0
    for path in sorted(ROOT.glob('*.html')):
        name = path.name
        if name in SKIP:
            continue
        html = path.read_text(encoding='utf-8')
        head_end = html.find('</head>')
        if head_end == -1:
            print('no </head>, skipped:', name)
            continue
        head, rest = html[:head_end], html[head_end:]

        if name in TITLE_FIX:
            head = re.sub(r'<title>.*?</title>', '<title>' + TITLE_FIX[name] + '</title>', head, count=1, flags=re.S)

        title_m = re.search(r'<title>(.*?)</title>', head, re.S)
        title = title_m.group(1).strip() if title_m else SITE
        desc_m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', head, re.I)
        if not desc_m:
            desc_m = re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', head, re.I)
        if not desc_m:
            print('no description, skipped:', name)
            continue
        description = desc_m.group(1).strip()

        for pattern in REMOVE:
            head = pattern.sub('', head)
        block = build_block(name, title, description, IMAGES.get(name, DEFAULT_IMAGE))
        head = head.rstrip() + block
        new_html = head + rest
        if new_html != html:
            path.write_text(new_html, encoding='utf-8')
            changed += 1
    print(f'seo meta written to {changed} pages')


if __name__ == '__main__':
    main()
