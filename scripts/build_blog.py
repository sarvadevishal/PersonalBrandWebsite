#!/usr/bin/env python3
"""Build the blog for vishal-sarvade.vercel.app.

Reads content/posts/*.json and writes:
  blog/index.html            list of every post
  blog/<slug>/index.html     one page per post
  blog/feed.xml              RSS feed
  sitemap.xml                home, blog and every post
  assets/site.css            the <style> block from index.html, shared by blog pages
and refreshes the three latest posts on the homepage between
<!--BLOG:START--> and <!--BLOG:END--> in index.html.

Standard library only. Run from anywhere:  python3 scripts/build_blog.py
Use --check to validate posts without writing anything.
"""
import datetime as dt
import html
import json
import math
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://vishal-sarvade.vercel.app"
AUTHOR = "Vishal Kumar Sarvade"
BLOG_TITLE = "Field notes on AI agent adoption"
BLOG_DESC = ("One short note a day on how companies are putting AI agents to work, "
             "with every source linked.")
GENERATOR = '<meta name="generator" content="build_blog.py">'

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CITE_RE = re.compile(r"\[(\d+)\]")
# Voice rule: no em dashes, en dashes or double hyphens anywhere in post text.
DASH_RE = re.compile(r"—|–|--")
# Client confidentiality: these must never appear in a post.
BANNED_RE = re.compile(r"forever living|flp360|\bflp\b|titan data ?mart|\btdm\b", re.I)


class PostError(Exception):
    pass


def fail(name, msg):
    raise PostError(f"{name}: {msg}")


def load_posts():
    posts, seen_slugs, seen_titles = [], set(), set()
    for path in sorted(POSTS_DIR.glob("*.json")):
        name = path.name
        try:
            p = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(name, f"invalid JSON ({e})")
        for key in ("slug", "date", "title", "summary", "tags", "body", "sources"):
            if key not in p:
                fail(name, f"missing '{key}'")
        if not SLUG_RE.match(p["slug"]) or len(p["slug"]) > 80:
            fail(name, "slug must be lowercase words joined by single hyphens, max 80 chars")
        if not DATE_RE.match(p["date"]):
            fail(name, "date must be YYYY-MM-DD")
        try:
            dt.date.fromisoformat(p["date"])
        except ValueError:
            fail(name, "date is not a real calendar date")
        if name != f"{p['date']}-{p['slug']}.json":
            fail(name, f"filename must be {p['date']}-{p['slug']}.json")
        if p["slug"] in seen_slugs:
            fail(name, "duplicate slug")
        if p["title"].strip().lower() in seen_titles:
            fail(name, "duplicate title")
        if not (10 <= len(p["title"]) <= 90):
            fail(name, "title must be 10 to 90 characters")
        if not (40 <= len(p["summary"]) <= 280):
            fail(name, "summary must be 40 to 280 characters")
        if not (isinstance(p["tags"], list) and 1 <= len(p["tags"]) <= 4 and all(isinstance(t, str) and t for t in p["tags"])):
            fail(name, "tags must be a list of 1 to 4 strings")
        body = p["body"]
        if not (isinstance(body, list) and 2 <= len(body) <= 8 and all(isinstance(x, str) and x.strip() for x in body)):
            fail(name, "body must be a list of 2 to 8 non-empty paragraphs")
        words = sum(len(x.split()) for x in body)
        if not (150 <= words <= 450):
            fail(name, f"body is {words} words; keep it between 150 and 450")
        sources = p["sources"]
        if not (isinstance(sources, list) and 2 <= len(sources) <= 6):
            fail(name, "sources must list 2 to 6 entries")
        for i, s in enumerate(sources, 1):
            for key in ("title", "publisher", "url"):
                if not isinstance(s.get(key), str) or not s[key].strip():
                    fail(name, f"source {i} is missing '{key}'")
            if not s["url"].startswith("https://"):
                fail(name, f"source {i} url must start with https://")
            if "date" in s and s["date"] and not DATE_RE.match(s["date"]):
                fail(name, f"source {i} date must be YYYY-MM-DD")
        cited = {int(n) for x in body for n in CITE_RE.findall(x)}
        if not cited:
            fail(name, "body must cite sources with [1], [2] markers")
        bad = sorted(n for n in cited if n < 1 or n > len(sources))
        if bad:
            fail(name, f"citation markers {bad} have no matching source")
        unused = sorted(set(range(1, len(sources) + 1)) - cited)
        if unused:
            fail(name, f"sources {unused} are never cited in the body")
        texts = [p["title"], p["summary"], *p["tags"], *body] + [s["title"] for s in sources] + [s["publisher"] for s in sources]
        for t in texts:
            if DASH_RE.search(t):
                fail(name, f"remove em dashes, en dashes and double hyphens: {t[:60]!r}")
            if BANNED_RE.search(t):
                fail(name, f"confidential client name found: {t[:60]!r}")
        seen_slugs.add(p["slug"])
        seen_titles.add(p["title"].strip().lower())
        p["_words"] = words
        posts.append(p)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


