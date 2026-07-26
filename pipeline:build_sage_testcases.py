"""
SAGE: Sacred Alchemy & Guidance Engine
Gold evaluation set — test-case builder (profile x quandary pairings)
--------------------------------------------------------------------
Each of the 100 quandaries is paired with one age-compatible profile to form a
test case. Every case carries the gold RETRIEVAL targets it should surface
(expected_references), looked up per tradition by the quandary's moral motif.

These cases are SAGE's testing split: ~30 profiles and 100 quandaries, each
paired with the ideal passages it should retrieve and an ideal reference
response. This script produces the pairings + ideal passages; the ideal
reference responses are generated in the next step.

Inputs:
    outputs/sage_profiles.json   (the frozen 30 profiles)
    QUANDARY_BANK, TRADITIONS  (imported from build_sage_profiles.py)

Output:
    outputs/sage_testcases.json
    outputs/sage_testcases_preview.csv
"""

import os
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from build_sage_profiles import QUANDARY_BANK, TRADITIONS  # static data, no RNG

OUT = Path(os.environ.get("SAGE_OUT", "outputs"))
SEED = 5002
rng = random.Random(SEED + 1)  # distinct stream from the profile builder

profiles = json.loads((OUT / "sage_profiles.json").read_text())
quandary_by_id = {q[0]: {"quandary_id": q[0], "theme": q[1], "min_age": q[2], "text": q[3]}
                  for q in QUANDARY_BANK}

# --------------------------------------------------------------------------- #
# 1. Theme -> moral motif (collapses ~59 themes onto 11 retrievable motifs)    #
# --------------------------------------------------------------------------- #
THEME_TO_MOTIF = {
    # forgiveness family
    "forgiveness": "forgiveness", "reconciliation": "forgiveness", "mercy": "forgiveness",
    "betrayal": "forgiveness", "repentance": "forgiveness", "regret": "forgiveness",
    # justice
    "justice": "justice", "revenge": "justice", "fairness": "justice",
    # honesty
    "honesty": "honesty", "truth": "honesty", "integrity": "honesty", "gossip": "honesty",
    # duty / calling
    "duty": "duty", "vocation": "duty", "work": "duty", "obedience": "duty",
    "responsibility": "duty", "conscience": "duty", "conviction": "duty",
    # grief / impermanence
    "grief": "grief", "mortality": "grief", "estrangement": "grief", "acceptance": "grief",
    # courage / fate
    "courage": "courage",
    # compassion / service
    "kindness": "compassion", "generosity": "compassion", "charity": "compassion",
    "compassion": "compassion", "service": "compassion", "sacrifice": "compassion",
    "stewardship": "compassion", "caregiving": "compassion",
    # desire / attachment
    "envy": "desire", "gratitude": "desire", "temptation": "desire", "contentment": "desire",
    "wealth": "desire", "ambition": "desire", "windfall": "desire",
    # humility / pride
    "humility": "humility", "pride": "humility",
    # identity / meaning / doubt
    "identity": "identity", "belonging": "identity", "autonomy": "identity",
    "doubt": "identity", "meaning": "identity", "wisdom": "identity",
    "surrender": "identity", "legacy": "identity",
    # relationships / bonds
    "loyalty": "relationships", "judgment": "relationships", "anger": "relationships",
    "promise": "relationships", "parenting": "relationships", "trust": "relationships",
    "marriage": "relationships", "boundaries": "relationships", "displacement": "relationships",
}
MOTIFS = ["forgiveness", "justice", "honesty", "duty", "grief", "courage",
          "compassion", "desire", "humility", "identity", "relationships"]

