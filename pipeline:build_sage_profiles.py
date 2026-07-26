"""
SAGE: Sacred Alchemy & Guidance Engine
Gold evaluation set — profile + quandary builder
--------------------------------------------------
Generates the ~30 synthetic profiles that anchor SAGE's testing split.

Each profile is the structured inference input SAGE expects:
    - one or more traditions
    - the seeker's relationship to those traditions (seeker -> disciple)
    - a free-text moral quandary

Design:
    - 10 single-tradition profiles (each of the 10 traditions, exclusively)
    - 20 dual-tradition profiles, each an "unlikely" pairing chosen to surface
      cross-tradition tension (the project's central contribution)
    - ages random 11-111; genders {male, female, nonbinary, transgender}
    - relationship spans the seeker -> novice -> practitioner -> disciple range
    - quandaries are first-person rewrites of debate prompts from
      https://discussionpostwriter.ai/blog/provoking-ethical-questions/ ,
      adapted to spiritual-counsel framing and tagged with a minimum age so
      minors only ever receive age-appropriate dilemmas.

Reproducible: everything is driven by SEED so the set can be frozen.
"""

import os
import json
import random
from pathlib import Path

SEED = 5002  # course number, for fun + reproducibility
rng = random.Random(SEED)

OUT = Path(os.environ.get("SAGE_OUT", "outputs"))
OUT.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# 1. Traditions (the ten SAGE traditions)                              #
# --------------------------------------------------------------------------- #
# key -> (display name, canonical source text, moral vocabulary)
TRADITIONS = {
    "hindu":        ("Hinduism (Vedas / Bhagavad Gita)", "Bhagavad Gita",  "duty and right action (dharma)"),
    "jewish":       ("Judaism (Talmud)",                 "Talmud",         "justice and obligation to others"),
    "islamic":      ("Islam (Qur'an)",                   "Qur'an",         "submission and mercy"),
    "buddhist":     ("Buddhism (Dharma)",                "Dhammapada",     "suffering as impermanence"),
    "christian":    ("Christianity (Bible)",             "Bible",          "forgiveness and grace"),
    "taoist":       ("Taoism (Tao Te Ching)",            "Tao Te Ching",   "yielding and non-striving (wu wei)"),
    "norse":        ("Norse (Prose Edda)",               "Prose Edda",     "courage in the face of fate"),
    "aboriginal":   ("Aboriginal teachings",             "Aboriginal teachings", "kinship and reciprocal care for community and land"),
    "gandhian":     ("Gandhian thought",                 "Gandhi",         "nonviolence (ahimsa, satyagraha)"),
    "teresan":      ("Missionaries of Charity (Mother Teresa)", "Mother Teresa", "compassionate service to the suffering"),
}

# 20 deliberately "unlikely" pairings: cross-cultural / philosophically distant,
# avoiding the obvious neighbours (two Abrahamic faiths, Gandhi+Gita,
# Buddhist+Taoist, Gandhi+Mother Teresa, etc.).
UNLIKELY_PAIRS = [
    ("norse", "teresan"),       # warrior fatalism vs. tender service
    ("islamic", "taoist"),      # active submission vs. effortless yielding
    ("hindu", "norse"),         # dharma-duty vs. fate-courage
    ("jewish", "buddhist"),     # clinging to justice vs. non-attachment
    ("christian", "norse"),     # turn the other cheek vs. honor and fate
    ("taoist", "jewish"),       # formless flow vs. detailed law
    ("aboriginal", "islamic"),  # immanent kinship vs. transcendent submission
    ("buddhist", "teresan"),    # no-self vs. love of the suffering person
    ("gandhian", "norse"),      # ahimsa vs. martial valor
    ("hindu", "teresan"),       # duty/hierarchy vs. service to the outcast
    ("taoist", "gandhian"),     # wu wei vs. active nonviolent resistance
    ("christian", "buddhist"),  # grace vs. self-effort / karma
    ("islamic", "norse"),       # submission and mercy vs. honor and fate
    ("jewish", "aboriginal"),   # text-covenant vs. land-covenant
    ("norse", "buddhist"),      # wyrd / fate vs. karmic causation
    ("christian", "taoist"),    # grace vs. non-striving
    ("hindu", "taoist"),        # cosmic order (dharma) vs. the Tao
    ("gandhian", "jewish"),     # satyagraha / truth-force vs. covenant justice
    ("buddhist", "aboriginal"), # impermanence / no-self vs. enduring kinship
    ("teresan", "jewish"),      # charity vs. tzedakah / obligation
]
assert len(UNLIKELY_PAIRS) == 20
assert len(set(map(frozenset, UNLIKELY_PAIRS))) == 20, "duplicate pairing"