# ---------- helpers ----------

def esc(s):
    return html.escape(s, quote=True)


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def read_minutes(p):
    return max(1, math.ceil(p["_words"] / 220))


def para_html(text):
    out = esc(text)
    return re.sub(r"\s*\[(\d+)\]", lambda m: f'<sup><a href="#src-{m.group(1)}" aria-label="Source {m.group(1)}">{m.group(1)}</a></sup>', out)


def tags_html(p):
    return '<div class="bl-tags">' + "".join(f"<span>{esc(t)}</span>" for t in p["tags"]) + "</div>"


def head_bits(index_html):
    icon = re.search(r'<link rel="icon"[^>]*>', index_html)
    fonts = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', index_html)
    return (icon.group(0) if icon else ""), (fonts.group(0) if fonts else "")


NAV_LINKS = [("/#work", "Work"), ("/#platform", "Platform"), ("/#ai", "AI"), ("/blog/", "Blog"),
             ("/#experience", "Experience"), ("/#writing", "Writing"), ("/#about", "About"), ("/#contact", "Contact")]


def nav_html():
    desk = "\n".join(
        f'      <a href="{h}"' + (' aria-current="true"' if t == "Blog" else "") + f">{t}</a>" for h, t in NAV_LINKS)
    mob = "".join(f'<a href="{h}">{t}</a>' for h, t in NAV_LINKS)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="/" aria-label="{AUTHOR}, home"><span class="mark" aria-hidden="true">VS</span>{AUTHOR}</a>
    <nav class="links" aria-label="Sections">
{desk}
    </nav>
    <button class="menu-btn" type="button" id="menuBtn" aria-expanded="false" aria-controls="mobileMenu" aria-label="Open menu">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </button>
  </div>
  <div class="wrap mobile-menu" id="mobileMenu" hidden>
    {mob}
  </div>
</header>'''


FOOTER = f'''<footer>
  <div class="wrap foot">
    <span>© {dt.date.today().year} {AUTHOR} · Building data platforms since 2014</span>
    <span><a href="/blog/feed.xml">RSS</a> · <a href="#top">Back to top</a></span>
  </div>
</footer>
<script>
(function(){{var b=document.getElementById('menuBtn'),m=document.getElementById('mobileMenu');
b.addEventListener('click',function(){{var o=m.hidden;m.hidden=!o;b.setAttribute('aria-expanded',String(o));b.setAttribute('aria-label',o?'Close menu':'Open menu');}});}})();
</script>'''


def page(title, description, canonical_path, body, icon, fonts, og_type="website", extra_head=""):
    url = SITE_URL + canonical_path
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="{AUTHOR}">
{GENERATOR}
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}/assets/vishal-headshot.jpg?v=2">
<meta name="theme-color" content="#F8F6F1">
{icon}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<link rel="stylesheet" href="/assets/site.css">
<link rel="alternate" type="application/rss+xml" title="{esc(BLOG_TITLE)}" href="/blog/feed.xml">
{extra_head}<style>body{{margin:0}}[hidden]{{display:none!important}}</style>
</head>
<body>
<span id="top"></span>
{nav_html()}
<main id="main">
{body}
</main>
{FOOTER}
</body>
</html>
'''