# --------------------------------------------------------------------------- #
# 2. Reference map: tradition x motif -> canonical retrieval targets           #
# --------------------------------------------------------------------------- #
# Scriptural traditions use canonical locators; oral/modern traditions
# (aboriginal, gandhian, teresan) use named teachings/works (flagged below).
REFERENCE_MAP = {
    "hindu": {  # Bhagavad Gita
        "forgiveness":   ["Bhagavad Gita 16.1-3", "Bhagavad Gita 12.13-14"],
        "justice":       ["Bhagavad Gita 3.35", "Bhagavad Gita 18.47"],
        "honesty":       ["Bhagavad Gita 17.15", "Bhagavad Gita 10.4-5"],
        "duty":          ["Bhagavad Gita 2.47", "Bhagavad Gita 3.19-21"],
        "grief":         ["Bhagavad Gita 2.13", "Bhagavad Gita 2.22-27"],
        "courage":       ["Bhagavad Gita 2.37", "Bhagavad Gita 11.32-33"],
        "compassion":    ["Bhagavad Gita 6.29-32", "Bhagavad Gita 12.13"],
        "desire":        ["Bhagavad Gita 2.62-63", "Bhagavad Gita 2.55-57"],
        "humility":      ["Bhagavad Gita 13.7-11", "Bhagavad Gita 16.1-3"],
        "identity":      ["Bhagavad Gita 2.20", "Bhagavad Gita 18.63"],
        "relationships": ["Bhagavad Gita 1.28-37", "Bhagavad Gita 6.5-6"],
        "general":       ["Bhagavad Gita 2.47", "Bhagavad Gita 2.13"],
    },
    "jewish": {  # Talmud + Tanakh
        "forgiveness":   ["Talmud, Yoma 87a", "Leviticus 19:18"],
        "justice":       ["Deuteronomy 16:20", "Mishnah Sanhedrin 4:5"],
        "honesty":       ["Talmud, Shabbat 31a", "Leviticus 19:11"],
        "duty":          ["Pirkei Avot 2:16", "Micah 6:8"],
        "grief":         ["Job 1:21", "Psalm 23"],
        "courage":       ["Joshua 1:9", "Psalm 27:1"],
        "compassion":    ["Pirkei Avot 1:2", "Leviticus 19:18"],
        "desire":        ["Pirkei Avot 4:1", "Ecclesiastes 5:9-10"],
        "humility":      ["Numbers 12:3", "Micah 6:8"],
        "identity":      ["Genesis 32:24-30", "Pirkei Avot 2:5"],
        "relationships": ["Ruth 1:16-17", "Exodus 20:12"],
        "general":       ["Micah 6:8", "Pirkei Avot 1:14"],
    },
    "islamic": {  # Qur'an
        "forgiveness":   ["Qur'an 24:22", "Qur'an 42:40"],
        "justice":       ["Qur'an 4:135", "Qur'an 16:90"],
        "honesty":       ["Qur'an 33:70-71", "Qur'an 9:119"],
        "duty":          ["Qur'an 2:286", "Qur'an 51:56"],
        "grief":         ["Qur'an 2:155-157", "Qur'an 94:5-6"],
        "courage":       ["Qur'an 3:159", "Qur'an 65:3"],
        "compassion":    ["Qur'an 2:177", "Qur'an 76:8-9"],
        "desire":        ["Qur'an 57:20", "Qur'an 89:27-30"],
        "humility":      ["Qur'an 31:18", "Qur'an 25:63"],
        "identity":      ["Qur'an 2:256", "Qur'an 13:28"],
        "relationships": ["Qur'an 17:23-24", "Qur'an 31:14"],
        "general":       ["Qur'an 2:286", "Qur'an 16:90"],
    },
    "buddhist": {  # Dhammapada + named suttas
        "forgiveness":   ["Dhammapada 3-5", "Dhammapada 223"],
        "justice":       ["Dhammapada 201", "Dhammapada 103-105"],
        "honesty":       ["Dhammapada 224", "Dhammapada 408"],
        "duty":          ["Dhammapada 166", "Dhammapada 276"],
        "grief":         ["Dhammapada 277-279", "Dhammapada 287"],
        "courage":       ["Dhammapada 103", "Dhammapada 380"],
        "compassion":    ["Karaniya Metta Sutta (Sn 1.8)", "Dhammapada 223"],
        "desire":        ["Dhammapada 204", "Dhammapada 251"],
        "humility":      ["Dhammapada 63", "Dhammapada 121-122"],
        "identity":      ["Dhammapada 165", "Kalama Sutta (AN 3.65)"],
        "relationships": ["Sigalovada Sutta (DN 31)", "Dhammapada 197-199"],
        "general":       ["Dhammapada 277-279", "Dhammapada 1-2"],
    },
    "christian": {  # Bible
        "forgiveness":   ["Matthew 18:21-22", "Colossians 3:13"],
        "justice":       ["Micah 6:8", "Romans 12:19-21"],
        "honesty":       ["Ephesians 4:25", "Proverbs 12:22"],
        "duty":          ["Colossians 3:23", "Luke 9:62"],
        "grief":         ["Psalm 34:18", "Matthew 5:4"],
        "courage":       ["Joshua 1:9", "2 Timothy 1:7"],
        "compassion":    ["Luke 10:25-37", "Matthew 25:35-40"],
        "desire":        ["Matthew 6:19-21", "1 Timothy 6:6-10"],
        "humility":      ["Philippians 2:3-4", "Proverbs 16:18"],
        "identity":      ["Mark 9:24", "John 20:24-29"],
        "relationships": ["1 Corinthians 13:4-7", "Ephesians 6:1-4"],
        "general":       ["Micah 6:8", "Matthew 22:37-40"],
    },
    "taoist": {  # Tao Te Ching (by chapter)
        "forgiveness":   ["Tao Te Ching 49", "Tao Te Ching 63"],
        "justice":       ["Tao Te Ching 79", "Tao Te Ching 58"],
        "honesty":       ["Tao Te Ching 81", "Tao Te Ching 8"],
        "duty":          ["Tao Te Ching 37", "Tao Te Ching 2"],
        "grief":         ["Tao Te Ching 16", "Tao Te Ching 50"],
        "courage":       ["Tao Te Ching 67", "Tao Te Ching 73"],
        "compassion":    ["Tao Te Ching 67", "Tao Te Ching 8"],
        "desire":        ["Tao Te Ching 44", "Tao Te Ching 46"],
        "humility":      ["Tao Te Ching 22", "Tao Te Ching 66"],
        "identity":      ["Tao Te Ching 71", "Tao Te Ching 33"],
        "relationships": ["Tao Te Ching 54", "Tao Te Ching 18-19"],
        "general":       ["Tao Te Ching 8", "Tao Te Ching 67"],
    },
    "norse": {  # Havamal (Poetic Edda) + Prose Edda/Gylfaginning
        "forgiveness":   ["Havamal 43-46", "Havamal 121-124"],
        "justice":       ["Havamal 42", "Havamal 64"],
        "honesty":       ["Havamal 124-125", "Havamal 46"],
        "duty":          ["Havamal 76-77", "Gylfaginning (Prose Edda) 51"],
        "grief":         ["Havamal 70-71", "Havamal 76-77"],
        "courage":       ["Havamal 15-16", "Gylfaginning (Prose Edda) 51"],
        "compassion":    ["Havamal 3-4", "Havamal 135"],
        "desire":        ["Havamal 10-11", "Havamal 75"],
        "humility":      ["Havamal 6", "Havamal 27"],
        "identity":      ["Havamal 27-28", "Havamal 57"],
        "relationships": ["Havamal 43-44", "Havamal 119"],
        "general":       ["Havamal 76-77", "Havamal 43-44"],
    },
    "aboriginal": {  # oral teachings — named motifs (thematic, not versified)
        "forgiveness":   ["Kinship law and restitution", "Reciprocity and care for Country"],
        "justice":       ["Customary law (the Dreaming)", "Reciprocity and obligation"],
        "honesty":       ["Truth-telling within kinship", "The Dreaming (Tjukurpa)"],
        "duty":          ["Obligations of kinship", "Caring for Country"],
        "grief":         ["Sorry business and mourning law", "Connection to ancestors and Country"],
        "courage":       ["Initiation and law", "Ancestral law (the Dreaming)"],
        "compassion":    ["Reciprocity and sharing", "Caring for Country and community"],
        "desire":        ["Sharing economy and non-accumulation", "Care for Country over possession"],
        "humility":      ["Place within kinship and Country", "Respect for Elders"],
        "identity":      ["Belonging to Country and kin", "The Dreaming (Tjukurpa)"],
        "relationships": ["Kinship and skin systems", "Obligations to Elders and kin"],
        "general":       ["The Dreaming (Tjukurpa)", "Kinship and care for Country"],
    },
    "gandhian": {  # Gandhi's writings — works/concepts (public-domain texts)
        "forgiveness":   ["Ahimsa (Hind Swaraj)", "Forgiveness as the attribute of the strong"],
        "justice":       ["Satyagraha (Satyagraha in South Africa)", "Hind Swaraj, ch. on true civilization"],
        "honesty":       ["Satya (The Story of My Experiments with Truth)", "Truth as God"],
        "duty":          ["Anasakti Yoga (Gita According to Gandhi)", "Swadharma and selfless action"],
        "grief":         ["Self-suffering / tapasya (Young India)", "Experiments with Truth, autobiography"],
        "courage":       ["Non-violence of the strong (Young India)", "Satyagraha as soul-force"],
        "compassion":    ["Sarvodaya (welfare of all)", "Daridranarayana (service to the poor)"],
        "desire":        ["Aparigraha (non-possession)", "Voluntary simplicity (Experiments with Truth)"],
        "humility":      ["Humility (Experiments with Truth)", "Reduction of self to zero"],
        "identity":      ["Conscience over authority (Hind Swaraj)", "Inner voice / antaryamin"],
        "relationships": ["Brahmacharya and family (autobiography)", "Sarvodaya community"],
        "general":       ["Satya and Ahimsa", "The Story of My Experiments with Truth"],
    },
    "teresan": {  # Mother Teresa — themes/sources (note: largely in-copyright)
        "forgiveness":   ["Works of mercy (Missionaries of Charity)", "Nobel Lecture (1979)"],
        "justice":       ["Service to the poorest of the poor", "Nobel Lecture (1979)"],
        "honesty":       ["Sincerity in small things", "Works of mercy"],
        "duty":          ["Vocation of charity (Missionaries of Charity)", "Wholehearted service"],
        "grief":         ["Accompanying the dying (Nirmal Hriday)", "Consolation in suffering"],
        "courage":       ["Faithfulness in hardship", "Service amid darkness"],
        "compassion":    ["Love in action (Nobel Lecture, 1979)", "Care for the dying and destitute"],
        "desire":        ["Holy poverty / simplicity", "Detachment for the sake of love"],
        "humility":      ["Humility and small acts of love", "Works of mercy"],
        "identity":      ["Serving Christ in the distressing disguise of the poor", "Vocation of charity"],
        "relationships": ["Love begins at home", "Tenderness toward the unwanted"],
        "general":       ["Love in action (Nobel Lecture, 1979)", "Works of mercy"],
    },
}

