# Performance

Guidelines for optimizing load times and runtime performance. Slow interfaces frustrate users and hurt engagement metrics. These rules focus on the most impactful performance optimizations.

## Image Optimization

- **Severity**: High
- **Platform**: All
- **Description**: Large, unoptimized images are the most common cause of slow page loads. Serving appropriately sized images in modern formats dramatically improves performance.
- **Do**: Use appropriate sizes and modern formats (WebP, AVIF) with `srcset` for responsive images.
- **Don't**: Serve unoptimized, full-resolution images.
- **Good Example**: `<img srcset="img-400.webp 400w, img-800.webp 800w" sizes="(max-width: 600px) 400px, 800px">`
- **Bad Example**: 4000px image displayed in a 400px container

## Lazy Loading

- **Severity**: Medium
- **Platform**: All
- **Description**: Loading all content upfront wastes bandwidth and slows the initial render. Below-fold content should load on demand.
- **Do**: Lazy load images and content below the fold.
- **Don't**: Load everything upfront, including off-screen content.
- **Good Example**: `loading="lazy"` on below-fold images
- **Bad Example**: All images set to eager load

## Code Splitting

- **Severity**: Medium
- **Platform**: Web
- **Description**: A single large JavaScript bundle delays initial page interaction. Splitting by route or feature reduces the initial payload.
- **Do**: Split code by route and feature using dynamic imports.
- **Don't**: Ship a single large bundle.
- **Good Example**: `const Page = lazy(() => import('./Page'))`
- **Bad Example**: All code in a single main bundle

## Caching

- **Severity**: Medium
- **Platform**: Web
- **Description**: Repeat visits should be fast. Proper caching prevents unnecessary network requests for unchanged resources.
- **Do**: Set appropriate `Cache-Control` headers for static assets.
- **Don't**: Serve every request from the origin with no caching strategy.
- **Good Example**: `Cache-Control: public, max-age=31536000, immutable` for hashed assets
- **Bad Example**: Every request hits the server without cache headers

## Font Loading

- **Severity**: Medium
- **Platform**: Web
- **Description**: Web fonts can block text rendering, showing invisible text (FOIT) until fonts download. Users should see text immediately.
- **Do**: Use `font-display: swap` or `font-display: optional`.
- **Don't**: Allow invisible text during font load.
- **Good Example**: `font-display: swap` with a similar system font fallback
- **Bad Example**: Flash of Invisible Text (FOIT) while font downloads

## Third Party Scripts

- **Severity**: Medium
- **Platform**: Web
- **Description**: External scripts loaded synchronously block rendering and delay interaction. Non-critical scripts should load without blocking.
- **Do**: Load non-critical third-party scripts with `async` or `defer`.
- **Don't**: Load third-party scripts synchronously in the `<head>`.
- **Good Example**: `<script src="analytics.js" async></script>`
- **Bad Example**: `<script src="analytics.js"></script>` in the head without async/defer

## Bundle Size

- **Severity**: Medium
- **Platform**: Web
- **Description**: Large JavaScript bundles slow down time-to-interactive. Bundle size should be monitored and minimized.
- **Do**: Monitor bundle size with a bundle analyzer and set size budgets.
- **Don't**: Ignore bundle size growth over time.
- **Good Example**: Bundle analyzer in CI with size limits
- **Bad Example**: No monitoring of bundle size

## Render Blocking

- **Severity**: Medium
- **Platform**: Web
- **Description**: Large CSS and JS files in the `<head>` block the first paint. Critical styles should be inlined, and non-critical resources deferred.
- **Do**: Inline critical CSS and defer non-critical stylesheets.
- **Don't**: Load all CSS in the head as blocking resources.
- **Good Example**: Critical CSS inlined + `<link rel="preload">` for the rest
- **Bad Example**: All stylesheets as render-blocking `<link>` tags in the head
