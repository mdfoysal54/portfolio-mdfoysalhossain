# Md. Foysal Hossain — Futuristic Portfolio

A production-oriented, responsive personal portfolio built with **plain HTML, CSS and JavaScript**. No framework, package manager, build step, canvas, WebGL, icon library or external font request is required.

## Why this version is fast
- No runtime dependencies or framework bundle.
- No continuous WebGL / Three.js rendering.
- CSS-only 3D hero geometry, orbit animation and project visuals.
- IntersectionObserver reveals only as content enters the viewport.
- Pointer glow and tilt automatically disable for touch, reduced-motion and data-saver users.
- Profile image uses native lazy loading + async decoding.
- System font stack avoids extra font downloads.
- Accessible fallbacks work when JavaScript is disabled.

## Structure
```text
foysal-portfolio/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── script.js
├── assets/
│   ├── profile-placeholder.svg
│   ├── favicon.svg
│   └── og-cover.svg
├── robots.txt
├── sitemap.xml
├── site.webmanifest
└── README.md
```

## Replace the profile photo
1. Export a professional portrait as **WebP**, ideally around **720 × 860 px** and under ~200 KB.
2. Save it as `assets/profile-photo.webp`.
3. In `index.html`, find `data-profile-image` and change:
   `src="assets/profile-placeholder.svg"`
   to:
   `src="assets/profile-photo.webp"`
4. Change the `alt` text to a short description such as `Portrait of Md. Foysal Hossain`.

## Update your content
Most personal content lives directly in `index.html`. Search for:
- `Md. Foysal Hossain`
- `faisalhasan494@gmail.com`
- `mdfoysal54`
- `Stamford University Bangladesh`
- Project titles and descriptions

Before publishing, verify all dates, descriptions, contact details and links are current.

## Contact form
The form intentionally has **no backend dependency**. On submit it validates fields and opens the visitor's email app with a pre-filled message to your email address. This is private, lightweight, and works on static hosting.

For direct in-page submissions later, connect a service such as Formspree or Netlify Forms and replace the submit handler in `js/script.js`.

## Run locally
### Simple option
Open `index.html` in your browser.

### Recommended local server
From this directory:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000`.

## Deploy
### GitHub Pages
1. Push this folder to a GitHub repository.
2. Repository **Settings → Pages**.
3. Deploy from your `main` branch, root folder.

### Netlify
Drag this entire folder into Netlify Drop or connect the Git repository.

### Vercel
Import the Git repository. No build command is required; serve the repository root as a static site.

## SEO checklist before going live
1. Replace `https://example.com/` in `sitemap.xml` with the real domain.
2. Add your canonical URL inside `<head>`:
   `<link rel="canonical" href="https://your-domain.com/">`
3. When you know the final domain, make `og:image` an absolute URL for best social sharing compatibility.
4. Add real project URLs where available.
5. Submit the sitemap in Google Search Console after deployment.

## Performance checklist
- Keep your profile photo under ~200 KB when possible.
- Use WebP/AVIF for any future project screenshots and set explicit width/height.
- Avoid autoplay video and huge background images.
- Keep third-party analytics/scripts to a minimum.
- Test production hosting with Lighthouse; caching/compression is handled by most modern static hosts automatically.

## Customization
Primary colors, surfaces, typography and sizing are CSS variables at the top of `css/style.css` under `:root`. The design is intentionally modular so you can change accents without hunting through the whole stylesheet.