def relativize(text, prefix):
    """Turn root-relative links into relative ones ending in index.html, so pages
    work from a local folder (file://) as well as on Vercel."""
    def fix(m):
        attr, path = m.group(1), m.group(2)
        base, sep, frag = path.partition("#")
        if base == "" or base.endswith("/"):
            base += "index.html"
        return f'{attr}="{prefix}{base}{sep}{frag}"'
    return re.sub(r'(href|src)="/(?!/)([^"]*)"', fix, text)

# ---------- renderers ----------

def card_html(p):
    n = len(p["sources"])
    return f'''      <a class="bl-card" href="/blog/{p["slug"]}/">
        <div class="bl-meta"><time datetime="{p["date"]}">{nice_date(p["date"])}</time><span>{read_minutes(p)} min read</span><span>{n} sources</span></div>
        <h3>{esc(p["title"])}</h3>
        <p>{esc(p["summary"])}</p>
        {tags_html(p)}
        <span class="bl-more">Read the note →</span>
      </a>'''


def home_block(posts):
    if not posts:
        return '''    <div class="bl-empty">The first note lands soon. Each one covers a single development in AI agent adoption, with its sources linked.</div>'''
    return '    <div class="bl-grid">\n' + "\n".join(card_html(p) for p in posts[:3]) + "\n    </div>"


def index_page(posts, icon, fonts):
    if posts:
        rows = "\n".join(f'''      <article class="bl-row">
        <time datetime="{p["date"]}">{nice_date(p["date"])}</time>
        <div>
          <h2><a href="/blog/{p["slug"]}/">{esc(p["title"])}</a></h2>
          <p>{esc(p["summary"])}</p>
          <div class="bl-meta">{"".join(f"<span>{esc(t)}</span>" for t in p["tags"])}<span>{read_minutes(p)} min read</span><span>{len(p["sources"])} sources</span></div>
        </div>
      </article>''' for p in posts)
        listing = f'    <div class="bl-list">\n{rows}\n    </div>'
    else:
        listing = '    <div class="bl-empty">The first note lands soon.</div>'
    body = f'''<section class="page-head" aria-labelledby="blog-title">
  <div class="wrap">
    <div class="eyebrow">Blog</div>
    <h1 id="blog-title">{BLOG_TITLE}</h1>
    <p>{BLOG_DESC} Written for data and engineering leaders deciding where agents belong in their stack.</p>
    <div class="bl-foot" style="margin-top:18px"><a href="/blog/feed.xml">Subscribe with RSS</a><a href="/">About {AUTHOR}</a></div>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="wrap">
{listing}
  </div>
</section>'''
    return page(f"Blog · {AUTHOR}", BLOG_DESC, "/blog/", body, icon, fonts)


def post_page(p, newer, older, icon, fonts):
    srcs = "\n".join(
        f'''        <li id="src-{i}"><b>{esc(s["publisher"])}</b>{(" · " + nice_date(s["date"])) if s.get("date") else ""}<br><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></li>'''
        for i, s in enumerate(p["sources"], 1))
    paras = "\n".join(f"        <p>{para_html(x)}</p>" for x in p["body"])
    nav_bits = []
    if older:
        nav_bits.append(f'<a href="/blog/{older["slug"]}/">← {esc(older["title"])}</a>')
    else:
        nav_bits.append('<span></span>')
    if newer:
        nav_bits.append(f'<a href="/blog/{newer["slug"]}/">{esc(newer["title"])} →</a>')
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["summary"],
        "datePublished": p["date"], "dateModified": p["date"],
        "author": {"@type": "Person", "name": AUTHOR, "url": SITE_URL + "/"},
        "mainEntityOfPage": f"{SITE_URL}/blog/{p['slug']}/",
        "keywords": ", ".join(p["tags"]),
        "citation": [s["url"] for s in p["sources"]],
    }
    extra = f'<meta property="article:published_time" content="{p["date"]}">\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    body = f'''<section class="section" style="padding-top:56px">
  <div class="wrap">
    <article class="post">
      <div class="eyebrow"><a href="/blog/" style="color:inherit;text-decoration:none">Blog</a> · <time datetime="{p["date"]}">{nice_date(p["date"])}</time> · {read_minutes(p)} min read</div>
      <h1>{esc(p["title"])}</h1>
      <p class="dek">{esc(p["summary"])}</p>
      {tags_html(p)}
      <div class="post-body">
{paras}
      </div>
      <section class="sources" aria-labelledby="src-title">
        <div class="eyebrow" id="src-title">Sources</div>
        <ol>
{srcs}
        </ol>
      </section>
      <aside class="author" aria-label="About the author">
        <img src="/assets/vishal-headshot.jpg?v=2" width="64" height="64" alt="">
        <p><b>{AUTHOR}</b> is a Technical Architect in the San Francisco Bay Area with 12+ years building cloud data platforms on Amazon Redshift. <a href="/">More about him</a> · <a href="https://www.linkedin.com/in/vishalkumarsarvade/" target="_blank" rel="noopener">LinkedIn</a></p>
      </aside>
      <nav class="post-nav" aria-label="More posts">{"".join(nav_bits)}</nav>
      <div class="bl-foot"><a href="/blog/">All posts</a><a href="/blog/feed.xml">RSS feed</a></div>
    </article>
  </div>
