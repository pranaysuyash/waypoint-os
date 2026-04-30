# Blog Content Architecture — Cloudflare R2 JSON Dump

**Date**: 2026-04-30
**Context**: 200+ research docs in travel_agency_agent/Docs/ can be repurposed as blog content
**Storage**: Cloudflare R2 (or S3) — cheap, no DB, no CMS

---

## 1. Architecture

```
DOCS/ (source of truth)
  ↓ (curate + convert to markdown)
Blog posts as Markdown files
  ↓ (build script)
JSON dump → Cloudflare R2
  ↓ (fetch at build or request time)
Next.js frontend (blogs pages)
```

### Why R2 over a database

| Factor | R2/S3 | Database | CMS |
|--------|-------|----------|-----|
| Cost | ~$0.015/GB/mo | $15-50/mo | $20-99/mo |
| Setup | 1 API call | Schema + migrations | Integration work |
| Speed | CDN-cached | Network round-trip | Depends |
| Content editing | Add/edit JSON files | Admin panel needed | Built-in |
| Scale for side project | Perfect | Overkill | Overkill |

---

## 2. JSON Schema

Each blog post is a JSON object. All posts are in a single JSON file (or split by year).

### Single JSON File Approach (Simplest)

```json
// posts.json — stored in R2 bucket
{
  "posts": [
    {
      "slug": "state-of-travel-agencies-india-2026",
      "title": "The State of Travel Agencies in India 2026",
      "excerpt": "An analysis of how Indian travel agencies operate, what tools they use, and where the industry is heading.",
      "content": "Full markdown content here...\n\n## The Current Landscape\n\n...",
      "date": "2026-05-15",
      "updated": "2026-05-15",
      "readTime": "8 min",
      "author": "Pranay",
      "tags": ["industry-research", "india"],
      "category": "research",
      "featuredImage": "https://r2.example.com/images/blog-1-hero.webp",
      "canonical": null
    },
    {
      "slug": "spreadsheets-vs-ai-travel-agencies",
      "title": "Spreadsheets vs AI: What Actually Works for Travel Agencies",
      "excerpt": "A real comparison of time, cost, and accuracy between manual processes and AI-powered tools.",
      "content": "...",
      "date": "2026-05-22",
      "updated": "2026-05-22",
      "readTime": "6 min",
      "author": "Pranay",
      "tags": ["comparison", "productivity"],
      "category": "guides",
      "featuredImage": null
    }
  ]
}
```

### Split by Year (Better at 200+ posts)

```
r2://waypoint-blog/
  posts/
    2026/
      05-state-of-travel-agencies.json
      05-spreadsheets-vs-ai.json
      06-5-signs-ai-ready.json
    2027/
      ...
  index.json  ← list of all posts (slug, title, date, excerpt, tags only)
  tags.json   ← tag cloud
```

### Index File (for listing pages)

```json
// index.json — lightweight, fetched for blog listing
{
  "posts": [
    {
      "slug": "state-of-travel-agencies-india-2026",
      "title": "The State of Travel Agencies in India 2026",
      "excerpt": "An analysis of how Indian travel agencies operate...",
      "date": "2026-05-15",
      "readTime": "8 min",
      "tags": ["industry-research", "india"],
      "category": "research"
    }
  ],
  "totalPosts": 200,
  "lastUpdated": "2026-04-30"
}
```

---

## 3. Build Script

A simple Python script converts markdown source files into the JSON dump.

```
tools/
  build-blog.py  ← reads MD files, generates JSON, uploads to R2
```

### Script Outline

```python
# tools/build-blog.py
# Run: python3 tools/build-blog.py
# Reads: blog-posts/*.md (frontmatter + markdown)
# Writes: posts.json + index.json → uploads to Cloudflare R2

import os, json, re
from datetime import datetime

BLOG_SRC = "blog-posts/"
OUTPUT = "dist/blog/"
R2_BUCKET = "waypoint-blog"

def parse_md(filepath):
    """Extract frontmatter and body from markdown file."""
    with open(filepath) as f:
        content = f.read()
    
    # Parse YAML frontmatter (between --- markers)
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return None
    
    frontmatter = parse_yaml(match.group(1))
    body = match.group(2).strip()
    
    return {
        "slug": os.path.splitext(os.path.basename(filepath))[0],
        "content": body,
        **frontmatter
    }

def build():
    posts = []
    for f in sorted(os.listdir(BLOG_SRC)):
        if f.endswith(".md"):
            post = parse_md(os.path.join(BLOG_SRC, f))
            if post:
                posts.append(post)
    
    # Sort by date descending
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    
    # Write full posts
    with open("posts.json", "w") as f:
        json.dump({"posts": posts}, f, indent=2)
    
    # Write index (lightweight)
    index = [{
        "slug": p["slug"],
        "title": p["title"],
        "excerpt": p.get("excerpt", ""),
        "date": p["date"],
        "readTime": p.get("readTime"),
        "tags": p.get("tags", []),
        "category": p.get("category"),
    } for p in posts]
    
    with open("index.json", "w") as f:
        json.dump({"posts": index, "totalPosts": len(posts),
                    "lastUpdated": datetime.now().isoformat()}, f, indent=2)
    
    # Upload to R2
    os.system(f"rclone copy posts.json r2:{R2_BUCKET}/")
    os.system(f"rclone copy index.json r2:{R2_BUCKET}/")
    
    print(f"Built {len(posts)} posts. Uploaded to R2.")

if __name__ == "__main__":
    build()
```

