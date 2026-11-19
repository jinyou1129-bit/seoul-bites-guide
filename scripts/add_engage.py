#!/usr/bin/env python3
"""Insert the stay-on-site blocks (Read next, prev/next, save button) into Bites pages.

python3 scripts/add_engage.py
Idempotent: the block between the engage markers is replaced on every run.
"""
from html import escape as esc
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# Reading order used for "Read next" and the prev/next links: slug -> (category label, filter key)
GUIDES = [
    ('seoul-must-eat-dishes-index.html', 'Must-Eat Index', 'street'),
    ('gwangjang-market-food-guide.html', 'Markets', 'market'),
    ('mangwon-market-food-guide.html', 'Markets', 'market'),
    ('majang-meat-market-hanwoo-guide.html', 'Markets', 'market'),
    ('myeongdong-street-food-guide.html', 'Street Food', 'street'),
    ('hongdae-late-night-food-guide.html', 'Street Food', 'street'),
    ('korean-convenience-store-snacks.html', 'Street Food', 'street'),
    ('han-river-chimaek-picnic-guide.html', 'Street Food', 'street'),
    ('myeongdong-korean-bbq-guide.html', 'K-BBQ', 'kbbq'),
    ('seongsu-cafe-and-bakeries-guide.html', 'Cafes', 'cafe'),
    ('insadong-traditional-tea-and-snacks.html', 'Tradition', 'tradition'),
    ('seoul-food-culture-and-etiquette-guide.html', 'Tradition', 'tradition'),
    ('seoul-halal-and-vegetarian-guide.html', 'Tradition', 'tradition'),
    ('food-tour-vs-cooking-class.html', 'Experiences', 'market'),
]
NON_GUIDE = {'index.html', 'about.html', 'advertise.html', 'contact.html', 'privacy.html',
             'seoul-cafe-hopping-seongsu-guide.html'}
START, END = '<!-- engage:start -->', '<!-- engage:end -->'


def text_of(html: str, pattern: str, default: str = '') -> str:
    m = re.search(pattern, html, re.S)
    return m.group(1).strip() if m else default


def short(text: str, limit: int = 96) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) <= limit else text[:limit - 1].rsplit(' ', 1)[0] + '…'


def main() -> None:
    pages = {}
    for slug, label, cat in GUIDES:
        path = ROOT / slug
        if not path.exists():
            continue
        html = path.read_text(encoding='utf-8')
        title = text_of(html, r'<title>(.*?)</title>')
        title = re.sub(r'\s*[|\-]\s*Seoul Bites Guide\s*$', '', title)
        desc = text_of(html, r'<meta name="description" content="([^"]*)"')
        pages[slug] = {'label': label, 'cat': cat, 'title': title, 'desc': desc}

    # any guide page added later (the daily generator) joins the rotation with a default label
    for path in sorted(ROOT.glob('*.html')):
        if path.name not in pages and path.name not in NON_GUIDE:
            html = path.read_text(encoding='utf-8')
            title = text_of(html, r'<title>(.*?)</title>')
            title = re.sub(r'\s*[|\-]\s*Seoul Bites Guide\s*$', '', title)
            pages[path.name] = {'label': 'Street Food', 'cat': 'street', 'title': title,
                                'desc': text_of(html, r'<meta name="description" content="([^"]*)"')}
            GUIDES.append((path.name, 'Street Food', 'street'))

    order = [slug for slug, _, _ in GUIDES if slug in pages]
    changed = 0

    for slug, html in ((s, (ROOT / s).read_text(encoding='utf-8')) for s in pages):
        page = pages[slug]
        body = html
        # drop a previous block
        body = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', body, flags=re.S)

        same = [s for s in order if s != slug and pages[s]['cat'] == page['cat']]
        other = [s for s in order if s != slug and pages[s]['cat'] != page['cat']]
        picks = (same + other)[:2] + (other or same)[:1]
        idx = order.index(slug)
        prev_slug = order[idx - 1] if idx > 0 else order[-1]
        next_slug = order[idx + 1] if idx + 1 < len(order) else order[0]

        items = ''.join(
            '<li><a href="./{slug}"><span class="rn-tag">{label}</span>'
            '<strong>{title}</strong><small>{desc}</small></a></li>'.format(
                slug=s, label=esc(pages[s]['label']), title=esc(pages[s]['title']),
                desc=esc(short(pages[s]['desc']))) for s in picks)

        block = ''.join([
            START,
            '<section class="read-next" id="read-next" aria-labelledby="read-next-title">'
            '<h2 id="read-next-title">Read next</h2>'
            '<p class="read-next-intro">Three guides that pick up where this one leaves off.</p>'
            f'<ul class="read-next-list">{items}</ul></section>'
            '<nav class="post-nav" aria-label="Guide navigation">'
            f'<a class="prev" href="./{prev_slug}"><small>Previous guide</small>'
            f'{esc(pages[prev_slug]["title"])}</a>'
            f'<a class="next" href="./{next_slug}"><small>Next guide</small>'
            f'{esc(pages[next_slug]["title"])}</a></nav>',
            END,
        ])

        if '</main>' not in body:
            print('no </main>, skipped', slug)
            continue
        body = body.replace('</main>', block + '</main>', 1)

        save_row = ('<div class="save-row">'
                    '<button class="save-btn" type="button" aria-pressed="false" '
                    f'data-save-href="./{slug}" data-save-title="{esc(page["title"], quote=True)}">'
                    '☆ Save this guide to my Seoul list</button>'
                    '<span class="save-note">Kept in this browser only.</span></div>')
        body = re.sub(r'<div class="save-row">.*?</div>', '', body, count=1, flags=re.S)
        h1 = re.search(r'</h1>', body)
        if h1:
            body = body[:h1.end()] + save_row + body[h1.end():]

        if body != html:
            (ROOT / slug).write_text(body, encoding='utf-8')
            changed += 1
    print(f'engage blocks written to {changed} guide pages')


if __name__ == '__main__':
    main()