# --------------------------------------------------------------------------- #
# 2. Relationship spectrum (seeker -> disciple)                               #
# --------------------------------------------------------------------------- #
RELATIONSHIPS = [
    (1, "seeker",       "exploring, not committed; curious and questioning"),
    (2, "novice",       "recently committed; learning the basics of practice"),
    (3, "practitioner", "established, regular practice and study"),
    (4, "disciple",     "deeply devoted; advanced, mentors or teaches others"),
]

GENDERS = ["male", "female", "nonbinary", "transgender"]

# --------------------------------------------------------------------------- #
# 3. Quandary bank — first-person rewrites of debate prompts, theme + min_age #
# --------------------------------------------------------------------------- #
# min_age gates which quandaries a profile may receive, so minors (11-17) only
# get age-appropriate dilemmas. Themes echo SAGE's recurring set
# (forgiveness, duty, grief, honesty, vocation) plus a few more.
QUANDARY_BANK = [
    # ===== Tier A: universally eligible, age-neutral wording (min_age 11) ===
    ("Q001", "honesty",      11, "A close friend asked me to cover for something they did. Telling the truth would get them in real trouble, but staying silent feels like a lie. What should I do?"),
    ("Q002", "integrity",    11, "Someone close to me is getting ahead by cheating, and they don't think it's a big deal. Calling it out feels right, but it would cost me the friendship. How do I weigh loyalty against honesty?"),
    ("Q003", "grief",        11, "Someone I loved deeply died recently, and I feel angry — at fate, at heaven, at God, I'm not even sure. Is it wrong to feel this way, and how do I carry it?"),
    ("Q004", "fairness",     11, "Some people around me get help and opportunities that others don't. It feels unfair, but maybe they need it more. How should I think about fairness here?"),
    ("Q005", "courage",      11, "Everyone around me is going along with something I believe is wrong, and standing apart would make me an outsider. Should I speak up even if I stand alone?"),
    ("Q006", "kindness",     11, "I pass someone who plainly needs help nearly every day. I'm only one person, and the need is so much bigger than me. Do I have a real responsibility to stop?"),
    ("Q007", "honesty",      11, "Is it ever okay to tell a small lie to keep someone from being hurt? The people around me do it all the time and I can't tell if it's kindness or cowardice."),
    ("Q008", "identity",     11, "There are parts of who I am that I keep hidden from people around me because I'm afraid of how they'd react. Is keeping them private a kind of dishonesty?"),
    ("Q009", "loyalty",      11, "A friend told me a secret, but keeping it might let someone else get hurt. Do I protect my friend's trust or protect the person at risk?"),
    ("Q010", "honesty",      11, "I found something valuable that someone clearly lost. No one would ever know if I kept it. Why should I return it, and what does that say about who I want to be?"),
    ("Q011", "integrity",    11, "I was praised for something I didn't really do on my own. Owning up would be embarrassing and cost me the credit. Is staying quiet a kind of lie?"),
    ("Q012", "judgment",     11, "Someone who wronged me before has clearly changed. Part of me still wants to hold it against them. How long should a past mistake define a person?"),
    ("Q013", "envy",         11, "I keep resenting someone for the good things that come easily to them. The comparison is eating at me. How do I let it go?"),
    ("Q014", "anger",        11, "Someone embarrassed me in front of others and I badly want to get back at them. Is wanting that wrong, and what do I do with the feeling?"),
    ("Q015", "gratitude",    11, "I have a lot, and yet I always seem to want more. Is that restlessness wrong, or just human — and how do I find contentment?"),
    ("Q016", "forgiveness",  11, "A close friend broke my trust. Everyone says to forgive and move on, but I don't want to be a pushover. Can I forgive without letting them hurt me again?"),
    ("Q017", "truth",        11, "I know someone broke a rule, but they did it for what they thought was a good reason. Do I report it, or is there room for mercy?"),
    ("Q018", "belonging",    11, "My group leaves someone out, and going against that would risk my own place. Do I speak up for the person being excluded even if it costs me?"),
    ("Q019", "conscience",   11, "Everyone around me is passing along something private and unkind about another person. Joining in is easy; refusing makes me stand out. What's the right move?"),
    ("Q020", "promise",      11, "I made a promise that I now think was wrong to make. Do I keep my word, or break it to do what's right?"),
    ("Q021", "generosity",   11, "I have more than someone who has very little. Nothing forces me to share. What, if anything, do I actually owe them?"),
    ("Q022", "mercy",        11, "Someone who was unkind to me before is now the one struggling. Do I help them, or is it fair to let them manage on their own?"),
    ("Q023", "temptation",   11, "There's a shortcut that would make things much easier for me, but it bends the rules a little. Where's the line between clever and dishonest?"),
    ("Q024", "humility",     11, "I turned out to be right when others were wrong. I want to feel proud, but I don't want to be arrogant about it. How do I hold being right gracefully?"),
    ("Q025", "obedience",    11, "Someone in charge told me to do something that feels wrong to me. Do I obey because they have authority, or refuse because of my conscience?"),
    ("Q026", "contentment",  11, "Almost everyone around me seems to have more than I do. How do I make peace with my own portion without bitterness?"),

    # ===== Tier B: adolescent / young-adult dilemmas (min_age 16) ===========
    ("Q027", "forgiveness",  16, "Someone I trusted betrayed me badly. Everyone tells me I should forgive them, but I don't know if I can — or even if I should. What does forgiveness actually require of me?"),
    ("Q028", "justice",      16, "I was wronged, and I now have a chance to get even. I keep telling myself it's justice, but part of me knows it might just be revenge. How do I tell the difference?"),
    ("Q029", "duty",         16, "My family expects me to carry on a tradition I'm no longer sure I believe in. Do I owe them obedience, or do I owe myself honesty?"),
    ("Q030", "identity",     16, "I've been living a kind of double life to keep peace with my family. The longer it goes, the heavier it gets. How long can I keep dividing myself like this?"),
    ("Q031", "conscience",   16, "I witnessed something wrong, and there's quiet pressure on me to stay silent about it. Do I speak up knowing it will turn people against me?"),
    ("Q032", "loyalty",      16, "A friend is asking me to lie for them, and this time it could have real consequences for someone else. How far does loyalty go before it becomes complicity?"),
    ("Q033", "autonomy",     16, "I'm drawn to a path my faith community clearly disapproves of. Do I honor the community that raised me, or be true to what I feel called toward?"),
    ("Q034", "reconciliation",16, "I'm estranged from a family member and neither of us will reach out. Is making the first move weakness, or the braver thing?"),
    ("Q035", "doubt",        16, "I'm questioning the faith I was raised in, and it scares me. Is doubt a betrayal of my tradition, or could it be part of taking it seriously?"),
    ("Q036", "responsibility",16, "I caused harm that I could probably hide. Owning it would cost me a lot. Is confession worth the price when no one would otherwise know?"),
    ("Q037", "courage",      16, "I believe something most people around me don't, and saying it out loud could cost me friends. Is silence keeping the peace, or just cowardice?"),
    ("Q038", "honesty",      16, "I'm caught between protecting someone I care about and telling the truth in a matter that's serious. Which loyalty comes first?"),
    ("Q039", "temptation",   16, "I'm drawn to something exciting that I could only have by deceiving someone who trusts me. How do I weigh my own desire against their trust?"),
    ("Q040", "judgment",     16, "I keep judging someone harshly for choices I don't really understand. How do I tell the difference between moral clarity and plain prejudice?"),

    # ===== Tier C: adult dilemmas (min_age 18) =============================
    ("Q041", "vocation",     18, "I've been offered a prestigious, well-paid job that quietly conflicts with my deepest values. Do I take it and tell myself I'll do good from the inside, or walk away?"),
    ("Q042", "honesty",      18, "Someone I love is dying and keeps asking me a question I could answer honestly or answer gently. Is a comforting half-truth ever the more loving choice?"),
    ("Q043", "responsibility",18, "My work supports my family but I've come to believe it causes real harm in the world. How do I weigh providing for the people I love against the cost to others?"),
    ("Q044", "mercy",        18, "A person who hurt my family years ago is now suffering and alone, and only I am in a position to help them. Does mercy ask me to, even when justice says they don't deserve it?"),
    ("Q045", "work",         18, "I work for an organization whose values I've come to reject. Do I stay and try to change it from within, or is staying its own kind of compromise?"),
    ("Q046", "conscience",   18, "I've discovered serious wrongdoing where I work. Reporting it could end careers, maybe my own. Is speaking up an act of integrity or just self-destruction?"),
    ("Q047", "wealth",       18, "I have more than I need while others go without. How much of what I've earned am I actually obligated to give away?"),
    ("Q048", "charity",      18, "Day after day I pass someone asking for help, and I never know whether stopping helps or just eases my own conscience. What does real charity ask of me here?"),
    ("Q049", "compassion",   18, "Someone I love is caught in addiction. I can't tell anymore where support ends and enabling begins. How do I love them without losing myself?"),
    ("Q050", "autonomy",     18, "Someone I love wants to refuse further treatment and let their suffering end. Everything in me wants them to fight. Do I honor their wishes or my own grief?"),
    ("Q051", "forgiveness",  18, "I'm wrestling with whether to forgive a parent who hurt me. They may never change. Could forgiving them be less about them and more about my own freedom?"),
    ("Q052", "parenting",    18, "There are painful truths about the world, and about our family, that a child in my care will eventually face. How honest should I be, and when?"),
    ("Q053", "trust",        18, "I'm responsible for someone and I could watch over them closely or give them room to make their own mistakes. Where's the line between care and control?"),
    ("Q054", "marriage",     18, "A bond that once meant everything has grown hollow. Do I stay out of duty and the promise I made, or leave in honesty about what's gone?"),
    ("Q055", "conscience",   18, "I've been asked to carry out a policy I believe is unethical. Do I follow the role I agreed to, or refuse and accept the fallout?"),
    ("Q056", "truth",        18, "I've learned something damning about a person I deeply admired. Exposing it would shatter how others see them. Do they deserve that, and do the others deserve to know?"),
    ("Q057", "service",      18, "I feel pulled to give myself to others, yet my own life feels unfinished and unsteady. Do I have to have my house in order before I can serve?"),
    ("Q058", "stewardship",  18, "My everyday habits quietly harm the earth, and changing them would cost me real comfort and money. How much am I obligated to sacrifice for something so diffuse?"),
    ("Q059", "conviction",   18, "I keep wondering whether it's right for me to consume and use animals the way I do, given what I claim to believe about compassion. Am I living honestly?"),
    ("Q060", "ambition",     18, "I'm chasing a kind of success that everyone admires, but I'm no longer sure my soul actually wants it. How do I tell the difference between calling and conditioning?"),
    ("Q061", "loyalty",      18, "A close friend did something seriously wrong. Standing by them feels like loyalty; it also feels like condoning it. What does true friendship ask of me now?"),
    ("Q062", "integrity",    18, "There's a chance to bend one rule to bring about a clearly good outcome. Do the ends justify it, or does breaking faith with the rule cost more than it's worth?"),
    ("Q063", "justice",      18, "I could pursue justice against someone who wronged me, but doing so would also harm people who are innocent. How do I weigh being made right against the harm it spreads?"),
    ("Q064", "honesty",      18, "Keeping a particular secret protects me but quietly wrongs someone else. Is my silence self-preservation, or is it a betrayal I'm dressing up as discretion?"),
    ("Q065", "pride",        18, "I'd have to admit publicly that I was wrong, and it would cost me standing I've worked hard for. Is swallowing my pride humility, or just humiliation?"),
    ("Q066", "sacrifice",    18, "I could give up something I love for someone who needs it more than I do. Nothing requires it of me. When does generosity become genuine sacrifice?"),
    ("Q067", "boundaries",   18, "A relative leans on me so heavily that it's draining me. Stepping back feels selfish, but staying is wearing me down. Is a boundary a failure of love?"),
    ("Q068", "fairness",     18, "I've benefited from advantages others around me never had. I didn't choose them, but I did keep them. What, in justice, do I owe?"),
    ("Q069", "revenge",      18, "Everyone tells me I'm owed payback for what was done to me. Letting it go feels like weakness. Is releasing the debt strength or surrender?"),
    ("Q070", "doubt",        18, "My prayers and practice have started to feel empty, like going through the motions. Do I keep showing up in hope it returns, or is that just self-deception?"),
    ("Q071", "trust",        18, "Someone betrayed me once and now wants back in. Trusting again could be foolish — or it could be grace. How do I know which?"),
    ("Q072", "displacement", 18, "I feel torn between the needs of my own community and the needs of a stranger from far away. Is it wrong to put my own people first?"),
    ("Q073", "windfall",     18, "Money has come to me, but it traces back to something I find questionable. Keeping it would help my family. Does where it came from stain what I'd do with it?"),
    ("Q074", "gossip",       18, "I know of someone's serious failing. Speaking up might warn others who could be hurt, but it would also expose and shame them. Where does the duty lie?"),
    ("Q075", "humility",     18, "I've always been the one who gives and provides, and now I'm the one who needs help. Accepting it feels like failure. Why is receiving so much harder than giving?"),
    ("Q076", "temptation",   18, "There's a real chance to get ahead by quietly compromising a principle I hold. No one would know but me. Is a private compromise still a compromise?"),
    ("Q077", "reconciliation",18, "I could make the first move toward someone who wronged me and never apologized. Why should I be the one to bend — and would doing so free me or diminish me?"),

    # ===== Tier D: midlife and later-life dilemmas (min_age 25+) ============
    ("Q078", "duty",         25, "I'm pulled between caring for an aging parent and a calling I feel I'm meant to pursue. Both feel like sacred duties and I cannot do both fully. How do I choose?"),
    ("Q079", "vocation",     25, "I could leave a stable, secure life for uncertain work that feels far more meaningful. Is choosing meaning over security brave or just reckless?"),
    ("Q080", "marriage",     25, "I'm being asked to commit fully to someone despite real doubts I can't quite name. Do I trust the doubts or trust the love?"),
    ("Q081", "parenting",    28, "I want to raise my child within my own tradition, but I also want them to choose freely. Is passing on my faith a gift or an imposition?"),
    ("Q082", "vocation",     30, "I've spent years building something I no longer believe in. Walking away would waste all of it and disrupt people who depend on me. Is it ever too late to change course honestly?"),
    ("Q083", "reconciliation",30, "A sibling and I haven't spoken in years, and the silence has hardened into habit. Someone has to bend first. Why shouldn't it be me?"),
    ("Q084", "legacy",       30, "I've reached a point where I'm asking what I actually want to have stood for — and whether the way I'm living now reflects it at all. Where do I even begin?"),
    ("Q085", "forgiveness",  35, "I've carried resentment toward someone for most of my adult life, and they will never apologize. They may never even know. Can I let it go for my own sake without it being a kind of surrender?"),
    ("Q086", "betrayal",     35, "A partner was unfaithful, and I'm torn between the work of rebuilding and the dignity of leaving. How do I tell whether staying is love or fear?"),
    ("Q087", "ambition",     35, "Success came, but it cost me the people I love. Now I have what I chased and not who I cherished. How do I reorder a life I built backwards?"),
    ("Q088", "grief",        40, "Someone central to my life is gone, and the faith that used to comfort me now feels hollow. Is doubt a betrayal of my tradition, or part of it?"),
    ("Q089", "mortality",    40, "I'm beginning to feel my own decline, and I keep counting the things I never did. How do I make peace with a life that's more behind me than ahead?"),
    ("Q090", "estrangement", 40, "An adult child has cut me off, and I don't fully understand why. Do I keep reaching out and risk more rejection, or honor the distance they've asked for?"),
    ("Q091", "regret",       45, "A choice I made decades ago still haunts me. I've changed since, but the harm was real. How do I forgive myself for something I can't undo?"),
    ("Q092", "caregiving",   45, "Caring for a dying spouse is slowly breaking me, and I feel guilty even admitting it. Is it a betrayal of love to say I need help?"),
    ("Q093", "legacy",       50, "Looking back, I made a serious choice that hurt people, and I've changed since. Can a person who did real wrong still be considered good, and how do I make peace with my past?"),
    ("Q094", "fairness",     50, "I have to divide what I've built among people who will each feel it's unfair. There may be no truly even answer. How do I act justly when someone will be hurt either way?"),
    ("Q095", "meaning",      55, "The work that gave my days their shape is over, and my sense of purpose left with it. Who am I now, and how do I begin again?"),
    ("Q096", "repentance",   55, "I want to make amends to someone I wronged long ago, but reopening it might serve me more than them. Do I have the right to seek peace at their expense?"),
    ("Q097", "mortality",    60, "I want to face my own death without fear, but I don't know how. What does my tradition ask of me in meeting the end with grace?"),
    ("Q098", "wisdom",       60, "I've learned hard lessons I could pass on, but unasked-for advice often does more harm than good. When do I speak, and when do I hold my peace?"),
    ("Q099", "surrender",    65, "I keep trying to steer the choices of people I love, and it's straining us. How do I let go of control without feeling I've abandoned them?"),
    ("Q100", "acceptance",   70, "My life didn't unfold the way I once hoped. How do I make genuine peace with that, rather than just resigning myself to it?"),
]

