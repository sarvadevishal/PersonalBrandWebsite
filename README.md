# PersonalBrandWebsite

Personal brand website for Vishal Kumar Sarvade. Static HTML, no build step, deployed on Vercel.

| Path | What it is |
|---|---|
| `index.html` | The whole site: markup, styles and script |
| `assets/vishal-headshot.jpg` | Headshot in the hero |
| `assets/Vishal-Kumar-Sarvade-Resume.pdf` | Resume behind every "Download resume" button |
| `vercel.json` | Makes the resume download as a file instead of opening in a tab; caches the assets |

To update the resume, replace `assets/Vishal-Kumar-Sarvade-Resume.pdf` with a file of the same name and redeploy.

Vercel project settings: Framework Preset "Other", no build command, output directory left empty (the repo root).