# traditions whose references are thematic rather than canonical locators
THEMATIC_TRADITIONS = {"aboriginal", "gandhian", "teresan"}


def references_for(tradition_key: str, motif: str):
    table = REFERENCE_MAP[tradition_key]
    return table.get(motif, table["general"])


# --------------------------------------------------------------------------- #
# 3. Assign each quandary to one age-compatible profile, balanced ~3-4 each    #
# --------------------------------------------------------------------------- #
def assign(profiles, quandaries):
    load = defaultdict(int)
    order = list(profiles)
    rng.shuffle(order)  # randomized tie-break, seeded
    pairs = []

    # most-constrained (highest min_age) first
    for q in sorted(quandaries, key=lambda x: x["min_age"], reverse=True):
        eligible = [p for p in order if p["age"] >= q["min_age"]]
        if not eligible:
            raise RuntimeError(f"No profile old enough for {q['quandary_id']} (min_age {q['min_age']})")
        # prefer least-loaded; keep a soft cap of 4
        eligible.sort(key=lambda p: load[p["profile_id"]])
        under_cap = [p for p in eligible if load[p["profile_id"]] < 4]
        chosen = (under_cap or eligible)[0]
        load[chosen["profile_id"]] += 1
        pairs.append((chosen, q))
    return pairs


