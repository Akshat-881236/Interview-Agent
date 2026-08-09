# RAG.md: Retrieval-Augmented Generation Architecture & Algorithmic Foundations

This document outlines the design, mathematical framework, and Design and Analysis of Algorithms (DAA) concepts underlying the **Retrieval-Augmented Generation (RAG)** pipeline for the AI Technical Interview Agent.

---

## 1. Core Architectural Philosophy: Non-Parametric Context Injection

In high-stakes technical interviewing, fine-tuning model parameters directly on candidate transcripts or evolving curriculum data presents significant liabilities:

* **Catastrophic Forgetting & Drift:** Updating model weights via standard fine-tuning algorithms introduces weight drift, degrading baseline reasoning and technical evaluation capabilities.
* **Privacy & Leakage:** Parameterizing candidate response history directly into model weights risks cross-session data leakage across interviewees.
* **Latency & Computational Cost:** Gradient-based optimization algorithms (e.g., AdamW, LoRA backpropagation) cannot run in real time during a multi-turn interview session.

### The RAG Alternative

Instead of parameter updates, our AI Interview Agent uses **Non-Parametric In-Context Knowledge Retrieval**. The foundational LLM remains frozen ($\theta_{\text{LLM}} = \text{const}$), while domain knowledge, candidate profile signals, and interview histories are ingested dynamically via a dual-stage retrieval pipeline.

---

## 2. Mathematical Formulation of the RAG Pipeline

```
  [ Candidate Query / Response ]
                │
                ▼
  ┌───────────────────────────┐
  │  Multi-Modal & Text Query │
  └─────────────┬─────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌──────────────┐ ┌──────────────┐
│ Dense Embed  │ │ Lexical BM25 │
│ (Vector DB)  │ │   (Inverted) │
└───────┬──────┘ └───────┬──────┘
        │                │
        └───────┬────────┘
                ▼
  ┌───────────────────────────┐
  │  Reciprocal Rank Fusion   │
  └─────────────┬─────────────┘
                │
                ▼
  ┌───────────────────────────┐
  │ Max Marginal Relevance    │
  └─────────────┬─────────────┘
                │
                ▼
  ┌───────────────────────────┐
  │   Grounded Prompt Injection│
  └───────────────────────────┘

```

### 2.1. Vector Representation & Document Embeddings

Let $\mathcal{D} = \{d_1, d_2, \dots, d_N\}$ represent the set of all curriculum chunks, learning objectives, and candidate mission signals derived from `curriculum.json` and `candidates.json`.

Each document chunk $d_i$ is mapped to a high-dimensional vector space using a dense embedding model $f_{\theta}: \mathcal{D} \to \mathbb{R}^D$:

$$\vec{e}_i = f_{\theta}(d_i) \in \mathbb{R}^D, \quad \Vert{}\vec{e}_i\Vert{}_2 = 1$$

When a candidate provides a response or when the agent evaluates the next topic, the input context $q$ is embedded as:

$$\vec{q} = f_{\theta}(q) \in \mathbb{R}^D$$

### 2.2. Hybrid Retrieval Engine: Sparse + Dense Score Fusion

To maximize retrieval recall and precision across both technical terminology (exact keywords like `ChromaDB`, `PEFT`, `MCP`) and semantic concepts, we implement a **Hybrid Search Engine**.

#### Lexical Retrieval (BM25)

For a query $q$ containing terms $t_1, t_2, \dots, t_n$ and document $d_i$:

$$\text{Score}_{\text{BM25}}(d_i, q) = \sum_{j=1}^n \text{IDF}(t_j) \cdot \frac{f(t_j, d_i) \cdot (k_1 + 1)}{f(t_j, d_i) + k_1 \cdot \left(1 - b + b \cdot \frac{\vert{}d_i\vert{}}{\text{avgdl}}\right)}$$

Where:

* $\text{IDF}(t_j) = \ln \left( \frac{N - n(t_j) + 0.5}{n(t_j) + 0.5} + 1 \right)$
* $k_1 = 1.2$, $b = 0.75$ are standard tuning parameters.
* $\text{avgdl}$ is the average document length across $\mathcal{D}$.

#### Dense Vector Similarity

Semantic similarity is calculated using the Cosine Inner Product:

$$\text{Score}_{\text{Dense}}(d_i, q) = \vec{q} \cdot \vec{e}_i = \sum_{k=1}^D q_k \cdot e_{i,k}$$

