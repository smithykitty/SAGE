"""
SAGE — embedding/retrieval comparison harness.

Builds a vector index over the corpus, retrieves tradition-filtered top-k for each
test-case quandary, and scores retrieval against the gold reference labels with the
overlap matcher. Compares several (embedding x similarity-metric) configurations on
Recall@k, hit-rate@k, and MRR across embedding x similarity-metric configs.

OFFLINE configs (run here, no downloads): sklearn TF-IDF / Hashing vectorizers with
cosine / dot / euclidean similarity. These prove the harness and the metric deltas.

REAL configs (documented; run in your GPU/Colab/HPC env): sentence-transformers
embeddings in ChromaDB. Swapping them in changes only the Index builder — the
evaluation code below is identical.

Usage:
    python retrieval_comparison.py            # offline configs on the seed corpus
    python retrieval_comparison.py --corpus sage_corpus.jsonl --real   # real run
"""

import os
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel, euclidean_distances

from references import parse_ref, refs_overlap

OUT = Path(os.environ.get("SAGE_OUT", "outputs"))
KS = [1, 3, 5, 10]
MRR_CUTOFF = 10


# --------------------------------------------------------------------------- #
# Index (offline sklearn vectorizers)                                          #
# --------------------------------------------------------------------------- #
class VectorIndex:
    def __init__(self, vectorizer, metric="cosine"):
        self.vectorizer = vectorizer
        self.metric = metric

    def fit(self, chunks):
        self.chunks = chunks
        self.X = self.vectorizer.fit_transform([c["text"] for c in chunks])
        self.parsed = [[parse_ref(r) for r in c["references"]] for c in chunks]
        self.by_trad = {}
        for i, c in enumerate(chunks):
            self.by_trad.setdefault(c["tradition"], []).append(i)
        return self

    def query(self, text, traditions, k):
        idx = np.array(sorted(j for t in traditions for j in self.by_trad.get(t, [])))
        if idx.size == 0:
            return []
        q = self.vectorizer.transform([text])
        Xs = self.X[idx]
        if self.metric == "cosine":
            scores = cosine_similarity(q, Xs)[0]
        elif self.metric == "dot":
            scores = linear_kernel(q, Xs)[0]
        elif self.metric == "euclidean":
            scores = -euclidean_distances(q, Xs)[0]
        else:
            raise ValueError(self.metric)
        order = np.argsort(-scores)[:k]
        return [(int(idx[o]), float(scores[o])) for o in order]


def make_offline_configs():
    return [
        ("tfidf_unigram + cosine",
         lambda: VectorIndex(TfidfVectorizer(stop_words="english", ngram_range=(1, 1)), "cosine")),
        ("tfidf_bigram + cosine",
         lambda: VectorIndex(TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                             sublinear_tf=True), "cosine")),
        ("tfidf_unigram + euclidean",
         lambda: VectorIndex(TfidfVectorizer(stop_words="english", ngram_range=(1, 1)), "euclidean")),
        ("hashing_bigram + dot",
         lambda: VectorIndex(HashingVectorizer(stop_words="english", ngram_range=(1, 2),
                                               n_features=2**18, alternate_sign=False), "dot")),
    ]


# --------------------------------------------------------------------------- #
# Real index (sentence-transformers + ChromaDB) — documented, not run offline  #
# --------------------------------------------------------------------------- #
REAL_MODELS = [
    ("all-MiniLM-L6-v2 + cosine", "sentence-transformers/all-MiniLM-L6-v2", "cosine"),
    ("bge-small-en-v1.5 + cosine", "BAAI/bge-small-en-v1.5", "cosine"),
    ("all-mpnet-base-v2 + cosine", "sentence-transformers/all-mpnet-base-v2", "cosine"),
]


class SentenceTransformerChromaIndex:
    """Real RAG index. Requires: pip install sentence-transformers chromadb."""
    def __init__(self, model_name, metric="cosine"):
        from sentence_transformers import SentenceTransformer
        import chromadb
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.Client()
        self.col = self.client.create_collection(
            name="sage_" + model_name.split("/")[-1].replace(".", "_"),
            metadata={"hnsw:space": {"cosine": "cosine", "dot": "ip", "euclidean": "l2"}[metric]})

    def fit(self, chunks):
        self.chunks = chunks
        self.parsed = [[parse_ref(r) for r in c["references"]] for c in chunks]
        embs = self.model.encode([c["text"] for c in chunks],
                                 normalize_embeddings=True, batch_size=256).tolist()
        ids = [c["chunk_id"] for c in chunks]
        docs = [c["text"] for c in chunks]
        metas = [{"tradition": c["tradition"], "i": i} for i, c in enumerate(chunks)]
        B = 5000                                    # under ChromaDB's ~5461 per-add cap
        for j in range(0, len(chunks), B):
            self.col.add(ids=ids[j:j + B], embeddings=embs[j:j + B],
                         documents=docs[j:j + B], metadatas=metas[j:j + B])
        return self

    def query(self, text, traditions, k):
        q = self.model.encode([text], normalize_embeddings=True).tolist()
        res = self.col.query(query_embeddings=q, n_results=k,
                             where={"tradition": {"$in": list(traditions)}})
        out = []
        for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
            out.append((int(meta["i"]), -float(dist)))
        return out


