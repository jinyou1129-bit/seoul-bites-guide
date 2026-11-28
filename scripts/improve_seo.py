#!/usr/bin/env python3
"""Seoul Bites 전 페이지 검색 노출 보강 (멱등).

  1) 이미지 <img>에 width/height·loading/decoding 기본값 부여 (CLS·LCP)
  2) 홈 ItemList를 실제 가이드 카드 전체로 갱신
  3) 푸터에 패밀리 사이트(Seoul Glow·스타핏픽) 링크 추가
  4) <head>에 RSS 발견 링크 추가
  5) 65자를 넘는 <title>을 60자 안쪽으로 줄인다(수식어 뒤에서 자름)

실행: python3 scripts/improve_seo.py
"""
from pathlib import Path
from html import escape as esc, unescape
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://jinyou1129-bit.github.io/seoul-bites-guide/'
SKIP = {'seoul-cafe-hopping-seongsu-guide.html'}
MARK_IL = '<!-- seo:itemlist -->'
MARK_FAM = '<!-- seo:family -->'
FAMILY = (MARK_FAM +
          '<div class="family-links">More from us: '
          '<a href="https://jinyou1129-bit.github.io/seoul-glow-guide/">Seoul Glow — K-beauty &amp; Olive Young guide</a> · '
          '<a href="https://starfitpick.netlify.app/">Star Fit Pick — K-celebrity outfit lookbook (Korean)</a></div>')
FAMILY_RE = re.compile(r'<!-- seo:family -->.*?</div>', re.S)
IL_RE = re.compile(r'<!-- seo:itemlist -->\s*<script type="application/ld\+json">.*?</script>\s*', re.S)

TITLE_MAX = 60
TITLE_OVERRIDE = {
    'majang-meat-market-hanwoo-guide.html': 'Majang Meat Market Hanwoo Guide: Half-Price Beef Cuts',
    'myeongdong-kbbq-pork-belly-hanwoo.html': 'Myeongdong K-BBQ Guide: Pork Belly & Hanwoo Ordering',
    'seongsu-cafe-and-bakeries-guide.html': 'Seongsu-dong Cafe & Bakery Guide for Seoul Visitors',
    'seoul-chimaek-chicken-beer-combos.html': 'Chimaek Culture: Korean Fried Chicken & Beer Combos',
    'myeongdong-korean-bbq-guide.html': 'Myeongdong Korean BBQ Guide: Ordering Pork Belly',
    'seoul-must-eat-dishes-index.html': '15 Must-Eat Seoul Dishes: Prices & Spice Levels',
}
NON_ARTICLE = {'index.html', 'about.html', 'advertise.html', 'contact.html', 'privacy.html'}


def short_title(t):
    t = re.sub(r'\s*[|—–-]\s*Seoul Bites Guide\s*$', '', t).strip()
    if len(t) <= TITLE_MAX or len(t) < 28:
        return t
    best = None
    for sep in (': ', ' — ', ' – ', ' | ', ' - ', ' ('):
        i = t.rfind(sep, 0, TITLE_MAX + 1)
        if i >= 28:
            best = t[:i].rstrip(' ,;:·—–-')
            break
    if not best or len(best) < 28:
        return t
    return best


def fix_images(html):
    def repl(m):
        tag = m.group(0)
        add = ''
        if 'width=' not in tag and 'height=' not in tag:
            if 'food-image' in tag:
                add += ' width="600" height="400"'
            else:
                add += ' width="1200" height="800"'
        if 'loading=' not in tag and 'food-image' not in tag:
            add += ' loading="lazy"'
        if 'decoding=' not in tag:
            add += ' decoding="async"'
        if not add:
            return tag
        return tag[:-1].rstrip() + add + '>'
    return re.sub(r'<img\b[^>]*>', repl, html)


def item_list(name, html):
    """홈의 기존 WebSite+ItemList 그래프를 WebSite+최신 ItemList로 교체한다."""
    if name != 'index.html':
        return html
    names = {}
    for m in re.finditer(r'<h3><a class="card-link" href="\./([a-z0-9-]+\.html)">(.*?)</a></h3>', html, re.S):
        names[m.group(1)] = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    if not names:
        return html
    ld = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebSite', 'name': 'Seoul Bites Guide', 'url': BASE, '@id': BASE + '#website'},
            {
                '@type': 'ItemList',
                '@id': BASE + '#guides',
                'name': 'Seoul food & drink guides',
                'numberOfItems': len(names),
                'itemListOrder': 'https://schema.org/ItemListOrderAscending',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'name': n, 'url': BASE + h}
                    for i, (h, n) in enumerate(names.items())
                ],
            },
        ],
    }
    block = MARK_IL + '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    # 기존 홈 그래프(WebSite+ItemList)만 교체하고 FAQPage 등 다른 블록은 그대로 둔다.
    def repl(m):
        try:
            j = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        txt = json.dumps(j, ensure_ascii=False)
        if '"WebSite"' in txt and '"ItemList"' in txt:
            return block
        return m.group(0)
    html = IL_RE.sub('', html)
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, html, count=1, flags=re.S)


def family(html):
    if 'seoul-glow-guide' in html:
        return FAMILY_RE.sub(FAMILY, html)
    m = re.search(r'(<footer>.*?)(<div class="disclaimer">|<div class="photo-credits">)', html, re.S)
    if not m:
        return html
    return html[:m.end(1)] + FAMILY + html[m.end(1):]


def rss_link(html):
    if 'application/rss+xml' in html:
        return html
    tag = ('<link rel="alternate" type="application/rss+xml" title="Seoul Bites Guide RSS" '
           f'href="{BASE}rss.xml">')
    return html.replace('</head>', tag + '</head>', 1)


def title_shorten(html, name):
    if name in NON_ARTICLE:
        return html, None
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    if not m:
        return html, None
    old = unescape(m.group(1))
    new = TITLE_OVERRIDE.get(name) or short_title(old)
    if new == old:
        return html, None
    html = html[:m.start(1)] + esc(new, quote=False) + html[m.end(1):]
    html = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda mm: mm.group(1) + esc(new, quote=True) + mm.group(2), html, count=1)
    html = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")', lambda mm: mm.group(1) + esc(new, quote=True) + mm.group(2), html, count=1)
    return html, (old, new)


def main():
    changed, retitled = 0, []
    for path in sorted(ROOT.glob('*.html')):
        name = path.name
        if name in SKIP:
            continue
        html = orig = path.read_text(encoding='utf-8')
        html = fix_images(html)
        html = item_list(name, html)
        html = family(html)
        html = rss_link(html)
        html, t = title_shorten(html, name)
        if t:
            retitled.append((name, len(t[0]), len(t[1]), t[1]))
        if html != orig:
            path.write_text(html, encoding='utf-8')
            changed += 1
    print(f'updated {changed} pages')
    for r in retitled:
        print('title:', r[0], r[1], '->', r[2], '|', r[3])


if __name__ == '__main__':
    sys.exit(main())
