#!/usr/bin/env python3
"""
RSS Feed Finder — discovers RSS/Atom feeds from a website URL.

Requires:
    pip install requests beautifulsoup4 fake-useragent curl_cffi

GUI version — all settings configurable via the interface.
"""

import re
import ssl
import random
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from xml.etree import ElementTree
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from fake_useragent import UserAgent
from curl_cffi import requests as cffi_requests

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuration ─────────────────────────────────────────────────────────────
TIMEOUT = 15
MAX_CRAWL_PAGES = 20
MAX_CATEGORY_FEEDS = 10
DEFAULT_DELAY = 2

PRIORITY_PATHS = [
    "/feed/",
    "/rss/index.xml",
    "/feed.xml",
    "/atom.xml",
    "/rss.xml",
    "/index.xml",
    "/category/blog/feed/",
]

EXTENDED_PATHS = [
    "/feed", "/feeds", "/feeds/",
    "/rss", "/rss/",
    "/atom", "/atom/",
    "/feed.rss", "/feed.atom",
    "/feed/atom/", "/feed/rss/", "/feed/rss2/",
    "/index.rss",
    "/blog/feed/", "/blog/rss", "/blog/atom.xml", "/blog/feed.xml",
    "/news/feed/", "/news/rss",
    "/category/news/feed/",
    "/comments/feed/",
    "/author/feed/",
    "/?feed=rss", "/?feed=rss2", "/?feed=atom",
]

FEED_CONTENT_TYPES = [
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
]

BLOCKED_STATUS_CODES = {403, 406, 418, 420, 429, 503, 999}

BLOCKED_SIGNALS = [
    "access denied", "please wait", "checking your browser", "just a moment",
    "enable javascript", "captcha", "cf-browser-verification", "sucuri",
    "cloudflare", "ray id", "attention required", "turnstile",
    "security check", "bot protection", "ddos-guard", "perimeterx", "akamai",
]


# ── Legacy SSL adapter ───────────────────────────────────────────────────────
class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        try:
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        except AttributeError:
            pass
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


# ── URL normalisation ─────────────────────────────────────────────────────────
def normalise_feed_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def deduplicate_feeds(feeds):
    seen = set()
    unique = []
    for f in feeds:
        norm = normalise_feed_url(f)
        if norm not in seen:
            seen.add(norm)
            unique.append(f)
    return unique


