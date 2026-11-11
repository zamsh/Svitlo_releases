"""Finds Rivneoblenergo's current GPV documents on roe.vsei.ua and prints them as JSON
{"city": URL, "region": URL}.

The disconnections page links them as wp-content/uploads/YYYY/MM/GPV_cherga_misto_Rivne*.pdf and
GPV_cherga_Rivnenska_oblast*.pdf; when several are linked, the most recently uploaded one wins
(upload folder, then the "-N" suffix). Exit code 1 if either link is missing (page layout changed).
"""
import json, re, sys, urllib.request

PAGE = "https://www.roe.vsei.ua/disconnections"
LINK = re.compile(r'href="(https://www\.roe\.vsei\.ua/wp-content/uploads/(\d{4})/(\d{2})/(GPV_cherga_(misto_Rivne|Rivnenska_oblast)(?:-(\d+))?\.pdf))"', re.I)
KIND = {"misto_rivne": "city", "rivnenska_oblast": "region"}


def find(html):
    best = {}
    for m in LINK.finditer(html):
        kind = KIND[m.group(5).lower()]
        key = (int(m.group(2)), int(m.group(3)), int(m.group(6) or 0))
        if kind not in best or key > best[kind][0]:
            best[kind] = (key, m.group(1))
    return {k: v[1] for k, v in sorted(best.items())}


def main():
    req = urllib.request.Request(PAGE, headers={"User-Agent": "Mozilla/5.0 (SvitloIndexBot)"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    found = find(html)
    if set(found) != {"city", "region"}:
        print(f"GPV documents not found on {PAGE}: {found}", file=sys.stderr)
        return 1
    print(json.dumps(found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
