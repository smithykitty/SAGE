"""
SAGE — canonical reference model.

Gold retrieval labels and corpus chunks both use canonical locators
("Matthew 18:21-22", "Bhagavad Gita 2.47", "Dhammapada 277-279",
"Tao Te Ching 44", "Havamal 43-46", "Qur'an 2:286", "Pirkei Avot 4:1",
named suttas, and thematic labels for oral/modern traditions).

This module parses a locator into a comparable structure and decides whether two
locators OVERLAP, so a retrieved chunk counts as a hit for a gold label even when
the corpus is chunked at a different granularity (e.g. gold "Dhammapada 277-279"
is satisfied by a chunk tagged "Dhammapada 278").
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

# works whose trailing number is the primary unit (no chapter:verse structure)
SINGLE_UNIT_WORKS = {"tao te ching", "havamal", "dhammapada", "gylfaginning"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))      # drop accents
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def normalize_work(w: str) -> str:
    w = _norm(w)
    w = re.sub(r"\(.*?\)", "", w).strip()        # drop parentheticals e.g. (prose edda)
    w = w.replace("quran", "qur'an")
    return re.sub(r"\s+", " ", w).strip()


@dataclass(frozen=True)
class Ref:
    raw: str
    work: str
    chapter: Optional[int]      # chapter (chapter:verse works) or None
    v_start: Optional[int]      # verse/unit start, or None for whole-chapter
    v_end: Optional[int]
    token: Optional[str]        # set for non-numeric refs (exact-match only)

    @property
    def is_token(self) -> bool:
        return self.token is not None


def parse_ref(raw: str) -> Ref:
    s = _norm(raw)

    # chapter:verse or chapter.verse, optional verse range
    m = re.match(r"^(?P<work>.+?)\s+(?P<chap>\d+)[:.](?P<vs>\d+)(?:-(?P<ve>\d+))?$", s)
    if m:
        work = normalize_work(m.group("work"))
        vs = int(m.group("vs")); ve = int(m.group("ve") or vs)
        return Ref(raw, work, int(m.group("chap")), vs, ve, None)

    # trailing single number or range  ("Tao Te Ching 18-19", "Psalm 23", "Havamal 6")
    m = re.match(r"^(?P<work>.+?)\s+(?P<a>\d+)(?:-(?P<b>\d+))?$", s)
    if m:
        work = normalize_work(m.group("work"))
        a = int(m.group("a")); b = int(m.group("b") or a)
        if work in SINGLE_UNIT_WORKS:
            return Ref(raw, work, None, a, b, None)         # number is the unit
        # otherwise treat as whole-chapter (verses unspecified -> matches any verse)
        return Ref(raw, work, a, None, None, None)

    # non-numeric -> token (suttas, Talmud folios, thematic labels)
    return Ref(raw, normalize_work(s), None, None, None, _norm(raw))


def _ranges_overlap(a0, a1, b0, b1) -> bool:
    return a0 <= b1 and b0 <= a1


def refs_overlap(a: Ref, b: Ref) -> bool:
    """True if locator a and locator b refer to overlapping text."""
    if a.is_token or b.is_token:
        # token vs anything: require exact normalized-raw equality
        return _norm(a.raw) == _norm(b.raw)
    if a.work != b.work:
        return False
    # single-unit works: chapter is None on both; compare unit ranges
    if a.chapter is None and b.chapter is None:
        return _ranges_overlap(a.v_start, a.v_end, b.v_start, b.v_end)
    # chapter:verse works
    if a.chapter != b.chapter:
        return False
    if a.v_start is None or b.v_start is None:
        return True                                   # whole-chapter on either side
    return _ranges_overlap(a.v_start, a.v_end, b.v_start, b.v_end)


def matches_any(chunk_ref: str, gold_refs) -> Optional[str]:
    """Return the gold ref this chunk satisfies, or None."""
    c = parse_ref(chunk_ref)
    for g in gold_refs:
        if refs_overlap(parse_ref(g), c):
            return g
    return None


if __name__ == "__main__":
    # self-test across every reference shape used in the corpus
    from build_sage_testcases import REFERENCE_MAP
    all_refs = sorted({r for m in REFERENCE_MAP.values() for refs in m.values() for r in refs})
    bad = []
    for r in all_refs:
        p = parse_ref(r)
        if not (p.is_token or p.v_start is not None or p.chapter is not None):
            bad.append(r)
    print(f"Parsed {len(all_refs)} distinct references; unparseable: {len(bad)}")
    for r in bad:
        print("   !", r)

    checks = [
        ("Dhammapada 278", "Dhammapada 277-279", True),
        ("Dhammapada 280", "Dhammapada 277-279", False),
        ("Matthew 18:22", "Matthew 18:21-22", True),
        ("Matthew 18:23", "Matthew 18:21-22", False),
        ("Bhagavad Gita 2.55", "Bhagavad Gita 2.55-57", True),
        ("Bhagavad Gita 3.55", "Bhagavad Gita 2.55-57", False),
        ("Tao Te Ching 18", "Tao Te Ching 18-19", True),
        ("Psalm 23", "Psalm 23", True),
        ("Qur'an 2:286", "Quran 2:286", True),
        ("Havamal 44", "Hávamál 43-46", True),
        ("Gylfaginning (Prose Edda) 51", "Gylfaginning 51", True),
        ("Karaniya Metta Sutta (Sn 1.8)", "Karaniya Metta Sutta (Sn 1.8)", True),
        ("Matthew 5:4", "Matthew 18:21-22", False),
    ]
    ok = 0
    for c, g, want in checks:
        got = refs_overlap(parse_ref(c), parse_ref(g))
        flag = "ok" if got == want else "FAIL"
        ok += got == want
        print(f"  [{flag}] overlap({c!r}, {g!r}) = {got} (want {want})")
    print(f"\n{ok}/{len(checks)} overlap checks passed")
