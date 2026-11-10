"""Finds the current GPV PDF on poe.pl.ua and prints its URL.

The GPV page links the schedule document as wp-content/uploads/YYYY/MM/HPV_<season>-...pdf; when
several are linked, the most recently uploaded one wins (upload folder, then the date in the name).
Exit code 1 if no document link is found (page layout changed).
"""
import re, sys, urllib.request

PAGE = "https://www.poe.pl.ua/disconnection/hrafik-pohodynnoho-vidkliuchennia-elektroenerhii/"
LINK = re.compile(r'href="(https://www\.poe\.pl\.ua/wp-content/uploads/(\d{4})/(\d{2})/(HPV[^"]*\.pdf))"', re.I)

def name_date(name):
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", name)
    return (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else (0, 0, 0)

def find(html):
    links = {m.group(1): ((int(m.group(2)), int(m.group(3))), name_date(m.group(4))) for m in LINK.finditer(html)}
    return max(links, key=links.get) if links else None

def main():
    req = urllib.request.Request(PAGE, headers={"User-Agent": "Mozilla/5.0 (SvitloIndexBot)"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    url = find(html)
    if not url:
        print("GPV document link not found on " + PAGE, file=sys.stderr)
        return 1
    print(url)
    return 0

if __name__ == "__main__":
    sys.exit(main())