def build_cases():
    quandaries = list(quandary_by_id.values())
    pairs = assign(profiles, quandaries)
    # stable order by quandary id for readability
    pairs.sort(key=lambda pr: pr[1]["quandary_id"])

    cases = []
    for i, (p, q) in enumerate(pairs, start=1):
        motif = THEME_TO_MOTIF.get(q["theme"], "duty")
        expected = {t: references_for(t, motif) for t in p["traditions"]}
        flat = [r for refs in expected.values() for r in refs]
        thematic = sorted(t for t in p["traditions"] if t in THEMATIC_TRADITIONS)
        cases.append({
            "case_id": f"T{i:03d}",
            "profile_id": p["profile_id"],
            "age": p["age"],
            "gender": p["gender"],
            "relationship": p["relationship"],
            "traditions": p["traditions"],
            "tradition_names": p["tradition_names"],
            "tradition_type": p["tradition_type"],
            "quandary_id": q["quandary_id"],
            "quandary_theme": q["theme"],
            "motif": motif,
            "quandary": q["text"],
            "expected_references": expected,
            "expected_references_flat": flat,
            "thematic_reference_traditions": thematic,
        })
    return cases


if __name__ == "__main__":
    cases = build_cases()

    (OUT / "sage_testcases.json").write_text(json.dumps(cases, indent=2, ensure_ascii=False))

    # flat CSV preview
    with (OUT / "sage_testcases_preview.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "profile_id", "age", "gender", "relationship",
                    "traditions", "quandary_id", "theme", "motif",
                    "expected_references", "quandary"])
        for c in cases:
            w.writerow([c["case_id"], c["profile_id"], c["age"], c["gender"],
                        c["relationship"], "+".join(c["traditions"]),
                        c["quandary_id"], c["quandary_theme"], c["motif"],
                        " | ".join(c["expected_references_flat"]), c["quandary"]])

    # ---- validation + summary --------------------------------------------
    assert len(cases) == 100, "expected 100 test cases"
    assert len({c["quandary_id"] for c in cases}) == 100, "each quandary used once"
    for c in cases:
        q = quandary_by_id[c["quandary_id"]]
        assert c["age"] >= q["min_age"], f"age violation in {c['case_id']}"
        assert all(c["expected_references"].get(t) for t in c["traditions"]), \
            f"missing references in {c['case_id']}"

    usage = Counter(c["profile_id"] for c in cases)
    minors = [c for c in cases if c["age"] < 18]
    print(f"Built {len(cases)} test cases (seed={SEED+1})\n")
    print("Cases per profile  : min", min(usage.values()), "max", max(usage.values()),
          "->", dict(sorted(Counter(usage.values()).items())), "(count: #profiles)")
    print("Single vs dual      :", dict(Counter(c["tradition_type"] for c in cases)))
    print("Motif coverage      :", dict(sorted(Counter(c["motif"] for c in cases).items())))
    print("Minor cases (<18)   :", len(minors),
          "-> all Tier-A:", all(quandary_by_id[c["quandary_id"]]["min_age"] <= 15 for c in minors))
    print("Thematic-ref cases  :", sum(1 for c in cases if c["thematic_reference_traditions"]),
          "(use named teachings rather than chapter/verse)")
    print("\nSample test case:")
    print(json.dumps(cases[2], indent=2, ensure_ascii=False))
