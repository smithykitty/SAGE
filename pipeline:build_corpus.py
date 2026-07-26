"""
SAGE — corpus builder.

Real run: you supply each tradition's PUBLIC-DOMAIN text as a normalized verse
file (JSONL of {"reference": "...", "text": "..."}), and this windows consecutive
verses into reference-tagged chunks for embedding. The normalized-verse contract
keeps source-specific scraping (Gutenberg/Sacred-Texts/CCEL layouts) out of the
pipeline while guaranteeing every chunk carries locators that match the gold set.

Demo run (`--seed-demo`): synthesizes a self-contained corpus covering every
reference in REFERENCE_MAP, with motif-themed chunk text and some verse-level
splitting, so the index + evaluation harness runs with no downloads.

Chunk schema (JSONL):
    {"chunk_id","tradition","reference","references":[...],"text"}
`references` is the list of component locators in the chunk; the evaluator counts
a chunk as relevant if ANY component overlaps a gold label.

Sources manifest (recommended public-domain editions):
"""
import os
import argparse
import json
from pathlib import Path

from references import parse_ref, SINGLE_UNIT_WORKS
from build_sage_profiles import TRADITIONS
from build_sage_testcases import REFERENCE_MAP, THEMATIC_TRADITIONS

OUT = Path(os.environ.get("SAGE_OUT", "outputs"))

# tradition -> recommended public-domain / openly-licensed source + license note
SOURCES = {
    "hindu":      {"work": "Bhagavad Gita", "edition": "Edwin Arnold / Telang trans.",
                   "source": "Project Gutenberg", "license": "Public domain"},
    "jewish":     {"work": "Tanakh + Pirkei Avot / Talmud excerpts", "edition": "JPS 1917 / Soncino",
                   "source": "Sefaria (CC) / Gutenberg", "license": "Public domain / CC-BY"},
    "islamic":    {"work": "Qur'an", "edition": "Pickthall 1930 / Yusuf Ali",
                   "source": "Project Gutenberg / Sacred-Texts", "license": "Public domain"},
    "buddhist":   {"work": "Dhammapada (+ named suttas)", "edition": "Max Müller / Buddharakkhita",
                   "source": "Sacred-Texts / Access to Insight", "license": "Public domain / CC"},
    "christian":  {"work": "Bible", "edition": "King James Version",
                   "source": "Project Gutenberg", "license": "Public domain"},
    "taoist":     {"work": "Tao Te Ching", "edition": "James Legge / Gia-Fu Feng (PD eds.)",
                   "source": "Sacred-Texts / Gutenberg", "license": "Public domain"},
    "norse":      {"work": "Havamal / Prose Edda", "edition": "Bellows / Brodeur",
                   "source": "Sacred-Texts / Gutenberg", "license": "Public domain"},
    "aboriginal": {"work": "Aboriginal teachings (thematic)", "edition": "Openly-licensed ethnography",
                   "source": "Curated, attributed", "license": "Check per source",
                   "note": "Oral tradition; thematic locators, not chapter/verse."},
    "gandhian":   {"work": "Hind Swaraj; Experiments with Truth", "edition": "Public-domain Gandhi texts",
                   "source": "Gutenberg / Gandhi Heritage Portal", "license": "Public domain"},
    "teresan":    {"work": "Nobel Lecture (1979); thematic", "edition": "Primary sources",
                   "source": "nobelprize.org (lecture)", "license": "Mostly in-copyright",
                   "note": "Most writings still in copyright; use the 1979 Nobel lecture or "
                           "an openly-licensed substitute, or flag the gap on the model card."},
}


def window_chunks(verses, tradition, size=3, stride=2):
    """Group consecutive verses into reference-tagged chunks, without crossing a
    `section` boundary (book+chapter), so chunks stay topically coherent.

    `verses`: list of {"reference","text","section"?} in document order.
    Returns chunk dicts. Component references are preserved for matching.
    """
    # split into runs of consecutive verses sharing a section
    runs, cur, last = [], [], object()
    for v in verses:
        sec = v.get("section")
        if cur and sec != last:
            runs.append(cur); cur = []
        cur.append(v); last = sec
    if cur:
        runs.append(cur)

    chunks = []
    for run in runs:
        i, n = 0, len(run)
        while i < n:
            group = run[i:i + size]
            refs = [v["reference"] for v in group]
            chunks.append({
                "tradition": tradition,
                "reference": _combine(refs),
                "references": refs,
                "text": " ".join(v["text"].strip() for v in group),
            })
            i += stride
    return chunks