# convenience views
THEME_BY_ID = {q[0]: q[1] for q in QUANDARY_BANK}


def pick_quandary(age: int) -> dict:
    """Return a quandary appropriate to the profile's age."""
    eligible = [q for q in QUANDARY_BANK if q[2] <= age]
    qid, theme, min_age, text = rng.choice(eligible)
    return {"quandary_id": qid, "quandary_theme": theme, "quandary": text}


# --------------------------------------------------------------------------- #
# 4. Build the 30 profiles                                                    #
# --------------------------------------------------------------------------- #
def make_demographics(n: int):
    """Reproducible age / gender / relationship draws spread across the ranges."""
    ages = [rng.randint(11, 111) for _ in range(n)]

    # balanced-ish gender + relationship coverage, then shuffled
    genders = [GENDERS[i % len(GENDERS)] for i in range(n)]
    rels    = [RELATIONSHIPS[i % len(RELATIONSHIPS)] for i in range(n)]
    rng.shuffle(genders)
    rng.shuffle(rels)
    return ages, genders, rels


def tradition_record(keys):
    names = [TRADITIONS[k][0] for k in keys]
    return {
        "traditions": list(keys),
        "tradition_key": "+".join(keys),          # the "concatenation"
        "tradition_names": names,
        "tradition_type": "single" if len(keys) == 1 else "dual_unlikely",
    }


