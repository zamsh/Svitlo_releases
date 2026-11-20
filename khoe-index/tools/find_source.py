"""Finds the link to Kharkivoblenergo's current "Адреси та черги" PDF in the operator's Telegram channel.

The site (oblenergo.kharkiv.ua) is behind a Cloudflare check since 2026-11 and its file API is off, so the
document can't be found or downloaded automatically. Every evening outage-schedule post on the public
channel preview https://t.me/s/kharkivenergy ends with "Перелік адрес за чергами — тут" linking the PDF;
the newest such link is the current document. One plain GET of the public page, plus one older page
(?before=<oldest post>) if the first has no such post. The PDF itself is not fetched.

Prints JSON {"url": URL, "new": bool} — "new" when the link differs from the one in meta.json (the
document the current index.json was built from). Exit codes: 0 found, 2 no link in the channel,
3 channel unreachable; the message for 2 and 3 goes to stderr.
"""
import argparse, html, json, os, re, sys, urllib.error, urllib.parse, urllib.request

CHANNEL = "https://t.me/s/kharkivenergy"
MARKER = re.compile(r"Перелік\s+адрес", re.I)
POST = re.compile(r'data-post="kharkivenergy/(\d+)"')
HREF = re.compile(r'<a\s[^>]*href="([^"]+)"', re.I)
META = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "meta.json")


def posts(page):
    """[(post id, post html)] in page order."""
    marks = list(POST.finditer(page))
    return [(int(m.group(1)), page[m.start():marks[i + 1].start() if i + 1 < len(marks) else len(page)])
            for i, m in enumerate(marks)]


def link_in(post):
    """The link right after "Перелік адрес" in a post, if it points to a PDF."""
    m = MARKER.search(post)
    if not m:
        return None
    a = HREF.search(post, m.end())
    if not a:
        return None
    url = html.unescape(a.group(1))
    return url if urllib.parse.unquote(urllib.parse.urlsplit(url).path).lower().endswith(".pdf") else None


def find(page):
    """(newest "Перелік адрес" PDF link or None, oldest post id on the page or None)."""
    ps = posts(page)
    found = [(pid, url) for pid, url in ((pid, link_in(p)) for pid, p in ps) if url]
    return (max(found)[1] if found else None), (min(pid for pid, _ in ps) if ps else None)


def same_document(a, b):
    """Links equal up to percent-encoding ("Адреси%20та" == "Адреси та")."""
    norm = lambda u: urllib.parse.unquote(u or "").strip()
    return norm(a) == norm(b)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (SvitloIndexBot)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default=META, help="meta.json of the current index")
    args = ap.parse_args(argv)
    try:
        url, oldest = find(fetch(CHANNEL))
        if not url and oldest:
            url, _ = find(fetch(f"{CHANNEL}?before={oldest}"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"Telegram channel {CHANNEL} didn't answer: {e}", file=sys.stderr)
        return 3
    if not url:
        print(f"No \"Перелік адрес за чергами\" PDF link in the last two pages of {CHANNEL}", file=sys.stderr)
        return 2
    try:
        with open(args.meta, encoding="utf-8") as f:
            current = json.load(f).get("url")
    except (OSError, ValueError):
        current = None
    print(json.dumps({"url": url, "new": not same_document(url, current)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
