# vezeeta-pulse

A data-driven analysis of 17,119 doctors on Vezeeta — Egypt's largest online healthcare marketplace — covering pricing, geographic distribution, performance metrics, and an AI-powered doctor recommendation engine.

---

## Running the Website

The website has two parts: a static HTML report and a Flask backend that powers the AI doctor finder.

### 1. Install dependencies

```bash
pip install flask flask-cors pandas faiss-cpu sentence-transformers
```

### 2. Start the Flask server

```bash
cd Website
python app.py
```

The server will load the data, FAISS index, and sentence-transformer model on startup (this takes ~30 seconds the first time).

### 3. Open the website

Once you see `Ready — 17,119 doctors indexed.` in the terminal, open your browser and go to:

```
http://localhost:5000
```

---

## Project Structure

```
vezeeta-pulse/
├── Website/
│   ├── app.py              # Flask backend (AI recommendation API)
│   ├── vezeeta2.html       # Main website
│   └── vezeeta brand new.pdf  # Downloadable report
├── AI_features/
│   ├── recommendation_engine.ipynb  # Symptom-to-doctor matcher notebook
│   └── vezeeta_faiss.index          # Pre-built FAISS vector index
├── cleaning/
│   └── cleaned_data.csv    # Cleaned dataset (17,119 doctors)
├── analysis/
│   └── vezeeta_project_analysis.ipynb  # Full analysis notebook
└── crawling/
    └── vezeeta_*.py        # Web scraping scripts
```

---

## AI Doctor Finder

The recommendation engine uses semantic search to match patient symptoms to doctors:

- **Model:** `all-MiniLM-L6-v2` (sentence-transformers)
- **Index:** FAISS flat inner-product index (cosine similarity)
- **Ranking:** 70% semantic similarity + 30% normalized review score
- **Filters:** Max fee, area/city, specialty

The FAISS index (`vezeeta_faiss.index`) is pre-built — no re-indexing needed unless the dataset changes.
