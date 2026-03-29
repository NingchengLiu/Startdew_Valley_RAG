# Stardew Valley RAG Project

This repository provides a clean Python project framework for a team-based Retrieval-Augmented Generation (RAG) conversational agent focused on the public Stardew Valley Wiki.

At the current stage, only the data extraction layer is intended as the first concrete milestone, while the remaining modules are organized so teammates can extend them without restructuring the codebase.

## Project Overview

The long-term system is intended to support:

- Wiki data extraction and reproducible storage
- Text preprocessing and normalization
- Chunking for retrieval
- Embedding generation
- Vector storage
- Retrieval orchestration
- Conversational agent logic
- A simple frontend

## Current Status

Implemented data artifact:

- Raw Stardew Valley Wiki extraction output stored in `data/raw/`

Project scaffold only:

- `src/extraction/`
- `src/preprocessing/`
- `src/chunking/`
- `src/embeddings/`
- `src/vectorstore/`
- `src/retrieval/`
- `src/agent/`
- `src/frontend/`
- `tests/`

## Folder Structure

```text
Stardew_valley_RAG/
├── .env.example
├── .gitignore
├── README.md
├── config.py
├── main.py
├── requirements.txt
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/
├── notebooks/
├── src/
│   ├── extraction/
│   ├── preprocessing/
│   ├── chunking/
│   ├── embeddings/
│   ├── vectorstore/
│   ├── retrieval/
│   ├── agent/
│   ├── frontend/
│   └── utils/
└── tests/
```

## Setup Instructions

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment defaults if needed:

```bash
copy .env.example .env
```

## Data Notes

The repository currently includes raw extracted Stardew Valley Wiki data in `data/raw/`. The `data/interim/` and `data/processed/` folders are reserved for future preprocessing and downstream pipeline outputs.

## Teammate Handoff Notes

- Keep extraction, preprocessing, chunking, embedding, retrieval, and agent logic separated by module.
- Avoid changing the project structure unless the team agrees on a repo-wide refactor.
- Treat `data/raw/` as the source-of-truth snapshot before future cleaning or chunking steps are added.
