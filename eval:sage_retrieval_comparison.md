# SAGE retrieval comparison

Corpus: `sage_corpus.jsonl` (38467 chunks) | 100 evaluable test cases | tradition-filtered top-k

| Config | Recall@1 | Recall@5 | Recall@10 | hit@5 | MRR |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 + cosine | 0.003 | 0.015 | 0.022 | 0.050 | 0.031 |
| bge-small-en-v1.5 + cosine | 0.003 | 0.025 | 0.040 | 0.080 | 0.033 |
| all-mpnet-base-v2 + cosine | 0.005 | 0.028 | 0.043 | 0.070 | 0.045 |

**Best by Recall@5 (tie-break MRR): all-mpnet-base-v2 + cosine**