</section>'''
    return page(f"{p['title']} · {AUTHOR}", p["summary"], f"/blog/{p['slug']}/", body, icon, fonts, "article", extra)


def rss(posts):
    items = []
    for p in posts[:30]:
        d = dt.datetime.fromisoformat(p["date"] + "T18:00:00+00:00")
        link = f"{SITE_URL}/blog/{p['slug']}/"
        items.append(f'''  <item>
    <title>{esc(p["title"])}</title>
    <link>{link}</link>
    <guid isPermaLink="true">{link}</guid>
    <pubDate>{d.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
    <description>{esc(p["summary"])}</description>
  </item>''')
    now = dt.datetime.now(dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(BLOG_TITLE)} · {AUTHOR}</title>
  <link>{SITE_URL}/blog/</link>
  <atom:link href="{SITE_URL}/blog/feed.xml" rel="self" type="application/rss+xml"/>
  <description>{esc(BLOG_DESC)}</description>
  <language>en-us</language>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
'''


def sitemap(posts):
    urls = [(SITE_URL + "/", posts[0]["date"] if posts else None), (SITE_URL + "/blog/", posts[0]["date"] if posts else None)]
    urls += [(f"{SITE_URL}/blog/{p['slug']}/", p["date"]) for p in posts]
    rows = "\n".join(f"  <url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


def main():
    check_only = "--check" in sys.argv
    try:
        posts = load_posts()
    except PostError as e:
        print(f"Build failed: {e}", file=sys.stderr)
        return 1
    if check_only:
        print(f"OK: {len(posts)} posts valid")
        return 0

    index_path = ROOT / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    style = re.search(r"<style>\n?(.*?)</style>", index_html, re.S)
    if not style:
        print("Build failed: no <style> block in index.html", file=sys.stderr)
        return 1
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "site.css").write_text(style.group(1), encoding="utf-8")

    start, end = "<!--BLOG:START-->", "<!--BLOG:END-->"
    if start not in index_html or end not in index_html:
        print("Build failed: BLOG markers missing from index.html", file=sys.stderr)
        return 1
    a, rest = index_html.split(start, 1)
    _, b = rest.split(end, 1)
    index_html = relativize(a + start + "\n" + home_block(posts) + "\n" + end + b, "")
    index_path.write_text(index_html, encoding="utf-8")

    icon, fonts = head_bits(index_html)
    BLOG_DIR.mkdir(exist_ok=True)
    live = {p["slug"] for p in posts}
    for d in BLOG_DIR.iterdir():
        if d.is_dir() and d.name not in live and (d / "index.html").exists() and GENERATOR in (d / "index.html").read_text(encoding="utf-8"):
            shutil.rmtree(d)
    (BLOG_DIR / "index.html").write_text(relativize(index_page(posts, icon, fonts), "../"), encoding="utf-8")
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        out = BLOG_DIR / p["slug"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(relativize(post_page(p, newer, older, icon, fonts), "../../"), encoding="utf-8")
    (BLOG_DIR / "feed.xml").write_text(rss(posts), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(posts), encoding="utf-8")
    print(f"Built {len(posts)} posts. Latest: {posts[0]['date']} {posts[0]['title']!r}" if posts else "Built 0 posts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