# --------------------------------------------------------------------------- #
# Evaluation                                                                   #
# --------------------------------------------------------------------------- #
def chunk_relevant(parsed_refs, gold_parsed):
    return any(refs_overlap(g, c) for c in parsed_refs for g in gold_parsed)


def gold_in_corpus(index, gold_parsed, traditions):
    for t in traditions:
        for i in index.by_trad.get(t, []) if hasattr(index, "by_trad") else range(len(index.chunks)):
            if chunk_relevant(index.parsed[i], gold_parsed):
                return True
    return False


def evaluate(index, cases):
    agg = {f"hit@{k}": [] for k in KS}
    agg.update({f"recall@{k}": [] for k in KS})
    agg["mrr"] = []
    evaluable = 0
    for c in cases:
        gold_parsed = [parse_ref(r) for r in c["expected_references_flat"]]
        results = index.query(c["quandary"], c["traditions"], max(KS))
        ranked = [(index.parsed[i], score) for i, score in results]
        rel_flags = [chunk_relevant(pr, gold_parsed) for pr, _ in ranked]
        evaluable += 1
        for k in KS:
            topk = rel_flags[:k]
            agg[f"hit@{k}"].append(1.0 if any(topk) else 0.0)
            covered = sum(1 for g in gold_parsed
                          if any(refs_overlap(g, c2) for pr, _ in ranked[:k] for c2 in pr))
            agg[f"recall@{k}"].append(covered / len(gold_parsed) if gold_parsed else 0.0)
        rr = 0.0
        for rank, flag in enumerate(rel_flags[:MRR_CUTOFF], start=1):
            if flag:
                rr = 1.0 / rank
                break
        agg["mrr"].append(rr)
    summary = {m: round(float(np.mean(v)), 4) if v else 0.0 for m, v in agg.items()}
    summary["n_cases"] = evaluable
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(OUT / "sage_corpus.seed.jsonl"))
    ap.add_argument("--cases", default=str(OUT / "sage_testcases.json"))
    ap.add_argument("--real", action="store_true", help="Use sentence-transformers + ChromaDB configs.")
    args = ap.parse_args()

    chunks = [json.loads(l) for l in Path(args.corpus).read_text().splitlines() if l.strip()]
    cases = json.loads(Path(args.cases).read_text())
    print(f"Corpus: {len(chunks)} chunks | cases: {len(cases)}\n")

    if args.real:
        configs = [(name, (lambda m=m, s=s: SentenceTransformerChromaIndex(m, s)))
                   for name, m, s in REAL_MODELS]
    else:
        configs = make_offline_configs()

    rows = []
    for name, builder in configs:
        index = builder().fit(chunks)
        summary = evaluate(index, cases)
        summary["config"] = name
        rows.append(summary)
        print(f"{name:32s} | "
              f"R@5={summary['recall@5']:.3f}  R@10={summary['recall@10']:.3f}  "
              f"hit@5={summary['hit@5']:.3f}  MRR={summary['mrr']:.3f}")

    # write comparison table (CSV + markdown)
    cols = ["config", "n_cases"] + [f"recall@{k}" for k in KS] + \
           [f"hit@{k}" for k in KS] + ["mrr"]
    with (OUT / "sage_retrieval_comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    best = max(rows, key=lambda r: (r["recall@5"], r["mrr"]))
    md = ["# SAGE retrieval comparison\n",
          f"Corpus: `{Path(args.corpus).name}` ({len(chunks)} chunks) | "
          f"{rows[0]['n_cases']} evaluable test cases | tradition-filtered top-k\n",
          "| Config | Recall@1 | Recall@5 | Recall@10 | hit@5 | MRR |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['config']} | {r['recall@1']:.3f} | {r['recall@5']:.3f} | "
                  f"{r['recall@10']:.3f} | {r['hit@5']:.3f} | {r['mrr']:.3f} |")
    md.append(f"\n**Best by Recall@5 (tie-break MRR): {best['config']}**")
    (OUT / "sage_retrieval_comparison.md").write_text("\n".join(md))
    print(f"\nBest: {best['config']}  (Recall@5={best['recall@5']:.3f}, MRR={best['mrr']:.3f})")
    print(f"Wrote sage_retrieval_comparison.csv + .md")


if __name__ == "__main__":
    main()
