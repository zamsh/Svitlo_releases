"""Finds Kharkivoblenergo's current "Адреси та черги" PDF and prints it as JSON {"url": URL}.

The site's Drupal JSON:API lists uploaded files; the newest PDF whose name has "Адреси та черги" wins
("Адреси та черги 26-27.pdf" for the 2026–27 season). Exit code 1 if none is found.
"""
import json, sys, urllib.parse, urllib.request

SITE = "https://oblenergo.kharkiv.ua"
API = (SITE + "/uk/jsonapi/file/file?sort=-created&page%5Blimit%5D=20"
       "&filter%5Bf%5D%5Bcondition%5D%5Bpath%5D=filename&filter%5Bf%5D%5Bcondition%5D%5Boperator%5D=CONTAINS"
       "&filter%5Bf%5D%5Bcondition%5D%5Bvalue%5D=" + urllib.parse.quote("Адреси та черг"))


def find(listing):
    for f in listing.get("data", []):
        a = f.get("attributes", {})
        if a.get("filemime") == "application/pdf" and a.get("uri", {}).get("url"):
            return SITE + a["uri"]["url"]
    return None


def main():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0 (SvitloIndexBot)", "Accept": "application/vnd.api+json"})
    url = find(json.load(urllib.request.urlopen(req, timeout=60)))
    if not url:
        print(f"No \"Адреси та черги\" PDF in {API}", file=sys.stderr)
        return 1
    print(json.dumps({"url": url}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
