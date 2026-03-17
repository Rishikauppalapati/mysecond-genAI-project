# RAG Chatbot Architecture for Groww - Phase-wise Implementation

## Overview
This document outlines the architecture for a RAG (Retrieval-Augmented Generation) chatbot that provides information about 4 Axis Mutual Funds:
1. Axis Large Cap Fund
2. Axis Small Cap Fund
3. Axis Nifty 500 Index Fund
4. Axis ELSS Tax Saver

---

## Phase 1: Data Ingestion & Collection

### 1.1 Data Sources Mapping

Based on the spreadsheet, we have two primary data sources:

#### Source A: Groww.in (Web Scraping)
| Fund | Data Points | URL Pattern |
|------|-------------|-------------|
| Axis Large Cap Fund | NAV, MIN SIP, Expense Ratio, Exit Load | https://groww.in/mutual-funds/axis-large-cap-fund-direct-growth |
| Axis Small Cap Fund | NAV, MIN SIP, Expense Ratio, Exit Load | https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth |
| Axis Nifty 500 Index Fund | NAV, MIN SIP, Expense Ratio, Exit Load | https://groww.in/mutual-funds/axis-nifty-500-index-fund-direct-growth |
| Axis ELSS Tax Saver | NAV, MIN SIP, Expense Ratio, Exit Load | https://groww.in/mutual-funds/axis-elss-tax-saver-direct-plan-growth |

#### Source B: AxisMF.com (Web Scraping + PDF Downloads)
| Fund | Data Points | URL Pattern |
|------|-------------|-------------|
| All 4 Funds | Riskometer, Benchmark, FAQs | https://www.axismf.com/mutual-funds/equity-funds/[fund-name]/[code]/direct |
| All 4 Funds | KIM (PDF) | Statutory PDF URLs |
| All 4 Funds | SID (PDF) | Statutory PDF URLs |
| All 4 Funds | Leaflet (PDF) | Factsheet PDF URLs |

### 1.2 Data Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Groww.in   │    │  AxisMF.com  │    │  PDF Docs    │       │
│  │   Scraper    │    │   Scraper    │    │  Downloader  │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                             ▼                                    │
│                  ┌─────────────────────┐                         │
│                  │   Data Normalizer   │                         │
│                  │  (Standard Format)  │                         │
│                  └──────────┬──────────┘                         │
│                             │                                    │
│                             ▼                                    │
│                  ┌─────────────────────┐                         │
│                  │   Raw Data Store    │                         │
│                  │    (JSON/Database)  │                         │
│                  └─────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Technical Components for Phase 1

#### Web Scraping Module
- **Tool**: Python with BeautifulSoup/Scrapy/Selenium
- **Purpose**: Extract structured data from HTML pages
- **Data Points to Extract**:
  - NAV (Current & Historical)
  - Minimum SIP Amount
  - Expense Ratio
  - Exit Load details
  - Riskometer level
  - Benchmark index
  - FAQs content

#### PDF Processing Module
- **Tool**: Python with PyPDF2/pdfplumber
- **Purpose**: Extract text from KIM, SID, Leaflet PDFs
- **Output**: Structured text chunks with metadata

#### Data Storage (Raw)
- **Format**: JSON files or SQLite database
- **Structure**:
  ```json
  {
    "fund_name": "Axis Large Cap Fund",
    "fund_code": "axis-large-cap-fund-direct-growth",
    "source": "groww.in",
    "last_updated": "2026-03-17",
    "data": {
      "nav": {"current": 45.67, "date": "2026-03-17"},
      "min_sip": 100,
      "expense_ratio": 0.64,
      "exit_load": "1% for redemption within 12 months"
    }
  }
  ```

---

## Phase 2: Document Processing & Chunking

### 2.1 Document Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                 Document Processing Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Raw Data   │───▶│  Text        │───▶│  Document    │       │
│  │   Loader     │    │  Cleaner     │    │  Chunker     │       │
│  └──────────────┘    └──────────────┘    └──────┬───────┘       │
│                                                  │                │
│                                                  ▼                │
│                                       ┌─────────────────────┐     │
│                                       │   Chunked Documents │     │
│                                       │   with Metadata     │     │
│                                       └─────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Text Cleaning & Normalization
- Remove HTML tags
- Normalize whitespace
- Handle special characters
- Standardize currency formats
- Normalize date formats

### 2.3 Chunking Strategy