def build():
    profiles = []
    ages, genders, rels = make_demographics(30)

    # 10 single-tradition profiles (one per tradition, exclusively)
    single_keys = [[k] for k in TRADITIONS.keys()]
    # 20 dual-tradition profiles (unlikely pairings)
    dual_keys = [list(p) for p in UNLIKELY_PAIRS]
    all_keys = single_keys + dual_keys           # 30 total

    for i, keys in enumerate(all_keys):
        age = ages[i]
        level, rel_name, rel_desc = rels[i]
        # minors should not be cast as advanced "disciples"; cap relationship
        if age < 16 and level > 2:
            level, rel_name, rel_desc = RELATIONSHIPS[rng.choice([0, 1])]

        prof = {"profile_id": f"P{i+1:02d}", "age": age, "gender": genders[i]}
        prof.update(tradition_record(keys))
        prof.update({
            "relationship": rel_name,
            "relationship_level": level,
            "relationship_desc": rel_desc,
        })
        prof.update(pick_quandary(age))
        profiles.append(prof)

    return profiles


if __name__ == "__main__":
    profiles = build()

    # write outputs
    (OUT / "sage_profiles.json").write_text(json.dumps(profiles, indent=2, ensure_ascii=False))
    (OUT / "sage_quandary_bank.json").write_text(json.dumps(
        [{"quandary_id": q[0], "theme": q[1], "min_age": q[2], "quandary": q[3]} for q in QUANDARY_BANK],
        indent=2, ensure_ascii=False))

    # quick provenance / sanity summary
    from collections import Counter
    print(f"Built {len(profiles)} profiles (seed={SEED})\n")
    print("Genders     :", dict(Counter(p['gender'] for p in profiles)))
    print("Relationship:", dict(Counter(p['relationship'] for p in profiles)))
    print("Type        :", dict(Counter(p['tradition_type'] for p in profiles)))
    print("Age range   :", min(p['age'] for p in profiles), "-", max(p['age'] for p in profiles))
    minors = [p for p in profiles if p['age'] < 18]
    print(f"Minors (<18): {len(minors)} -> themes:",
          dict(Counter(p['quandary_theme'] for p in minors)))

    print(f"\nQuandary bank: {len(QUANDARY_BANK)} items")
    print("  min_age tiers:", dict(sorted(Counter(q[2] for q in QUANDARY_BANK).items())))
    print("  distinct themes:", len(set(q[1] for q in QUANDARY_BANK)))
    print("  eligible for an 11-yo:", sum(1 for q in QUANDARY_BANK if q[2] <= 11),
          "| for a 15-yo:", sum(1 for q in QUANDARY_BANK if q[2] <= 15))
    assert len(QUANDARY_BANK) == 100, "bank must have 100 items"
    assert len({q[0] for q in QUANDARY_BANK}) == 100, "duplicate quandary id"