#### Reciprocal Rank Fusion (RRF)

To combine dense and sparse rankings without requiring score normalization, we apply Reciprocal Rank Fusion:

$$\text{RRF}(d_i) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{1}{k + r_m(d_i)}$$

Where $r_m(d_i)$ is the rank of document $d_i$ in retrieval mode $m$, and $k = 60$ is a smoothing constant.

---

### 2.3. Contextual Diversity via Maximum Marginal Relevance (MMR)

To avoid asking redundant follow-up questions from the same subset of learning objectives, we filter retrieved documents $\mathcal{R}$ to produce a final context set $\mathcal{S}$ using Maximum Marginal Relevance:

$$\text{MMR} = \arg\max_{d_i \in \mathcal{R} \setminus \mathcal{S}} \left[ \lambda \cdot \text{Sim}_1(d_i, q) - (1 - \lambda) \cdot \max_{d_j \in \mathcal{S}} \text{Sim}_2(d_i, d_j) \right]$$

Where:

* $\text{Sim}_1, \text{Sim}_2$ denote inner product vector similarities.
* $\lambda \in [0, 1]$ controls the trade-off between relevance and diversity (default set to $\lambda = 0.7$).

---

## 3. Dynamic Curriculum Traversal & DAA Concepts

The interview engine guarantees that each interview session covers **at least 4 distinct curriculum days** and **at least 8 questions** tailored to candidate weaknesses.

### 3.1. Graph Formulation of the Curriculum

We model the 31-day curriculum as a Directed Acyclic Graph $G = (V, E)$:

* **Vertices ($V$):** $v_i \in \{1, 2, \dots, 31\}$, representing curriculum days and their associated objectives.
* **Edges ($E$):** $(v_i, v_j) \in E$ where $i < j$, representing prerequisite dependencies between modules.

Each candidate profile $C$ provides a historical attempt vector $\vec{w}_C \in \mathbb{R}^{31}$, where weight $w_i$ measures the candidate's mastery gap for day $i$:

$$w_i = \alpha \cdot \text{attempts}_i + \beta \cdot \mathbb{I}(\text{skipped}_i) - \gamma \cdot \mathbb{I}(\text{passed}_i)$$

```
     [ Day 1: Setup ]
            │
            ▼
   [ Day 7: Embeddings ] ───(w_7 = 0.8)───┐
            │                             │
            ▼                             ▼
[ Day 10: Retrieval Engine ] ──► [ Day 12: Prompting ]
            │                             │
            └──────────────┬──────────────┘
                           ▼
             [ Day 22: Multi-Agent ]

```

### 3.2. Dynamic Programming for Optimal Topic Selection

To select $k = 4$ curriculum days that maximize assessment utility subject to graph ordering constraints, we solve a constrained Dynamic Programming problem over $G$.

#### Subproblem Definition

Let $DP(i, m)$ be the maximum candidate evaluation utility obtainable by selecting $m$ days from the topological prefix of vertices up to vertex $v_i$:

$$DP(i, m) = \max \left( DP(i-1, m), \max_{(v_j, v_i) \in E} \left\{ DP(j, m-1) \right\} + w_i \right)$$

#### Boundary Conditions

$$DP(i, 0) = 0 \quad \forall i$$

$$DP(0, m) = -\infty \quad \forall m > 0$$

#### Time & Space Complexity Analysis

* **Time Complexity:** Computing the optimal interview path across $\vert{}V\vert{} = 31$ curriculum days and target $k = 4$ days takes $\mathcal{O}(k \cdot (\vert{}V\vert{} + \vert{}E\vert{}))$. With $\vert{}V\vert{} \le 31$ and $\vert{}E\vert{} \le \frac{31 \times 30}{2} = 465$, the topological graph traversal completes in $\mathcal{O}(1)$ runtime ($< 1 \text{ ms}$ execution).
* **Space Complexity:** $\mathcal{O}(k \cdot \vert{}V\vert{})$ space required for the dynamic programming memoization table.

---

### 3.3. Indexing Algorithms & Vector Search Complexities

To handle scale as curriculum documents and interview session transcripts grow, the vector database relies on **Hierarchical Navigable Small World (HNSW)** graphs.

