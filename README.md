# PersonalBrandWebsite

Personal brand website for Vishal Kumar Sarvade. Static HTML on Vercel at https://www.vishalkumarsarvade.com. Every push to `main` deploys automatically.

## Layout

| Path | What it is |
|---|---|
| `index.html` | Homepage markup and its page-only script. Its `<head>` holds the theme and font loader that the build copies into every other page |
| `assets/site.css` | The one stylesheet for every page: design system, three themes, and the mobile and robustness layer at the end. Edit it directly |
| `assets/theme.js` | Shared script: theme picker, mobile menu, back-to-top, blog search |
| `assets/vishal-headshot*.{jpg,webp}`, `assets/vishal-sf*.{jpg,webp}` | Photos in 480 and 800 pixel widths |
| `assets/og-card.png`, `favicon.ico`, `apple-touch-icon.png`, `assets/icon-*.png`, `site.webmanifest` | Social preview card and icons |
| `assets/Vishal-Kumar-Sarvade-Resume.pdf` | Resume behind every "Download resume" button |
| `content/posts/*.json` | Blog posts, one file per post (source of truth) |
| `scripts/build_blog.py` | Builds the blog from `content/posts` |
| `blog/` | Generated: blog index, one page per post, RSS feed |
| `sitemap.xml`, `robots.txt`, `404.html` | Generated |
| `vercel.json` | Security headers, one-year caching for versioned assets, resume downloads as a file |

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
3. Commit everything (the post file plus the regenerated `index.html`, `blog/`, `sitemap.xml`, `robots.txt`, `404.html`) and push to `main`.

A scheduled task publishes one post a day at about 11 AM Pacific using these steps.

## Run locally

`python3 -m http.server 8000` in the repo root, then open http://localhost:8000. Every page uses root-relative links, so opening files directly from disk will not load styles.

## Changing styles or scripts

Edit `assets/site.css` or `assets/theme.js`, then run `python3 scripts/build_blog.py`. The build stamps a content hash into the `?v=` on both files in every page, which is what lets Vercel cache them for a year. Skipping the build after a style change leaves visitors on the old cached file.

If a photo changes, regenerate its 480 and 800 pixel versions and bump its `?v=` in `index.html` and `scripts/build_blog.py`.

The domain lives in `SITE_URL` at the top of `scripts/build_blog.py` and in the canonical and Open Graph tags in the `index.html` head.