| Content Type | Chunking Method | Chunk Size | Overlap |
|--------------|-----------------|------------|---------|
| NAV Data | Semantic (per fund) | Single record | 0 |
| FAQs | Semantic (per Q&A pair) | Per question | 0 |
| KIM/SID PDFs | Recursive Character | 1000 chars | 200 chars |
| Leaflet | Recursive Character | 1000 chars | 200 chars |

### 2.4 Metadata Enrichment
Each chunk will include:
```json
{
  "chunk_id": "uuid",
  "fund_name": "Axis Large Cap Fund",
  "fund_type": "Equity - Large Cap",
  "source": "groww.in | axismf.com",
  "document_type": "NAV | KIM | SID | Leaflet | FAQ",
  "last_updated": "2026-03-17",
  "url": "source_url"
}
```

---

## Phase 3: Vector Store & Embedding

### 3.1 Embedding Generation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Embedding Layer                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐   │
│  │   Chunked    │───▶│  Embedding       │───▶│   Vector     │   │
│  │   Documents  │    │  Model (OpenAI/  │    │   Store      │   │
│  │              │    │  HuggingFace)    │    │              │   │
│  └──────────────┘    └──────────────────┘    └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Embedding Model Options
| Model | Provider | Dimensions | Use Case |
|-------|----------|------------|----------|
| text-embedding-3-small | OpenAI | 1536 | Balanced quality/cost |
| text-embedding-3-large | OpenAI | 3072 | Higher accuracy |
| all-MiniLM-L6-v2 | HuggingFace | 384 | Local deployment |

### 3.3 Vector Store Options
| Option | Type | Best For |
|--------|------|----------|
| ChromaDB | Local | Development, small scale |
| Pinecone | Cloud | Production, scalability |
| Weaviate | Hybrid | Complex queries |
| FAISS | Local | Research, custom implementations |

### 3.4 Vector Store Schema
```python
{
    "id": "chunk_uuid",
    "embedding": [0.1, 0.2, ...],  # 1536 dimensions
    "metadata": {
        "fund_name": "Axis Large Cap Fund",
        "document_type": "FAQ",
        "content": "original text",
        "source_url": "..."
    }
}
```

---

## Phase 4: RAG Retrieval & Generation

### 4.1 RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Query                                                     │
│       │                                                          │
│       ▼                                                          │
│   ┌──────────────┐                                              │
│   │   Query      │                                              │
│   │   Router     │───▶ Fund-specific filter?                    │
│   └──────────────┘                                              │
│       │                                                          │
│       ▼                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│   │   Query      │───▶│   Vector     │───▶│  Retrieved   │       │
│   │   Embedder   │    │   Search     │    │  Chunks      │       │
│   └──────────────┘    └──────────────┘    └──────┬───────┘       │
│                                                  │                │
│                                                  ▼                │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│   │   Generated  │◀───│    LLM       │◀───│   Context    │       │
│   │   Response   │    │  (GPT-4/     │    │   Builder    │       │
│   └──────────────┘    │   Claude)    │    └──────────────┘       │
│                       └──────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Retrieval Strategy

#### Hybrid Search Approach
1. **Vector Search**: Semantic similarity using embeddings
2. **Keyword Search**: BM25 for exact matches (fund names, terms)
3. **Metadata Filtering**: Filter by fund_name, document_type

#### Retrieval Configuration
- **Top-K chunks**: 5-10 most relevant
- **Re-ranking**: Cross-encoder for relevance scoring
- **Context Window**: Fit within LLM token limits

### 4.3 Context Builder
```python
def build_context(retrieved_chunks):
    context = ""
    for chunk in retrieved_chunks:
        context += f"""
        Source: {chunk.metadata.source}
        Fund: {chunk.metadata.fund_name}
        Type: {chunk.metadata.document_type}
        Content: {chunk.content}
        ---
        """
    return context
```

### 4.4 LLM Integration

#### Prompt Template
```
You are a helpful mutual fund assistant for Groww. Answer the user's 
question based ONLY on the provided context about Axis Mutual Funds.

Available Funds:
- Axis Large Cap Fund
- Axis Small Cap Fund  
- Axis Nifty 500 Index Fund
- Axis ELSS Tax Saver

Context:
{context}

User Question: {question}

Instructions:
1. Answer based only on the provided context
2. If information is not available, say so clearly
3. Include relevant numbers (NAV, expense ratio, etc.) when available
4. Cite the source document type for key facts

Answer:
```

#### LLM Options
| Model | Provider | Context Length | Best For |
|-------|----------|----------------|----------|
| GPT-4 | OpenAI | 128K | High accuracy |
| GPT-3.5-turbo | OpenAI | 16K | Cost-effective |
| Claude 3 Sonnet | Anthropic | 200K | Long contexts |

