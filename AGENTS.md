## Code Review Rules

### Preserve existing site behavior
Changes to one page or component must not unintentionally alter the layout, spacing, typography, navigation, metadata, or behavior of unrelated pages. Check shared CSS, layouts, includes, and JavaScript for regressions.

### Preserve content and editor compatibility
Do not break compatibility between the editor and the published site. Existing notes, memories, front matter, media embeds, drafts, slugs, and metadata must continue to load and publish correctly unless the change explicitly migrates them.

### Preserve URLs and metadata
Do not unintentionally change existing public URLs, canonical URLs, OGP metadata, sitemap behavior, or GitHub Pages paths. When a metadata or routing change is intentional, verify its effect across the whole site.