### Blog Post Source File

```
blog-posts/state-of-travel-agencies-india-2026.md
```

```markdown
---
title: The State of Travel Agencies in India 2026
excerpt: An analysis of how Indian travel agencies operate, what tools they use, and where the industry is heading.
date: 2026-05-15
updated: 2026-05-15
readTime: 8 min
author: Pranay
tags: [industry-research, india]
category: research
featuredImage: https://r2.example.com/images/blog-1-hero.webp
---

## The Current Landscape

Indian travel agencies are at an inflection point...

[Full markdown content here]
```

---

## 4. Next.js Frontend

### Fetching from R2

```typescript
// lib/blog.ts
const R2_BASE = 'https://pub-abc123.r2.dev/waypoint-blog';

export async function getAllPosts(): Promise<BlogIndexEntry[]> {
  const res = await fetch(`${R2_BASE}/index.json`, {
    next: { revalidate: 3600 }, // ISR: revalidate every hour
  });
  const data = await res.json();
  return data.posts;
}

export async function getPostBySlug(slug: string): Promise<BlogPost | null> {
  const res = await fetch(`${R2_BASE}/posts/2026/${slug}.json`, {
    next: { revalidate: 3600 },
  });
  if (!res.ok) return null;
  return res.json();
}
```

### Pages

```tsx
// app/blog/page.tsx — listing page
export default async function BlogPage() {
  const posts = await getAllPosts();
  return (
    <div>
      <h1>Blog</h1>
      {posts.map(post => (
        <BlogCard key={post.slug} post={post} />
      ))}
    </div>
  );
}
```

```tsx
// app/blog/[slug]/page.tsx — individual post
export default async function BlogPostPage({ params }: Props) {
  const post = await getPostBySlug(params.slug);
  if (!post) return notFound();
  
  return (
    <article>
      <h1>{post.title}</h1>
      <div className="prose" dangerouslySetInnerHTML={{ __html: markdownToHtml(post.content) }} />
    </article>
  );
}
```

### Rendering Markdown

```bash
npm install remark remark-html
```

```typescript
import { remark } from 'remark';
import html from 'remark-html';

function markdownToHtml(md: string): string {
  return remark().use(html).processSync(md).toString();
}
```

---

## 5. Cloudflare R2 Setup (10 Min)

```bash
# 1. Create R2 bucket
npx wrangler r2 bucket create waypoint-blog

# 2. Make it public (for direct URL access)
# In Cloudflare Dashboard: R2 → waypoint-blog → Settings → Public Access → Allow

# 3. Install rclone
brew install rclone

# 4. Configure rclone for R2
rclone config
# → Choose S3-compatible
# → Endpoint: https://<account-id>.r2.cloudflarestorage.com
# → Access Key & Secret from Cloudflare R2 dashboard

# 5. Upload
python3 tools/build-blog.py
```

### Cost

| Resource | Free Tier | Expected Usage | Cost |
|----------|-----------|----------------|------|
| Cloudflare R2 | 10GB storage, 10M requests/mo | ~50MB, ~5K requests/mo | $0 |
| R2 bandwidth (egress) | Free | Free | $0 |
| **Total** | | | **$0/mo** |

---

## 6. Converting 200+ Docs to Blog Posts

### Strategy: Don't convert everything. Curate the best.

| Tier | Count | Action |
|------|-------|--------|
| **Tier 1: Publish now** | 10-20 | Docs that are already close to blog-ready (pricing research, competitive analysis, GTM strategy) |
| **Tier 2: Adapt** | 30-50 | Docs that need light editing to become posts (remove internal notes, add intro, add CTA) |
| **Tier 3: Reference** | 100+ | Leave as docs. Use them as source material for future posts. |

### Workflow per post

```
1. Pick a Tier 1 doc from Docs/
2. Strip internal references ("see FUNDRAISING_ASSESSMENT.md")
3. Write a self-contained intro paragraph
4. Add a CTA at the bottom ("Want to automate your inquiry processing? Try Waypoint OS free.")
5. Save as blog-posts/<slug>.md
6. Run: python3 tools/build-blog.py
7. Share on Facebook/WhatsApp
```

**Time per post**: ~20 min (most of the content is already written).

---

## 7. Files to Create

```
travel_agency_agent/
  blog-posts/                  ← Source markdown files (new)
    state-of-travel-agencies-india-2026.md
    spreadsheets-vs-ai.md
    ...
  tools/
    build-blog.py              ← Build + upload script (new)
  frontend/
    src/
      lib/
        blog.ts                ← Fetch from R2 (new)
      app/
        blog/
          page.tsx             ← Listing page (new)
          [slug]/
            page.tsx           ← Post page (new)
```

### Implementation Order

```
Day 1: Set up R2 bucket + rclone config (10 min)
Day 1: Create build-blog.py (30 min)
Day 1: Create blog.ts lib + blog pages (30 min)
Day 2: Convert first 3 Tier 1 docs to blog posts (1 hour)
Day 2: Run build script, verify pages work (15 min)
Day 3: Add blog section to homepage + update nav (30 min)
Day 3: Submit blog sitemap to Google Search Console (10 min)
```

**Total implementation time**: ~3-4 hours.