| Algorithm / Step | Time Complexity (Average) | Time Complexity (Worst Case) | Space Complexity |
| --- | --- | --- | --- |
| **HNSW Index Construction** | $\mathcal{O}(N \log N)$ | $\mathcal{O}(N^2)$ | $\mathcal{O}(N \cdot M)$ |
| **HNSW Search ($K$-NN Retrieval)** | $\mathcal{O}(\log N)$ | $\mathcal{O}(N)$ | $\mathcal{O}(1)$ auxiliary |
| **BM25 Lexical Lookup** | $\mathcal{O}(\vert{}q\vert{})$ | $\mathcal{O}(\vert{}q\vert{} \cdot \text{df}_{\max})$ | $\mathcal{O}(N \cdot L)$ inverted index |
| **Reciprocal Rank Fusion (RRF)** | $\mathcal{O}(K \log K)$ | $\mathcal{O}(K \log K)$ | $\mathcal{O}(K)$ |
| **MMR Re-Ranking** | $\mathcal{O}(K \cdot \vert{}\mathcal{S}\vert{})$ | $\mathcal{O}(K^2)$ | $\mathcal{O}(K)$ |

Where:

* $N$ is the total number of indexed knowledge chunks.
* $M$ is the number of bi-directional links per node in HNSW ($M = 16$).
* $K$ is the top-$k$ retrieved candidates before re-ranking ($K = 20$).
* $\vert{}q\vert{}$ is the number of tokens in the query string.
* $L$ is the average string length.

---

## 4. Adaptive Follow-Up Engine & Grounding Verification

After a candidate responds to an interview question, the AI evaluates whether to issue a dynamic follow-up question or proceed to the next node in the DP-generated interview path.

```
       [ Transcribed Candidate Answer ]
                      │
                      ▼
       ┌──────────────────────────────┐
       │ Compute Grounding Score (G)  │
       └──────────────┬───────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
  G < 0.65                       G ≥ 0.65
(Shallow / Incomplete)      (Sufficient Answer)
        │                           │
        ▼                           ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ Trigger RAG Follow-up   │   │ Advance Node in          │
│ Query Pipeline          │   │ Interview Path (DP)      │
└─────────────────────────┘   └──────────────────────────┘

```

### 4.1. Grounding Score Formulation

The system calculates a **Grounding Score ($G$)** to detect hallucination, vagueness, or technical inaccuracies in candidate responses before constructing a follow-up:

$$G(A, \mathcal{K}) = \mu_1 \cdot \text{Cosine}(\vec{e}_A, \vec{e}_{\mathcal{K}}) + \mu_2 \cdot \frac{\vert{}\text{Entities}(A) \cap \text{Entities}(\mathcal{K})\vert{}}{\vert{}\text{Entities}(\mathcal{K})\vert{}}$$

Where:

* $A$ is the candidate's transcribed answer.
* $\mathcal{K}$ is the ground-truth technical objective retrieved from `curriculum.json` for that specific day.
* $\mu_1 = 0.6, \mu_2 = 0.4$ are weighting coefficients.

### 4.2. Decision Tree Logic for Follow-Up Routing

1. **If $G(A, \mathcal{K}) < 0.65$ AND current topic question count $< 2$:**
* Trigger follow-up sub-agent. Retrieve specific prerequisite objectives for day $d_i$ using BM25 + Dense RAG. Ask targeted clarification question.


2. **If $G(A, \mathcal{K}) \ge 0.65$ OR topic question count $\ge 2$:**
* Log transcript node evaluation, increment globally covered curriculum days count, and advance to next vertex in the dynamic programming path.



---

## 5. Security, Token Window Optimization, and Privacy

### 5.1. Context Window Bounds & Token Management

To prevent LLM context saturation during multi-turn interviews, conversation transcripts are pruned using a **Sliding Window Buffer with Summarization**:

$$\text{Context}_t = \text{SystemPrompt} \cup \text{RAG}_{\text{Curriculum}} \cup \text{Summary}(H_{1:t-4}) \cup H_{t-3:t}$$

This bounds the input token length to a constant limit $T_{\max} \le 4096 \text{ tokens}$, ensuring consistent API latency ($\le 2.5 \text{ s}$) across prolonged interviews.

### 5.2. Data Privacy & Isolation Guards

* **In-Memory Session Lifecycle:** All session vectors and context windows stored in Redis expire automatically via Time-To-Live (TTL) policies ($\text{TTL} = 3600 \text{ seconds}$) upon interview completion.
* **Sanitization Layer:** Transcripts are stripped of personal health information (PHI) or personally identifiable information (PII) using regex filters and named-entity recognition (NER) before reaching vector storage.