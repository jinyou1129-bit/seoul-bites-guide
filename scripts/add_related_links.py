#!/usr/bin/env python3
"""가이드 글마다 '관련 가이드' 내부 링크 블록을 넣는다 (멱등).

- 제목·슬러그 단어가 겹치는 글을 우선 연결하고, 모자라면 최신 글·전체 목록으로 채운다.
- 크롤 깊이와 주제 묶음(topic cluster)을 만들어 검색엔진이 모든 글을 찾게 하는 목적.

실행: python3 scripts/add_related_links.py
"""
from pathlib import Path
from html import escape as esc, unescape
import math
import re

ROOT = Path(__file__).resolve().parent.parent
MARK = '<!-- seo:related -->'
BLOCK_RE = re.compile(r'<!-- seo:related -->.*?</nav>\s*', re.S)
NON_ARTICLE = {'index.html', 'about.html', 'advertise.html', 'contact.html',
               'privacy.html', 'seoul-cafe-hopping-seongsu-guide.html'}
STOP = {'guide', 'seoul', 'korean', 'the', 'and', 'for', 'in', 'of', 'a', 'to', 'best',
        'what', 'how', 'your', 'you', 'with', 'at', 'on', 'vs', 'near', 'where', 'eat'}


def tokens(text):
    return {w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP and len(w) > 2}


def main():
    pages = [p for p in sorted(ROOT.glob('*.html')) if p.name not in NON_ARTICLE]
    info = {}
    for p in pages:
        s = p.read_text(encoding='utf-8')
        t = re.search(r'<title>(.*?)</title>', s, re.S)
        info[p.name] = {'title': (t.group(1).strip() if t else p.stem),
                        'tokens': tokens(p.stem + ' ' + (t.group(1) if t else ''))}
    changed = 0
    for p in pages:
        me = info[p.name]
        scores = []
        for name, meta in info.items():
            if name == p.name:
                continue
            overlap = len(me['tokens'] & meta['tokens'])
            scores.append((overlap, name))
        scores.sort(key=lambda x: (-x[0], x[1]))
        picks = [n for o, n in scores if o > 0][:4]
        if len(picks) < 3:
            picks += [n for o, n in scores if n not in picks][:3 - len(picks)]
        items = ''.join(
            f'<li><a href="./{n}">{esc(unescape(info[n]["title"]))}</a></li>' for n in picks[:4])
        block = (MARK + '<nav class="related-guides" aria-label="Related guides" '
                 'style="margin:2.2rem 0 0;padding:1.1rem 1.3rem;border:1px solid #ead9df;'
                 'border-radius:12px;background:#fffafb">'
                 '<h2 style="font-size:1.05rem;margin:0 0 .5rem">Related guides</h2>'
                 f'<ul style="margin:0;padding-left:1.2rem">{items}'
                 '<li><a href="./index.html#guides">All food guides</a></li></ul></nav>')
        html = p.read_text(encoding='utf-8')
        html = BLOCK_RE.sub('', html)
        if '</main>' not in html:
            continue
        new = html.replace('</main>', block + '</main>', 1)
        if new != html:
            p.write_text(new, encoding='utf-8')
            changed += 1
    print(f'related links written to {changed} pages')


if __name__ == '__main__':
    main()