def _combine(refs):
    """Build a display locator spanning a group of component refs when possible."""
    if len(refs) == 1:
        return refs[0]
    a, b = parse_ref(refs[0]), parse_ref(refs[-1])
    if a.work == b.work and not a.is_token and not b.is_token:
        if a.chapter == b.chapter and a.chapter is not None:
            sep = ":" if ":" in refs[0] else "."
            head = refs[0].rsplit(sep, 1)[0]
            return f"{head}{sep}{a.v_start}-{b.v_end or b.v_start}"
        if a.chapter is None and b.chapter is None:  # single-unit work
            head = refs[0].rsplit(" ", 1)[0]
            return f"{head} {a.v_start}-{b.v_end or b.v_start}"
    return f"{refs[0]} … {refs[-1]}"


# --------------------------------------------------------------------------- #
# Seed-demo corpus                                                            #
# --------------------------------------------------------------------------- #
MOTIF_TEXT = {
    "forgiveness": "On forgiving those who wrong us, releasing old debts, mercy, and reconciliation.",
    "justice": "On justice and fairness, and the line between righting a wrong and taking revenge.",
    "honesty": "On truthful speech, integrity in small things, and the slow cost of deception.",
    "duty": "On duty and calling, acting rightly, and serving without clinging to the reward.",
    "grief": "On grief and loss, the impermanence of all things, and consolation within sorrow.",
    "courage": "On courage before fear, the acceptance of fate, and facing mortality without flinching.",
    "compassion": "On compassion and charity, service to the suffering, and kindness to the stranger.",
    "desire": "On desire and attachment, restlessness, contentment, and knowing when one has enough.",
    "humility": "On humility and pride, taking the lower place, and yielding rather than boasting.",
    "identity": "On doubt and conscience, meaning, surrender, and the long work of knowing oneself.",
    "relationships": "On loyalty, family and friendship, and the bonds and obligations we owe one another.",
    "general": "On living wisely and well within this tradition's teaching.",
}
MOTIF_ORDER = ["forgiveness", "justice", "honesty", "duty", "grief", "courage",
               "compassion", "desire", "humility", "identity", "relationships"]


def primary_motifs():
    """ref -> (tradition, primary motif): first non-'general' motif it appears under."""
    out = {}
    for trad, motifs in REFERENCE_MAP.items():
        for motif in MOTIF_ORDER + ["general"]:
            for r in motifs.get(motif, []):
                out.setdefault(r, (trad, motif))
    return out


def split_components(ref):
    """Split a range locator into per-verse/per-unit component refs (cap 4)."""
    p = parse_ref(ref)
    if p.is_token or p.v_start is None or p.v_end is None or p.v_end == p.v_start:
        return [ref]
    units = list(range(p.v_start, min(p.v_end, p.v_start + 3) + 1))
    if p.chapter is None and p.work in SINGLE_UNIT_WORKS:           # "Havamal 43-46"
        head = ref.rsplit(" ", 1)[0]
        return [f"{head} {u}" for u in units]
    if p.chapter is not None:                                       # "Matthew 18:21-22"
        head = ref.rsplit(":", 1)[0]
        return [f"{head}:{u}" for u in units]
    return [ref]


def build_seed():
    pm = primary_motifs()
    chunks, cid = [], 0
    for ref, (trad, motif) in sorted(pm.items()):
        tname = TRADITIONS[trad][0]
        flavor = TRADITIONS[trad][2]
        for comp in split_components(ref):
            cid += 1
            chunks.append({
                "chunk_id": f"C{cid:04d}",
                "tradition": trad,
                "reference": comp,
                "references": [comp],
                "text": f"[{tname} — {comp}] {MOTIF_TEXT[motif]} "
                        f"This passage speaks to {flavor}.",
            })
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-demo", action="store_true",
                    help="Write a self-contained seed corpus for offline testing.")
    ap.add_argument("--verses-dir", default=None,
                    help="Dir of <tradition>.jsonl normalized verse files for the real build.")
    ap.add_argument("--size", type=int, default=3)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.seed_demo:
        chunks = build_seed()
        out = Path(args.out or OUT / "sage_corpus.seed.jsonl")
    else:
        if not args.verses_dir:
            raise SystemExit("Provide --verses-dir for the real build, or use --seed-demo.")
        chunks, cid = [], 0
        for trad in TRADITIONS:
            vf = Path(args.verses_dir) / f"{trad}.jsonl"
            if not vf.exists():
                print(f"  (skip {trad}: no {vf.name})"); continue
            verses = [json.loads(l) for l in vf.read_text().splitlines() if l.strip()]
            for ch in window_chunks(verses, trad, args.size, args.stride):
                cid += 1
                ch["chunk_id"] = f"C{cid:04d}"
                chunks.append(ch)
        out = Path(args.out or OUT / "sage_corpus.jsonl")

    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in chunks))
    from collections import Counter
    by_trad = Counter(c["tradition"] for c in chunks)
    print(f"Wrote {len(chunks)} chunks -> {out}")
    print("  per tradition:", dict(sorted(by_trad.items())))
    print(f"  thematic-locator traditions: {sorted(THEMATIC_TRADITIONS)}")


if __name__ == "__main__":
    main()