---

## Phase 5: Chatbot API & Interface

### 5.1 Backend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│   │   FastAPI    │    │   RAG        │    │   Vector     │       │
│   │   Server     │◀──▶│   Engine     │◀──▶│   Store      │       │
│   └──────┬───────┘    └──────────────┘    └──────────────┘       │
│          │                                                       │
│          │    ┌──────────────┐    ┌──────────────┐               │
│          └───▶│  Chat        │◀──▶│  Conversation│               │
│               │  History     │    │  Memory      │               │
│               │  (Redis/DB)  │    │              │               │
│               └──────────────┘    └──────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat endpoint |
| `/funds` | GET | List all available funds |
| `/funds/{fund_name}` | GET | Get specific fund details |
| `/refresh-data` | POST | Trigger data refresh |

### 5.3 Request/Response Format

#### Chat Request
```json
{
  "message": "What is the NAV of Axis Large Cap Fund?",
  "session_id": "user_session_123",
  "fund_filter": "Axis Large Cap Fund"
}
```

#### Chat Response
```json
{
  "response": "The current NAV of Axis Large Cap Fund is Rs. 45.67 as of March 17, 2026.",
  "sources": [
    {
      "fund": "Axis Large Cap Fund",
      "document_type": "NAV",
      "source_url": "https://groww.in/..."
    }
  ],
  "session_id": "user_session_123"
}
```

---

## Phase 6: Conversation Memory

### 6.1 Memory Management

```
┌─────────────────────────────────────────────────────────────────┐
│                 Conversation Memory                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Short-term Memory (Current Session)                            │
│   ├── Last 5-10 message pairs                                    │
│   └── Used for context in current conversation                   │
│                                                                  │
│   Long-term Memory (Cross-session)                               │
│   ├── User preferences                                           │
│   ├── Frequently asked about funds                               │
│   └── Watchlist/favorite funds                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Memory Implementation
- **Storage**: Redis or SQLite
- **Session Management**: UUID-based session IDs
- **Context Window**: Sliding window of last N messages

---

## Technology Stack Summary

| Component | Technology Options |
|-----------|-------------------|
| **Language** | Python 3.10+ |
| **Web Scraping** | BeautifulSoup4, Scrapy, Selenium |
| **PDF Processing** | PyPDF2, pdfplumber |
| **Embeddings** | OpenAI, HuggingFace Sentence-Transformers |
| **Vector Store** | ChromaDB (dev), Pinecone (prod) |
| **LLM** | OpenAI GPT-4/3.5, Anthropic Claude |
| **API Framework** | FastAPI |
| **Memory Store** | Redis, SQLite |
| **Scheduling** | APScheduler, Celery |

---

## Data Refresh Strategy

| Data Type | Refresh Frequency | Trigger |
|-----------|-------------------|---------|
| NAV | Daily | Scheduled job at 9 PM IST |
| Expense Ratio | Weekly | Every Monday |
| KIM/SID/Leaflet | Monthly | First day of month |
| FAQs | Weekly | Every Monday |

---

## Directory Structure (Recommended)

```
groww-rag-chatbot/
├── data/
│   ├── raw/                    # Raw scraped data
│   ├── processed/              # Cleaned & chunked data
│   └── vector_store/           # Vector database files
├── src/
│   ├── scrapers/
│   │   ├── groww_scraper.py
│   │   ├── axismf_scraper.py
│   │   └── pdf_downloader.py
│   ├── processors/
│   │   ├── text_cleaner.py
│   │   ├── chunker.py
│   │   └── metadata_enricher.py
│   ├── embeddings/
│   │   ├── embedder.py
│   │   └── vector_store.py
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── context_builder.py
│   │   └── generator.py
│   ├── api/
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── models.py
│   └── memory/
│       └── conversation_store.py
├── config/
│   └── settings.yaml
├── requirements.txt
└── README.md
```

---

## Next Steps

1. **Phase 1 Implementation**: Start with web scrapers for groww.in and axismf.com
2. **Data Validation**: Verify scraped data accuracy against source websites
3. **Phase 2-3**: Implement document processing and vector store setup
4. **Phase 4-5**: Build RAG pipeline and API
5. **Testing**: Validate responses for all 4 funds and data types
6. **Phase 6**: Add conversation memory for enhanced UX

---

## Notes

- Deployment will be handled in a future phase
- Consider rate limiting for web scraping to avoid IP blocks
- Implement retry logic for failed scrapes
- Store raw data snapshots for audit/debugging purposes
- Consider caching frequently accessed data