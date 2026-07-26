"""
SAGE — verse-file builder for the five verse-structured traditions.

Downloads public-domain / freely-distributable editions and normalizes each to
JSONL of {"reference", "text", "section"} whose `reference` matches the gold-label
scheme (so retrieved chunks line up with the gold retrieval targets via
references.py). Output: verses/<tradition>.jsonl for
  christian (KJV Bible), islamic (Qur'an), hindu (Bhagavad Gita),
  buddhist (Dhammapada), taoist (Tao Te Ching).

Sources (all reachable over https, licensed for this use — see SOURCES notes):
  - KJV Bible:      github.com/aruljohn/Bible-kjv          (public domain)
  - Qur'an (EN):    github.com/risan/quran-json            (Saheeh Intl. translation)
  - Bhagavad Gita:  github.com/gita/gita                   (Swami Sivananda, public domain)
  - Dhammapada:     github.com/iacchus/dhammapada.json     (Buddharakkhita, free distribution)
  - Tao Te Ching:   Standard Ebooks (James Legge, public domain; CC0 transcription)

Run:  python build_verses.py            # -> verses/*.jsonl
"""
import json, re, time, urllib.request
from pathlib import Path

VERSES = Path("verses"); VERSES.mkdir(exist_ok=True)
RAW = "https://raw.githubusercontent.com"


def fetch(url, tries=3):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=30).read()
        except Exception as e:
            if t == tries - 1:
                raise
            time.sleep(2)


def write(tradition, records):
    p = VERSES / f"{tradition}.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records))
    print(f"  {tradition:10s} {len(records):>6} verses -> {p}")


# --------------------------------------------------------------------------- #
def build_christian():
    books = json.loads(fetch(f"{RAW}/aruljohn/Bible-kjv/master/Books.json"))
    rename = {"Psalms": "Psalm"}                       # match gold's "Psalm 23"
    recs = []
    for name in books:
        data = json.loads(fetch(f"{RAW}/aruljohn/Bible-kjv/master/{name.replace(' ', '')}.json"))
        book = rename.get(data["book"], data["book"])
        for ch in data["chapters"]:
            c = ch["chapter"]
            for v in ch["verses"]:
                recs.append({"reference": f"{book} {c}:{v['verse']}",
                             "text": v["text"].strip(),
                             "section": f"{book} {c}"})
    write("christian", recs)


def build_islamic():
    data = json.loads(fetch(f"{RAW}/risan/quran-json/main/dist/quran_en.json"))
    recs = []
    for surah in data:
        s = surah["id"]
        for v in surah["verses"]:
            recs.append({"reference": f"Qur'an {s}:{v['id']}",
                         "text": v["translation"].strip(),
                         "section": f"Qur'an {s}"})
    write("islamic", recs)


def build_hindu():
    verses = json.loads(fetch(f"{RAW}/gita/gita/master/data/verse.json"))
    trans = json.loads(fetch(f"{RAW}/gita/gita/master/data/translation.json"))
    AUTHOR = "Swami Sivananda"
    eng = {t["verse_id"]: t["description"].strip()
           for t in trans if t["lang"] == "english" and t["authorName"] == AUTHOR}
    recs = []
    for v in verses:
        ref = f"Bhagavad Gita {v['chapter_number']}.{v['verse_number']}"
        recs.append({"reference": ref,
                     "text": eng.get(v["id"], "").strip(),
                     "section": f"Bhagavad Gita {v['chapter_number']}"})
    recs = [r for r in recs if r["text"]]
    write("hindu", recs)


def build_buddhist():
    data = json.loads(fetch(f"{RAW}/iacchus/dhammapada.json/master/dhammapada.json"))
    recs = []
    for _, (nums, text) in sorted(data.items(), key=lambda kv: int(kv[0])):
        lo, hi = min(nums), max(nums)
        ref = f"Dhammapada {lo}" if lo == hi else f"Dhammapada {lo}-{hi}"
        recs.append({"reference": ref,
                     "text": re.sub(r"\s+", " ", text).strip(),
                     "section": "Dhammapada"})
    write("buddhist", recs)


def build_taoist():
    xml = fetch("https://raw.githubusercontent.com/standardebooks/"
                "laozi_tao-te-ching_james-legge/master/src/epub/text/tao-te-ching.xhtml").decode("utf-8")
    recs = []
    for m in re.finditer(r'<section id="chapter-(\d+)"[^>]*>(.*?)</section>', xml, re.S):
        n = int(m.group(1))
        paras = re.findall(r"<p[^>]*>(.*?)</p>", m.group(2), re.S)
        text = " ".join(re.sub(r"<[^>]+>", "", p) for p in paras)
        text = re.sub(r"\s+", " ", text).replace("&#160;", " ").strip()
        if text:
            recs.append({"reference": f"Tao Te Ching {n}", "text": text,
                         "section": f"Tao Te Ching {n}"})
    recs.sort(key=lambda r: int(r["reference"].split()[-1]))
    write("taoist", recs)


if __name__ == "__main__":
    print("Building verse files ...")
    build_christian()
    build_islamic()
    build_hindu()
    build_buddhist()
    build_taoist()
    print("Done -> verses/")
