# RSS Feed Finder

A Python GUI tool that attempts to discover RSS and Atom feeds from any website URL - even sites behind aggressive bot protection (Cloudflare, Sucuri, Akamai, etc.).

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-Unlicense-green)

## Why?

Not every website advertises its RSS feeds in `<link>` tags. Some bury them at non-standard paths, some hide them behind WAFs, and some make you guess. This tool uses five different discovery strategies and three HTTP session modes to find feeds that may be tricky to obtain.

## Features

- **Tkinter GUI** — no command line needed, real-time colour-coded output
- **Five discovery strategies:**
  1. HTML `<link rel="alternate">` tag detection
  2. High-priority common feed paths (covers ~90% of sites)
  3. Extended path brute-force (30+ well-known feed URLs)
  4. Internal link crawling for feed-like URLs
  5. Sitemap/robots.txt parsing for category and tag feeds
  6. Google search fallback as a last resort
- **Three HTTP session modes to bypass bot protection:**
  - **Standard** — browser-like headers with `requests` (works for most sites)
  - **Legacy SSL** — plain headers with relaxed TLS settings (bypasses WAFs that detect TLS fingerprint mismatches, e.g. Sucuri)
  - **Impersonate browser** — full Chrome TLS fingerprint via `curl_cffi` (bypasses strict WAFs like Cloudflare that check TLS fingerprints)
- **Configurable request delay** with ±30% jitter to avoid rate limiting
- **Automatic session probing** — tries standard first, falls back to legacy if blocked
- **Smart deduplication** — normalises trailing slashes to avoid duplicate results
- **Category/tag feed cap** — limits how many category feeds to check (configurable)
- **Stop button** — cancel a scan mid-run without waiting

## Installation

```bash
pip install requests beautifulsoup4 fake-useragent curl_cffi
```

## Usage

```bash
python rssfeedfinder.py
```

This opens the GUI. Enter a URL and click **Scan**.

### Settings

| Setting | Default | Description |
|---|---|---|
| **Delay** | 2s | Seconds between requests. Use 5–7 for aggressive WAFs. |
| **Legacy SSL** | Off | Use for sites with old TLS configs or WAFs that block browser-like headers (e.g. Sucuri). |
| **Impersonate browser** | Off | Use for sites with strict TLS fingerprint checking (e.g. Cloudflare). Requires `curl_cffi`. |
| **Max category feeds** | 10 | Cap on how many category/tag feeds to validate. |

### Which mode should I use?

| Symptom | Mode |
|---|---|
| Works fine, no issues | Default (no checkboxes) |
| Everything returns 403, but site works in browser | Try **Impersonate browser** first |
| 403s with Impersonate, but plain `requests` works without headers | Try **Legacy SSL** |
| Site is slow to respond or starts timing out | Increase **Delay** to 5–7 seconds |

### Tips for stubborn sites

- If a site blocks you after several requests, **wait 15–30 minutes** for the rate limit to clear, then try again with a higher delay.
- Some WAFs (like Sucuri) have long cooldown periods. If you've been testing repeatedly, you may need to wait an hour or more.
- **Legacy SSL** and **Impersonate browser** solve opposite problems — don't tick both at the same time.

## How it works

The tool runs through its strategies in order:

1. **Fetch the main page** — this also probes which session mode works for the site
2. **Check HTML `<link>` tags** — the fastest method, but many sites don't use them
3. **Try priority feed paths** — `/feed/`, `/rss/index.xml`, `/feed.xml`, `/atom.xml`, `/rss.xml`, `/index.xml`, `/category/blog/feed/`
4. **Try extended paths** — 26 additional common feed URL patterns
5. **Crawl internal links** — looks for anchor tags containing "feed", "rss", or "atom"
6. **Parse sitemaps** — checks `sitemap.xml` and `robots.txt` for category/tag URLs, appends `/feed/` to each
7. **Google search** — last resort, searches for `site:domain inurl:feed OR inurl:rss`

If priority paths find feeds, extended paths are skipped to reduce request volume.

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for standard and legacy sessions |
| `beautifulsoup4` | HTML parsing for link and anchor tag detection |
| `fake-useragent` | Rotating User-Agent strings for standard session |
| `curl_cffi` | Browser TLS fingerprint impersonation |

## Licence

Unlicense - do what you like with it.

