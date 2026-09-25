Build a system where three specialised AI agents collect the day's news in Technology, Finance, and Politics. The agents clean the articles, tag them, and store them in a shared knowledge base. A Retrieval-Augmented Generation (RAG) layer sits on top of that knowledge base, and a chat interface lets any user ask questions such as "What did the RBI announce this week and how did markets react?" The answers are grounded in the collected news, cite their sources, and are aware of dates.

The project covers the core skills of agentic AI: multi-agent orchestration, data pipelines, embeddings and vector search, prompt design, and building a usable product.

Problem Statement

Business owners and professionals cannot read hundreds of news sources every day. General-purpose chatbots either don't know today's news or can't show where their information came from. This project builds a personal news analyst that is always current, organised by domain, and answers only from verified sources.

System Architecture
[Scheduler: daily / hourly]
        │
   ┌────┼────────────┐
   ▼    ▼            ▼
Tech   Finance    Politics      ← Fetcher agents (RSS, news APIs, web)
Agent  Agent      Agent
   └────┼────────────┘
        ▼
Processing Agent  → clean, dedupe, summarise, tag, chunk
        ▼
Embedding + Vector Store (with metadata: date, category, source, URL)
        ▼
RAG Query Engine → retrieve → rerank → generate answer with citations
        ▼
Chat Interface (web app)
Core Components

1. Fetcher agents (one per domain). Each agent has its own list of sources, such as RSS feeds, NewsAPI or GNews, and official sites like RBI, SEBI, and PIB. Each also has its own relevance rules. For example, the Finance agent keeps articles about markets, policy rates, and earnings, and drops lifestyle pieces. The agents run on a schedule and store the raw articles with the headline, body, URL, publication date, and source.

2. Orchestrator. The orchestrator coordinates the agents. It triggers the runs, handles failures and retries, and logs what was collected each day. It can be built with LangGraph, CrewAI, n8n, or a simple Python scheduler.

3. Processing agent. This agent removes duplicates, since the same story often appears in 20 outlets. It strips boilerplate, generates a short summary, and extracts entities such as companies, people, and countries. It then tags each article by category and splits it into chunks of roughly 300–500 tokens.

4. Knowledge base. The chunks are embedded and stored in a vector database such as Chroma, Qdrant, Pinecone, or pgvector. Rich metadata is stored alongside them so that searches can be filtered, for example "only finance, last 7 days."

5. RAG query engine. The engine works in five steps:

It interprets the question and infers any time range or category.
It retrieves the most relevant chunks, combining keyword and semantic (hybrid) search.
It reranks the results and gives more weight to recent news.
It generates an answer using only the retrieved content.
It cites the sources with links and dates. If nothing relevant was found, it says "I don't have news on that" instead of guessing.

6. Chat interface. A simple web app built with Streamlit, Gradio, or a React front end. It includes a chat window, category filters, and a date picker. Optionally, it can show a "Today's Briefing" panel that is generated automatically each morning.

Suggested Tech Stack
Language: Python
Agent framework: LangGraph or CrewAI
LLM: Claude or another capable model
Embeddings: an OpenAI, Cohere, or open-source embedding model
Vector database: ChromaDB, which is easy to run locally for learners
Interface: Streamlit
Scheduling: cron, APScheduler, or n8n
Deliverables
A working deployed app, or a local demo
A code repository with a README
An architecture diagram
An evaluation report: a set of 20–30 test questions with scores for accuracy, citation correctness, recency, and handling of questions the system can't answer
A 10-minute demo and presentation