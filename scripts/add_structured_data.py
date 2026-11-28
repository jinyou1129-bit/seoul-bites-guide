#!/usr/bin/env python3
"""Article · BreadcrumbList 구조화 데이터를 전 페이지에 붙인다 (멱등).

- 이미 넣은 블록은 마커 주석(<!-- seo:jsonld -->)으로 찾아 교체한다.
- datePublished는 파일이 처음 커밋된 날, dateModified는 마지막 커밋 날(미커밋이면 오늘).
- 새 글이 생성될 때 scripts/generate_post.py가 apply_file()로 호출한다.

실행: python3 scripts/add_structured_data.py
"""
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://jinyou1129-bit.github.io/seoul-bites-guide/'
SITE = 'Seoul Bites Guide'
KST = timezone(timedelta(hours=9))

MARK = '<!-- seo:jsonld -->'
BLOCK_RE = re.compile(r'<!-- seo:jsonld -->\s*<script type="application/ld\+json">.*?</script>\s*', re.S)

# 가이드가 아닌 페이지: Article 없이 BreadcrumbList만 넣는다.
NON_ARTICLE = {'index.html', 'about.html', 'advertise.html', 'contact.html', 'privacy.html'}
# 리다이렉트 스텁
SKIP = {'seoul-cafe-hopping-seongsu-guide.html'}
SECTION = {
    'about.html': 'About',
    'advertise.html': 'Advertise',
    'contact.html': 'Contact',
    'privacy.html': 'Privacy',
}


def git_date(name, first=False):
    args = ['git', 'log', '-1', '--format=%cs']
    if first:
        args += ['--diff-filter=A', '--follow']
    args += ['--', name]
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        out = ''
    return out or datetime.now(KST).date().isoformat()


def url_for(name):
    return BASE if name == 'index.html' else BASE + name


def faq_entities(html):
    """본문에 실제로 보이는 FAQ(질문/답)를 FAQPage 엔티티로 바꾼다."""
    body = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    pairs = re.findall(
        r'<div class="faq-q">(.*?)</div>\s*<div class="faq-a">(.*?)</div>', body, re.S)
    if not pairs:
        pairs = re.findall(
            r'<details><summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>', body, re.S)
    out = []
    for q, a in pairs[:6]:
        q = re.sub(r'<[^>]+>', '', unescape(q)).strip()
        a = re.sub(r'<[^>]+>', '', unescape(a)).strip()
        if q and a:
            out.append({'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}})
    return out


def build(name, title, description, image, faq=None):
    url = url_for(name)
    graph = []
    if name not in NON_ARTICLE:
        graph.append({
            '@type': 'Article',
            '@id': url + '#article',
            'headline': title,
            'description': description,
            **({'image': [image]} if image else {}),
            'datePublished': git_date(name, first=True) + 'T09:00:00+09:00',
            'dateModified': git_date(name) + 'T09:00:00+09:00',
            'inLanguage': 'en',
            'author': {'@type': 'Organization', 'name': SITE, 'url': BASE},
            'publisher': {'@type': 'Organization', 'name': SITE, 'url': BASE},
            'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
            'isPartOf': {'@type': 'WebSite', '@id': BASE + '#website', 'name': SITE, 'url': BASE},
            'articleSection': 'Seoul food guides',
        })
    trail = [('Home', BASE)]
    if name not in NON_ARTICLE:
        trail.append(('Food guides', BASE + 'index.html#guides'))
    if name != 'index.html':
        trail.append((title, url))
    if len(trail) > 1:
        graph.append({
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                for i, (n, u) in enumerate(trail)
            ],
        })
    if faq:
        graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': faq,
                      'isPartOf': {'@type': 'WebPage', '@id': url}})
    if not graph:
        return ''
    return MARK + '<script type="application/ld+json">' + json.dumps(
        {'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False) + '</script>\n'


def apply(html, name):
    head_end = html.find('</head>')
    if head_end == -1:
        return html
    head, rest = html[:head_end], html[head_end:]
    title_m = re.search(r'<title>(.*?)</title>', head, re.S)
    title = unescape(title_m.group(1).strip()) if title_m else SITE
    desc_m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', head, re.I)
    if not desc_m:
        desc_m = re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', head, re.I)
    description = unescape(desc_m.group(1).strip()) if desc_m else ''
    img_m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', head, re.I)
    image = unescape(img_m.group(1)) if img_m else ''
    head = BLOCK_RE.sub('', head)
    if not description:
        return head + rest
    faq = None if 'FAQPage' in html else faq_entities(html)
    head = head.rstrip() + '\n' + build(name, title, description, image, faq)
    return head + rest


def apply_file(path):
    path = Path(path)
    rel = path.relative_to(ROOT).as_posix()
    if rel.split('/')[-1] in SKIP:
        return False
    html = path.read_text(encoding='utf-8')
    new = apply(html, rel)
    if new != html:
        path.write_text(new, encoding='utf-8')
        return True
    return False


def main():
    changed = 0
    for path in sorted(ROOT.glob('*.html')):
        changed += bool(apply_file(path))
    print(f'structured data written to {changed} pages')


if __name__ == '__main__':
    main()
