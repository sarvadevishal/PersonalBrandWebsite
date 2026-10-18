# PersonalBrandWebsite

Personal brand website for Vishal Kumar Sarvade. Static HTML on Vercel at https://vishal-sarvade.vercel.app. Every push to `main` deploys automatically.

## Layout

| Path | What it is |
|---|---|
| `index.html` | Homepage: markup, styles and script. The `<style>` block is the design system for the whole site |
| `assets/vishal-headshot.jpg` | Headshot |
| `assets/Vishal-Kumar-Sarvade-Resume.pdf` | Resume behind every "Download resume" button |
| `assets/site.css` | Generated copy of the homepage styles, used by blog pages |
| `content/posts/*.json` | Blog posts, one file per post (source of truth) |
| `scripts/build_blog.py` | Builds the blog from `content/posts` |
| `blog/` | Generated: blog index, one page per post, RSS feed |
| `sitemap.xml` | Generated |
| `vercel.json` | Resume downloads as a file; asset caching |

## Adding a blog post

1. Create `content/posts/YYYY-MM-DD-your-slug.json`:

```json
{
  "slug": "your-slug",
  "date": "2026-10-19",
  "title": "Short, specific title",
  "summary": "One or two sentences that state the finding.",
  "tags": ["Governance"],
  "body": [
    "Paragraph one, citing a source like this [1].",
    "Paragraph two [2]."
  ],
  "sources": [
    {"title": "Source title", "publisher": "Publisher", "date": "2026-10-18", "url": "https://..."},
    {"title": "Source title", "publisher": "Publisher", "date": "2026-10-17", "url": "https://..."}
  ]
}
```

2. Run `python3 scripts/build_blog.py`. It refuses to build if a post breaks a rule: 150 to 450 words, 2 to 6 sources, every source cited with `[n]` and every `[n]` matching a source, no em dashes or double hyphens, no client names. Use `--check` to validate without writing.
3. Commit everything (the post file plus the regenerated `index.html`, `blog/`, `sitemap.xml`, `assets/site.css`) and push to `main`.

A scheduled task publishes one post a day at about 11 AM Pacific using these steps.

## Run locally

`python3 -m http.server 8000` in the repo root, then open http://localhost:8000. Blog pages use root-relative links, so opening files directly from disk will not load styles.
