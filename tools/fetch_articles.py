"""Fetch openly licensed news articles (full text) into articles/*.json for the reader.
Runs on GitHub Actions. Standard library only."""
import json, re, html, sys, os, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = {'User-Agent': 'Mozilla/5.0 (HifzReader; +https://github.com/Ahmadhaj85/Hifz)'}
CONV = 'The Conversation (CC BY-ND 4.0)'
SOURCES = {
  # category: list of (feed url, source label)
  'world':       [('https://globalvoices.org/feed/', 'Global Voices (CC BY 3.0)'),
                  ('https://theconversation.com/global/articles.atom', CONV)],
  'politics':    [('https://theconversation.com/us/politics/articles.atom', CONV),
                  ('https://theconversation.com/uk/politics/articles.atom', CONV)],
  'business':    [('https://theconversation.com/us/business/articles.atom', CONV),
                  ('https://theconversation.com/uk/business/articles.atom', CONV)],
  'technology':  [('https://theconversation.com/us/technology/articles.atom', CONV),
                  ('https://theconversation.com/uk/technology/articles.atom', CONV)],
  'science':     [('https://theconversation.com/us/science/articles.atom', CONV),
                  ('https://theconversation.com/uk/science/articles.atom', CONV),
                  ('https://theconversation.com/us/health/articles.atom', CONV)],
  'environment': [('https://theconversation.com/us/environment/articles.atom', CONV),
                  ('https://theconversation.com/uk/environment/articles.atom', CONV)],
  'culture':     [('https://theconversation.com/us/arts/articles.atom', CONV),
                  ('https://theconversation.com/uk/arts/articles.atom', CONV)],
  'education':   [('https://theconversation.com/us/education/articles.atom', CONV)],
  'investigations': [('https://www.propublica.org/feeds/propublica/main', 'ProPublica (CC BY-NC-ND 3.0)')],
}
MAX = 25
NS = {'a': 'http://www.w3.org/2005/Atom', 'content': 'http://purl.org/rss/1.0/modules/content/'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

BLOCK = re.compile(r'<(p|h2|h3|li|blockquote)[^>]*>(.*?)</\1>', re.S | re.I)
def paras(content_html):
    out = []
    for _, inner in BLOCK.findall(content_html or ''):
        t = html.unescape(re.sub(r'<[^>]+>', '', inner))
        t = re.sub(r'\s+', ' ', t).strip()
        if len(t) > 25 and not t.lower().startswith(('read more', 'this article is republished')):
            out.append(t)
    return out

def text(el):
    return (el.text or '').strip() if el is not None else ''

def parse(data, label):
    root = ET.fromstring(data); items = []
    if root.tag.endswith('feed'):  # Atom
        for e in root.findall('a:entry', NS):
            link = e.find("a:link[@rel='alternate']", NS)
            if link is None: link = e.find('a:link', NS)
            c = e.find('a:content', NS)
            if c is None: c = e.find('a:summary', NS)
            author = e.find('a:author/a:name', NS)
            items.append(dict(title=html.unescape(text(e.find('a:title', NS))), url=link.get('href') if link is not None else '',
                              date=(text(e.find('a:published', NS)) or text(e.find('a:updated', NS)))[:10],
                              author=text(author), html=c.text if c is not None else ''))
    else:  # RSS 2.0
        for it in root.iter('item'):
            c = it.find('content:encoded', NS)
            d = text(it.find('pubDate'))
            try: d = datetime.strptime(d[:25].strip(), '%a, %d %b %Y %H:%M:%S').strftime('%Y-%m-%d')
            except Exception: d = d[:16]
            items.append(dict(title=html.unescape(text(it.find('title'))), url=text(it.find('link')), date=d,
                              author=text(it.find('{http://purl.org/dc/elements/1.1/}creator')),
                              html=(c.text if c is not None else text(it.find('description')))))
    out = []
    for it in items:
        ps = paras(it.pop('html'))
        if sum(len(p.split()) for p in ps) < 150:  # skip summaries / stubs
            continue
        it.update(src=label, paras=ps, words=sum(len(p.split()) for p in ps), id='f:' + it['url'])
        out.append(it)
    return out

report = {}
for cat, feeds in SOURCES.items():
    arts, seen = [], set()
    for url, label in feeds:
        try:
            got = parse(get(url), label); report[url] = len(got)
        except Exception as ex:
            got = []; report[url] = 'ERR ' + type(ex).__name__ + ': ' + str(ex)[:80]
        for a in got:
            if a['url'] not in seen: seen.add(a['url']); arts.append(a)
    arts.sort(key=lambda a: a['date'], reverse=True)
    path = f'articles/{cat}.json'
    if not arts and os.path.exists(path):
        continue  # keep the last good copy
    json.dump({'updated': datetime.now(timezone.utc).isoformat()[:16], 'articles': arts[:MAX]},
              open(path, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
json.dump(report, open('articles/_report.json', 'w'), indent=1)
print(json.dumps(report, indent=1))
