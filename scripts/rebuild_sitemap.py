#!/usr/bin/env python3
"""sitemap.xml을 실제 HTML 페이지와 git 최종 수정일 기준으로 다시 만든다.

- 리다이렉트 스텁·404는 제외, index는 사이트 루트(/)로 표기
- 날짜가 없는 lastmod를 만들지 않고, 모든 URL에 YYYY-MM-DD lastmod를 넣는다

실행: python3 scripts/rebuild_sitemap.py
"""
from pathlib import Path
import subprocess
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://jinyou1129-bit.github.io/seoul-bites-guide/'
SKIP = {'seoul-cafe-hopping-seongsu-guide.html'}
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date().isoformat()


def lastmod(name):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', name],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        out = ''
    return out or TODAY


def main():
    pages = [p.name for p in sorted(ROOT.glob('*.html'))
             if p.name not in SKIP and not p.name.startswith('google')]
    pages.sort(key=lambda n: (n != 'index.html', n))
    rows = []
    for name in pages:
        loc = BASE if name == 'index.html' else BASE + name
        rows.append(f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod(name)}</lastmod>\n  </url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(rows) + '\n</urlset>\n')
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print(f'sitemap: {len(pages)} URLs')


if __name__ == '__main__':
    main()
