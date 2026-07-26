---
license: apache-2.0
base_model: Qwen/Qwen2.5-7B-Instruct
pipeline_tag: text-generation
tags:
  - rag
  - retrieval-augmented-generation
  - religion
  - ethics
language:
  - en
---
![SAGE Universal Guidance](images/SAGE%20Universal%20Guidance.png)

# SAGE: Sacred Alchemy & Guidance Engine

SAGE is a retrieval-augmented generation (RAG) pipeline that offers **non-prescriptive moral and spiritual reflection grounded in the public-domain scriptures of a seeker's own tradition(s)**. It is built on [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) as the generator, with tradition-filtered dense retrieval over a five-tradition corpus of ~38K verses.

---

## Introduction

People routinely bring moral and existential quandaries — forgiveness, duty, grief, honesty, vocation — to the wisdom of their religious traditions, but a general-purpose LLM is a poor guide here: asked to cite scripture, it frequently **fabricates plausible-sounding verses**, misattributes them, or defaults to a [documented Western-Christian and anti-Muslim skew](https://arxiv.org/abs/2101.05783) because that content dominates pretraining. Fabricated or misattributed scripture is not a harmless error in this domain — it can distort a person's relationship with their own faith. SAGE addresses this by keeping the scripture **outside the model's weights**: it retrieves real passages from a curated, public-domain corpus, filters them to the seeker's declared tradition(s), and asks the generator to reflect only on what it was handed, citing each passage by name. On a hand-built evaluation set of 100 profile–quandary test cases, this moved the generator from citing plausible-but-off-topic verses recalled from memory to citing verses actually present in the retrieved context **62% of the time (versus 0% without retrieval)**, and on the [RGB](https://arxiv.org/abs/2309.01431) benchmark of recent-events questions it raised accuracy from **19% closed-book to 98% with retrieval**. Notably, SAGE is built on the *weakest* closed-book recaller of the three generators tested yet outperforms all of them once retrieval is supplied — evidence that the gains come from the pipeline rather than the base model. The results also cleanly localize the remaining ceiling to **retrieval quality** rather than generation.

## Data

SAGE's retrieval corpus is **38,467 single-verse chunks** drawn from five verse-structured, public-domain (or free-distribution) scriptures, one per tradition: the [King James Bible](https://github.com/aruljohn/Bible-kjv) (Christian, 31,102 verses), the [Qur'an in Saheeh International English](https://github.com/risan/quran-json) (Islamic, 6,236), the [Bhagavad Gita, Swami Sivananda translation](https://github.com/gita/gita) (Hindu, 701), the [Dhammapada, Buddharakkhita translation](https://github.com/iacchus/dhammapada.json) (Buddhist, 347), and the [Tao Te Ching, James Legge translation via Standard Ebooks](https://standardebooks.org/ebooks/laozi/tao-te-ching/james-legge) (Taoist, 81). Each source was reformatted into a normalized `{reference, text}` verse record whose reference uses a canonical locator scheme (e.g. `Matthew 18:21`, `Qur'an 2:286`, `Bhagavad Gita 2.47`, `Dhammapada 5`, `Tao Te Ching 44`), then chunked one verse per chunk and tagged with its tradition. To evaluate the pipeline, I constructed a **gold test set of 100 test cases**: 30 synthetic seeker profiles (spanning age, gender, and a seeker→disciple relationship to their tradition) paired with first-person moral quandaries, where each case carries the **ideal passages it should retrieve** (canonical labels) and an **ideal reference response**. Retrieval is scored against those labels; generation against the reference responses. The corpus intentionally covers five of the project's ten traditions — Jewish, Norse, Aboriginal, Gandhian, and Missionaries-of-Charity sources are oral or in-copyright and are left as a documented gap — so 34 of the 100 test cases fall outside the corpus by design.

## Methodology

SAGE is a **RAG pipeline, not a fine-tuned model**, chosen because the task requires *verifiable, citable* scripture and the knowledge is a large public-domain corpus best kept external and updatable ([Lewis et al., 2020](https://arxiv.org/abs/2005.11401)); grounding also directly counters the [fabrication failure mode](https://arxiv.org/abs/2005.00661) of ungrounded generation. The corpus is embedded and stored in [ChromaDB](https://www.trychroma.com/); at inference the seeker's quandary is embedded, the top-*k* (k=5) most similar chunks are retrieved under **cosine similarity and filtered to the seeker's tradition(s)**, and [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) generates a 250–400-word, non-prescriptive reflection that cites the retrieved passages, seeded with five hand-written exemplars that fix the output style. I compared three sentence-embedding encoders — [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5), and [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) — holding the vector store and chunking fixed to isolate the encoder; **all-mpnet-base-v2** performed best (Recall@5 0.028, MRR 0.045), with bge-small a close, faster second (comparable hit@5 at half the dimensionality). Reproducibility: profiles seeded at 5002, test-case matching at 5003, retrieval top-k = 5, greedy decoding for evaluation.

## Evaluation

Results on the three benchmark tasks and the constructed testing split. The testing-split columns report **citation grounding** (share of citations that appear in the retrieved passages) and **citation gold-relevance** (share of cases citing a gold-labeled verse).


| Model | RGB (closed-book acc) ↑ | MultiHop-RAG (acc) ↑ |
|---|---|---|
| **SAGE (Qwen2.5-7B + RAG)** | **98.0%** | **64.0%** |
| Qwen2.5-7B-Instruct (base, no retrieval) | 19.0% | 47.0% |
| Llama-3.1-8B-Instruct (comparison) | 28.0% | 44.0% |
| Mistral-7B-Instruct-v0.3 (comparison) | 36.0% | 58.0% |


*QA benchmarks scored on n=100 items sampled with seed 5002; correctness is substring answer-matching. The SAGE row supplies each benchmark's gold passages as retrieved context; the base row is closed-book, so the two differ only in the presence of context. Testing-split columns are reported for the SAGE pipeline and its base generator; comparison models were evaluated on the shared public benchmarks. RAGTruth measures span-level faithfulness rather than answer accuracy and requires a separate entailment-based evaluation, which was not run — see Limitations.*

**Benchmarks and why.** I chose three complementary RAG benchmarks that stress different failure modes: [RGB](https://arxiv.org/abs/2309.01431) (Chen et al., 2024) tests robustness to noisy retrieval and whether a model can answer recent-events questions it cannot know closed-book — a direct probe of the need for retrieval; [MultiHop-RAG](https://arxiv.org/abs/2401.15391) (Tang & Yang, 2024) tests synthesis across multiple retrieved passages; and [RAGTruth](https://aclanthology.org/2024.acl-long.585/) (Niu et al., 2024) tests faithfulness — whether generations hallucinate relative to their context, the property SAGE most needs. The **testing split** is SAGE's domain-specific benchmark: 100 profile–quandary cases scored on grounded, in-tradition citation. **Comparison models.** [Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) and [Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) are chosen as strong, similarly-sized (7–8B) open instruction models with solid general reasoning, giving a fair same-scale baseline for the generator swapped into the identical pipeline. **Summary.** Holding the generator fixed and adding retrieval raised RGB accuracy from 19% to 98% (+79 points) and MultiHop-RAG from 47% to 64%; the smaller multi-hop gain reflects that benchmark's need to synthesize across documents rather than look up a single fact. SAGE outperforms both comparison models despite being built on Qwen2.5-7B, which is the weakest of the three closed-book (19% RGB vs. 36% for Mistral) — the clearest evidence that the gains come from the retrieval pipeline, not the base model. On SAGE's own testing split, citation grounding rose from 0% to 62% while gold-relevance held near 7%, showing the generator faithfully cites what it is given and that retrieval, not generation, is the binding constraint.

## Usage and Intended Uses

SAGE is a pipeline (retriever + generator), so usage loads the generator from Hugging Face Transformers and runs it over retrieved passages. Minimal example:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
import torch, json, numpy as np

# 1. generator + retriever
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
gen = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct",
                                           dtype=torch.bfloat16, device_map="auto")
emb = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cuda")

# 2. corpus (sage_corpus.jsonl in this repo)
chunks = [json.loads(l) for l in open("sage_corpus.jsonl")]
C = emb.encode([c["text"] for c in chunks], normalize_embeddings=True)

def sage(quandary, traditions, k=5):
    idx = np.array([i for i, c in enumerate(chunks) if c["tradition"] in traditions])
    q = emb.encode([quandary], normalize_embeddings=True)[0]
    top = idx[np.argsort(-(C[idx] @ q))[:k]]
    passages = "\n".join(f"- {chunks[i]['reference']}: {chunks[i]['text']}" for i in top)
    msg = [{"role": "system", "content": "You are SAGE, a non-prescriptive spiritual companion. "
            "Reflect on the seeker's quandary grounded ONLY in the retrieved passages, cite each by "
            "name, and end with a line 'Sources: <ref>; <ref>'."},
           {"role": "user", "content": f"QUANDARY\n{quandary}\n\nRETRIEVED PASSAGES\n{passages}"}]
    text = tok.apply_chat_template(msg, add_generation_prompt=True, tokenize=False)
    out = gen.generate(**tok(text, return_tensors="pt").to(gen.device), max_new_tokens=700)
    return tok.decode(out[0], skip_special_tokens=True)

print(sage("A friend asked me to cover for something they did. What should I do?", ["christian"]))
```

**Intended uses.** SAGE is intended for **educational and exploratory** purposes: personal reflection, comparative study of how different traditions frame a moral question, and as a demonstration of tradition-faithful RAG. It is **not** a source of religious authority, a substitute for a rabbi, imam, priest, monk, or other qualified spiritual advisor, and **not** a mental-health or crisis resource. Outputs should be read as prompts for reflection, not rulings.

## Prompt Format

The model is prompted with a SAGE system instruction, then a user turn containing the seeker's quandary and the tradition-filtered retrieved passages, each labeled with its canonical reference.

```
SYSTEM: You are SAGE, a non-prescriptive spiritual companion. Reflect on the seeker's
quandary grounded ONLY in the retrieved passages, cite each by name, and end with a
line "Sources: <ref>; <ref>".

USER:
QUANDARY
  <the seeker's free-text moral quandary>

RETRIEVED PASSAGES
  - Matthew 18:21: Then came Peter to him, and said, Lord, how oft shall my brother sin...
  - Colossians 3:13: Forbearing one another, and forgiving one another...
```

## Expected Output Format

A single 250–400-word, non-prescriptive reflection that surfaces tension and convergence across the cited passages and closes with a machine-readable `Sources:` line listing the references used.

```
Forgiveness, in the passages you've been given, is framed less as a single act than as a
posture returned to over time. When Peter asks how many times he must forgive (Matthew
18:21), the answer points past any fixed number... [~300 words] ...releasing the debt is
not the same as restoring trust, and you are not asked to do both at once.

Sources: Matthew 18:21; Colossians 3:13
```

## Repository Contents

| Path | Description |
|---|---|
| `sage_corpus.jsonl` | The retrieval corpus: 38,467 verse-level chunks, each tagged with its tradition and canonical reference. |
| `eval/sage_testcases.json` | The 100 gold test cases (profile + quandary + ideal retrieval labels). |
| `eval/sage_profiles.json`, `eval/sage_quandary_bank.json` | The 30 seeker profiles and 100-item quandary bank the test cases are built from. |
| `eval/sage_exemplars.json` | The five hand-written exemplars that fix SAGE's output style. |
| `eval/sage_retrieval_comparison.{md,csv}` | Recall@k / MRR results for the three embedding encoders. |
| `pipeline/build_verses.py` | Downloads the five public-domain scriptures and normalizes them to verse records. |
| `pipeline/build_corpus.py` | Chunks the verse files into the reference-tagged corpus. |
| `pipeline/references.py` | Canonical-locator parser and overlap matcher used to score retrieval. |
| `pipeline/retrieval_comparison.py` | Embedding × similarity-metric comparison harness. |
| `pipeline/build_sage_profiles.py`, `pipeline/build_sage_testcases.py` | Reproduce the gold evaluation set (seeds 5002 / 5003). |

To rebuild the corpus from source: `python pipeline/build_verses.py && python pipeline/build_corpus.py --verses-dir ./verses --size 1 --stride 1`

## Citation and Licensing

The generator is [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) (Apache 2.0). Corpus texts are public domain (King James Bible; Bhagavad Gita, Sivananda; Tao Te Ching, Legge) or distributed freely for non-commercial use (Dhammapada, Buddharakkhita; Qur'an, Saheeh International) — please observe the terms of each source when redistributing.

## Limitations

SAGE's quality is **bottlenecked by retrieval**: the best encoder reached only Recall@5 ≈ 0.03 on the test set, so while the generator faithfully grounds 62% of its citations in the retrieved context, it surfaces the *ideal* verse only ~7% of the time. This is driven by (a) the corpus covering only **five of ten traditions** — Jewish, Norse, Aboriginal, Gandhian, and Missionaries-of-Charity texts are oral or in-copyright, so 34% of test cases have nothing to retrieve; (b) exact single-verse gold labels evaluated against a ~38K-chunk corpus, penalizing semantically apt but non-identical retrievals; and (c) a **register gap** between modern first-person quandaries and archaic KJV / classical translations that depresses embedding similarity. The benchmark evaluation also has scope limits: RAGTruth was not run, so span-level faithfulness is unmeasured, and QA correctness uses substring answer-matching, which is generous on short entity and yes/no answers and likely inflates the closed-book MultiHop-RAG baseline. Further, the gold reference responses were generated by a teacher model and so inherit its stylistic tendencies, the seeker profiles are synthetic rather than drawn from real users, and citation validity is measured by locator match rather than deep semantic faithfulness. SAGE should be treated as a research prototype for tradition-faithful reflection, not a deployable spiritual advisor.