# ── Feed Finder Engine ────────────────────────────────────────────────────────
class FeedFinder:
    def __init__(self, log_callback, status_callback):
        self.log = log_callback
        self.set_status = status_callback
        self._ua = UserAgent()
        self._base_delay = DEFAULT_DELAY
        self._session_mode = "unknown"
        self._std_session = None
        self._leg_session = None
        self._imp_session = None
        self._cancelled = False

    def _build_headers(self):
        return {
            "User-Agent": self._ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    def _create_sessions(self):
        self._std_session = requests.Session()
        self._std_session.headers.update(self._build_headers())
        self._leg_session = requests.Session()
        self._leg_session.mount("https://", LegacySSLAdapter())
        # No custom headers for legacy — fake browser headers + non-browser TLS
        # fingerprint triggers WAF detection. Default python-requests UA is safer.
        self._imp_session = cffi_requests.Session(impersonate="chrome")

    def _polite_delay(self):
        if self._cancelled:
            return
        jitter = self._base_delay * 0.3
        time.sleep(random.uniform(self._base_delay - jitter, self._base_delay + jitter))

    def _is_response_blocked(self, r):
        if r.status_code in BLOCKED_STATUS_CODES:
            return True
        text = r.text.lower()
        return any(sig in text for sig in BLOCKED_SIGNALS)

    def _probe_session(self, url):
        try:
            r = self._std_session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=True)
            if not self._is_response_blocked(r):
                self._session_mode = "standard"
                return r
        except requests.RequestException:
            pass

        self._session_mode = "legacy"
        if self._base_delay < 5:
            self._base_delay = 5
            self.log(f"  ℹ  Site has bot protection. Delay increased to {self._base_delay}s.", "info")

        try:
            r = self._leg_session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=False)
            if not self._is_response_blocked(r):
                self.log("  ℹ  Using legacy SSL mode.", "info")
                return r
        except requests.RequestException:
            pass

        self.log("  ℹ  Using legacy SSL mode (main page blocked, trying feed paths).", "info")
        return None

    def _fetch(self, url):
        if self._cancelled:
            return None
        if self._session_mode == "unknown":
            return self._probe_session(url)

        if self._session_mode == "impersonate":
            try:
                r = self._imp_session.get(url, timeout=TIMEOUT, allow_redirects=True)
                if r.status_code in BLOCKED_STATUS_CODES:
                    return None
                return r
            except Exception:
                return None

        session = self._leg_session if self._session_mode == "legacy" else self._std_session
        verify = self._session_mode != "legacy"

        try:
            r = session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=verify)
            if r.status_code in BLOCKED_STATUS_CODES:
                return None
            return r
        except requests.RequestException:
            return None

    def _is_page_blocked(self, response):
        if response is None:
            return True
        if response.status_code in BLOCKED_STATUS_CODES:
            return True
        text = response.text.lower()
        return any(signal in text for signal in BLOCKED_SIGNALS)

    def _is_valid_feed(self, url):
        r = self._fetch(url)
        if r is None:
            return False
        if self._is_page_blocked(r):
            return False

        content_type = r.headers.get("Content-Type", "").lower()
        ct_match = any(ct in content_type for ct in FEED_CONTENT_TYPES)

        try:
            root = ElementTree.fromstring(r.content)
            tag = root.tag.lower()
            xml_match = any(kw in tag for kw in ["rss", "feed", "rdf", "channel"])
            return ct_match or xml_match
        except ElementTree.ParseError:
            return False

    # ── Strategies ────────────────────────────────────────────────────────

    def _find_feeds_in_html(self, url, soup):
        feeds = []
        for link in soup.find_all("link", rel="alternate"):
            link_type = link.get("type", "").lower()
            if "rss" in link_type or "atom" in link_type:
                href = link.get("href")
                if href:
                    feeds.append(urljoin(url, href))
        return feeds

    def _find_feeds_by_common_paths(self, base_url):
        feeds = []
        parsed = urlparse(base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        found_normalised = set()

        self.log("  ℹ  Trying high-priority feed paths...", "info")
        for i, path in enumerate(PRIORITY_PATHS, 1):
            if self._cancelled:
                return feeds
            candidate = root + path
            self.set_status(f"Priority paths... ({i}/{len(PRIORITY_PATHS)})")
            if self._is_valid_feed(candidate):
                self.log(f"  ✓  Found: {candidate}", "found")
                feeds.append(candidate)
                found_normalised.add(normalise_feed_url(candidate))
            self._polite_delay()

        if feeds:
            self.log(f"  ℹ  Found {len(feeds)} feed(s) in priority paths. Skipping extended.", "info")
            return feeds

        self.log("  ℹ  Trying extended feed paths...", "info")
        total = len(EXTENDED_PATHS)
        for i, path in enumerate(EXTENDED_PATHS, 1):
            if self._cancelled:
                return feeds
            candidate = root + path
            if normalise_feed_url(candidate) in found_normalised:
                continue
            self.set_status(f"Extended paths... ({i}/{total})")
            if self._is_valid_feed(candidate):
                self.log(f"  ✓  Found: {candidate}", "found")
                feeds.append(candidate)
                found_normalised.add(normalise_feed_url(candidate))
            self._polite_delay()

        return feeds

    def _find_feeds_by_crawling(self, url, soup):
        parsed_base = urlparse(url)
        base_domain = parsed_base.netloc
        feed_pattern = re.compile(r"(feed|rss|atom)", re.IGNORECASE)

        candidate_urls = set()
        for a_tag in soup.find_all("a", href=True):
            href = urljoin(url, a_tag["href"])
            parsed_href = urlparse(href)
            if parsed_href.netloc != base_domain:
                continue
            if feed_pattern.search(href):
                candidate_urls.add(href)

        feeds = []
        checked = 0
        for candidate in candidate_urls:
            if self._cancelled or checked >= MAX_CRAWL_PAGES:
                break
            checked += 1
            self.set_status(f"Crawling... ({checked}/{min(len(candidate_urls), MAX_CRAWL_PAGES)})")
            if self._is_valid_feed(candidate):
                feeds.append(candidate)
            self._polite_delay()

        return feeds

    def _discover_category_feeds(self, base_url, soup=None):
        parsed = urlparse(base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        category_pattern = re.compile(
            r"/(category|tag|topics?|section|author)/[^/]+/?$", re.IGNORECASE
        )
        candidates = set()

        if soup:
            for a_tag in soup.find_all("a", href=True):
                href = urljoin(base_url, a_tag["href"])
                parsed_href = urlparse(href)
                if parsed_href.netloc != parsed.netloc:
                    continue
                if category_pattern.search(parsed_href.path):
                    path = parsed_href.path.rstrip("/")
                    candidates.add(f"{root}{path}/feed/")

        self.log("  ℹ  Checking sitemap.xml...", "info")
        r = self._fetch(f"{root}/sitemap.xml")
        self._polite_delay()

        if r and not self._is_page_blocked(r):
            try:
                sitemap_root = ElementTree.fromstring(r.content)
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                sitemap_locs = sitemap_root.findall(".//sm:sitemap/sm:loc", ns)
                if sitemap_locs:
                    self.log(f"  ℹ  Found sitemap index with {len(sitemap_locs)} sub-sitemaps...", "info")
                    for sloc in sitemap_locs:
                        if self._cancelled:
                            break
                        sub_r = self._fetch(sloc.text or "")
                        self._polite_delay()
                        if sub_r and not self._is_page_blocked(sub_r):
                            try:
                                sub_root = ElementTree.fromstring(sub_r.content)
                                for loc in sub_root.findall(".//sm:loc", ns):
                                    url_text = loc.text or ""
                                    if category_pattern.search(urlparse(url_text).path):
                                        path = urlparse(url_text).path.rstrip("/")
                                        candidates.add(f"{root}{path}/feed/")
                            except ElementTree.ParseError:
                                pass

                for loc in sitemap_root.findall(".//sm:loc", ns):
                    url_text = loc.text or ""
                    if category_pattern.search(urlparse(url_text).path):
                        path = urlparse(url_text).path.rstrip("/")
                        candidates.add(f"{root}{path}/feed/")
            except ElementTree.ParseError:
                pass

        self.log("  ℹ  Checking robots.txt...", "info")
        r = self._fetch(f"{root}/robots.txt")
        self._polite_delay()

        if r and not self._is_page_blocked(r):
            for line in r.text.splitlines():
                if line.strip().lower().startswith("sitemap:"):
                    sitemap_href = line.split(":", 1)[1].strip()
                    sr = self._fetch(sitemap_href)
                    self._polite_delay()
                    if sr and not self._is_page_blocked(sr):
                        try:
                            sr_root = ElementTree.fromstring(sr.content)
                            ns2 = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                            for loc in sr_root.findall(".//sm:loc", ns2):
                                url_text = loc.text or ""
                                if category_pattern.search(urlparse(url_text).path):
                                    path = urlparse(url_text).path.rstrip("/")
                                    candidates.add(f"{root}{path}/feed/")
                        except ElementTree.ParseError:
                            pass

        feeds = []
        total = len(candidates)
        if total > 0:
            self.log(f"  ℹ  Found {total} potential category/tag feed URLs to check...", "info")
        checked = 0
        for i, candidate in enumerate(candidates, 1):
            if self._cancelled:
                break
            self.set_status(f"Checking category feeds... ({i}/{total})")
            if self._is_valid_feed(candidate):
                self.log(f"  ✓  Found: {candidate}", "found")
                feeds.append(candidate)
                checked += 1
                if checked >= MAX_CATEGORY_FEEDS:
                    self.log(f"  ℹ  Reached category feed cap ({MAX_CATEGORY_FEEDS}).", "info")
                    break
            self._polite_delay()

        return feeds

    def _find_feeds_via_search(self, domain):
        feeds = []
        query = quote_plus(f"site:{domain} inurl:feed OR inurl:rss OR inurl:atom")
        search_url = f"https://www.google.com/search?q={query}&num=10"

        r = self._fetch(search_url)
        if r is None:
            return feeds

        soup = BeautifulSoup(r.text, "html.parser")
        feed_pattern = re.compile(r"(feed|rss|atom)", re.IGNORECASE)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/url?q=" in href:
                actual_url = href.split("/url?q=")[1].split("&")[0]
                if domain in actual_url and feed_pattern.search(actual_url):
                    feeds.append(actual_url)

        return list(dict.fromkeys(feeds))

    # ── Main discovery ────────────────────────────────────────────────────

    def discover(self, url, force_legacy=False, force_impersonate=False, delay=DEFAULT_DELAY):
        self._cancelled = False
        self._base_delay = delay
        if force_impersonate:
            self._session_mode = "impersonate"
        elif force_legacy:
            self._session_mode = "legacy"
        else:
            self._session_mode = "unknown"
        self._create_sessions()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        domain = parsed.netloc

        self.log(f"Target: {url}", "header")
        if force_impersonate:
            self.log("  ℹ  Impersonate browser mode enabled.", "info")
        elif force_legacy:
            self.log("  ℹ  Legacy SSL mode enabled.", "info")
        self.log(f"  ℹ  Delay: {self._base_delay}s (±30% jitter).", "info")

        all_feeds = []
        main_page_accessible = False
        soup = None

        self.log("\n  ℹ  Fetching main page...", "info")
        self.set_status("Fetching main page...")
        response = self._fetch(url)
        self._polite_delay()

        if self._cancelled:
            return []

        if response is None:
            self.log("  ⚠  Could not load main page (may be behind bot protection).", "warn")
            self.log("  ⚠  Will still try direct feed detection.\n", "warn")
        elif self._is_page_blocked(response):
            self.log("  ⚠  Main page is behind bot protection.", "warn")
            self.log("  ⚠  Skipping HTML scan — trying direct feed detection.\n", "warn")
        else:
            main_page_accessible = True
            soup = BeautifulSoup(response.text, "html.parser")
            self.log("  ✓  Main page loaded successfully.", "found")

        # Strategy 1 — HTML link tags
        if main_page_accessible and soup and not self._cancelled:
            self.log("  ℹ  Checking HTML <link> tags...", "info")
            html_feeds = self._find_feeds_in_html(url, soup)
            if html_feeds:
                for f in html_feeds:
                    self.log(f"  ✓  Found via <link>: {f}", "found")
                all_feeds.extend(html_feeds)
            else:
                self.log("  ⚠  No feeds in HTML <link> tags.", "warn")

        # Strategy 2 — Common paths
        if not self._cancelled:
            path_feeds = self._find_feeds_by_common_paths(url)
            new_path = [f for f in path_feeds if normalise_feed_url(f) not in
                        {normalise_feed_url(x) for x in all_feeds}]
            if new_path:
                all_feeds.extend(new_path)
            else:
                self.log("  ⚠  No feeds found at common paths.", "warn")

        # Strategy 3 — Crawl
        if main_page_accessible and soup and not self._cancelled:
            self.log("  ℹ  Crawling site for feed-like links...", "info")
            self.set_status("Crawling...")
            crawl_feeds = self._find_feeds_by_crawling(url, soup)
            new_crawl = [f for f in crawl_feeds if normalise_feed_url(f) not in
                         {normalise_feed_url(x) for x in all_feeds}]
            if new_crawl:
                for f in new_crawl:
                    self.log(f"  ✓  Found via crawl: {f}", "found")
                all_feeds.extend(new_crawl)
            else:
                self.log("  ⚠  No additional feeds found by crawling.", "warn")

        # Strategy 4 — Category/tag feeds
        if not self._cancelled:
            self.log("  ℹ  Checking for category/tag feeds...", "info")
            self.set_status("Checking category feeds...")
            cat_feeds = self._discover_category_feeds(url, soup)
            new_cat = [f for f in cat_feeds if normalise_feed_url(f) not in
                       {normalise_feed_url(x) for x in all_feeds}]
            if new_cat:
                all_feeds.extend(new_cat)
            elif not cat_feeds:
                self.log("  ⚠  No category/tag feeds found.", "warn")

        # Strategy 5 — Google search
        if not all_feeds and not self._cancelled:
            self.log("  ℹ  Searching Google for feed URLs...", "info")
            self.set_status("Searching Google...")
            search_feeds = self._find_feeds_via_search(domain)
            if search_feeds:
                for candidate in search_feeds:
                    if self._cancelled:
                        break
                    if self._is_valid_feed(candidate):
                        self.log(f"  ✓  Found via search: {candidate}", "found")
                        all_feeds.append(candidate)
                    self._polite_delay()
                if not all_feeds:
                    self.log("  ⚠  Search results didn't contain valid feeds.", "warn")
            else:
                self.log("  ⚠  No feeds found via Google search.", "warn")

        # Results
        unique_feeds = deduplicate_feeds(all_feeds)

        self.log("", "info")
        if unique_feeds:
            main_feeds = [f for f in unique_feeds if "/tag/" not in f and
                          not re.search(r"/category/[^/]+/feed", f)]
            cat_feeds_list = [f for f in unique_feeds if f not in main_feeds]

            self.log(f"Found {len(unique_feeds)} feed(s):", "result")
            if main_feeds:
                self.log("\nMain feeds:", "result")
                for i, feed_url in enumerate(main_feeds, 1):
                    self.log(f"  {i}. {feed_url}", "result_url")
            if cat_feeds_list:
                self.log(f"\nCategory/tag feeds ({len(cat_feeds_list)} total):", "result")
                for i, feed_url in enumerate(cat_feeds_list[:MAX_CATEGORY_FEEDS], 1):
                    self.log(f"  {i}. {feed_url}", "result_url")
                if len(cat_feeds_list) > MAX_CATEGORY_FEEDS:
                    self.log(f"  ... and {len(cat_feeds_list) - MAX_CATEGORY_FEEDS} more.", "info")
        else:
            self.log("No RSS/Atom feeds found for this site.", "error")

        self.set_status("Done.")
        return unique_feeds

    def cancel(self):
        self._cancelled = True


# ── GUI ───────────────────────────────────────────────────────────────────────
class FeedFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RSS Feed Finder")
        self.root.geometry("750x600")
        self.root.minsize(600, 450)

        self.finder = None
        self._running = False

        self._build_ui()

    def _build_ui(self):
        # ── Settings frame ────────────────────────────────────────────────
        settings = ttk.LabelFrame(self.root, text="Settings", padding=10)
        settings.pack(fill="x", padx=10, pady=(10, 5))

        # URL row
        url_frame = ttk.Frame(settings)
        url_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(url_frame, text="URL:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.url_entry.bind("<Return>", lambda e: self._start_scan())

        # Options row
        opts_frame = ttk.Frame(settings)
        opts_frame.pack(fill="x")

        ttk.Label(opts_frame, text="Delay (seconds):").pack(side="left")
        self.delay_var = tk.StringVar(value=str(DEFAULT_DELAY))
        delay_spin = ttk.Spinbox(opts_frame, from_=0, to=30, increment=0.5,
                                 textvariable=self.delay_var, width=5)
        delay_spin.pack(side="left", padx=(5, 15))

        self.legacy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="Legacy SSL", variable=self.legacy_var).pack(side="left")

        self.impersonate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="Impersonate browser",
                        variable=self.impersonate_var).pack(side="left", padx=(10, 0))

        ttk.Label(opts_frame, text="Max category feeds:").pack(side="left", padx=(15, 0))
        self.max_cat_var = tk.StringVar(value=str(MAX_CATEGORY_FEEDS))
        max_cat_spin = ttk.Spinbox(opts_frame, from_=1, to=200, increment=1,
                                   textvariable=self.max_cat_var, width=5)
        max_cat_spin.pack(side="left", padx=(5, 0))

        # ── Buttons frame ─────────────────────────────────────────────────
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.scan_btn = ttk.Button(btn_frame, text="Scan", command=self._start_scan)
        self.scan_btn.pack(side="left")

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=(5, 0))

        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self._clear_log)
        self.clear_btn.pack(side="left", padx=(5, 0))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(btn_frame, textvariable=self.status_var,
                  foreground="grey").pack(side="right")

        # ── Output area ───────────────────────────────────────────────────
        output_frame = ttk.LabelFrame(self.root, text="Output", padding=5)
        output_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.output = scrolledtext.ScrolledText(output_frame, wrap="word",
                                                 font=("Consolas", 10),
                                                 state="disabled",
                                                 background="#1e1e1e",
                                                 foreground="#cccccc",
                                                 insertbackground="#cccccc")
        self.output.pack(fill="both", expand=True)

        # Text tags for colours
        self.output.tag_config("header", foreground="#ffffff", font=("Consolas", 10, "bold"))
        self.output.tag_config("info", foreground="#66b2ff")
        self.output.tag_config("found", foreground="#66ff66")
        self.output.tag_config("warn", foreground="#ffcc00")
        self.output.tag_config("error", foreground="#ff6666", font=("Consolas", 10, "bold"))
        self.output.tag_config("result", foreground="#ffffff", font=("Consolas", 10, "bold"))
        self.output.tag_config("result_url", foreground="#66ff66")

    def _log(self, message, tag="info"):
        """Thread-safe log to the output area."""
        def _append():
            self.output.configure(state="normal")
            self.output.insert("end", message + "\n", tag)
            self.output.see("end")
            self.output.configure(state="disabled")
        self.root.after(0, _append)

    def _set_status(self, text):
        """Thread-safe status bar update."""
        self.root.after(0, lambda: self.status_var.set(text))

    def _clear_log(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.status_var.set("Ready")

    def _start_scan(self):
        url = self.url_var.get().strip()
        if not url:
            self._log("Please enter a URL.", "error")
            return
        if self._running:
            return

        try:
            delay = float(self.delay_var.get())
        except ValueError:
            delay = DEFAULT_DELAY

        try:
            global MAX_CATEGORY_FEEDS
            MAX_CATEGORY_FEEDS = int(self.max_cat_var.get())
        except ValueError:
            pass

        legacy = self.legacy_var.get()
        impersonate = self.impersonate_var.get()

        self._running = True
        self.scan_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.url_entry.configure(state="disabled")

        self._clear_log()
        self._log("═" * 50, "header")
        self._log("  RSS Feed Finder", "header")
        self._log("═" * 50, "header")
        self._log("", "info")

        self.finder = FeedFinder(self._log, self._set_status)

        def run():
            try:
                self.finder.discover(url, force_legacy=legacy,
                                    force_impersonate=impersonate, delay=delay)
            except Exception as e:
                self._log(f"\n  Error: {e}", "error")
            finally:
                self.root.after(0, self._scan_finished)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _stop_scan(self):
        if self.finder:
            self.finder.cancel()
            self._log("\n  ⚠  Scan cancelled.", "warn")
            self._set_status("Cancelled")

    def _scan_finished(self):
        self._running = False
        self.scan_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.url_entry.configure(state="normal")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = FeedFinderApp(root)
    root.mainloop()