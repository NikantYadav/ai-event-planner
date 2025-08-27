# AI Event Planner

An intelligent Python application that helps plan events by analyzing event descriptions and finding the most suitable vendors using AI-powered semantic matching. The system leverages Google Places API for vendor discovery, Gemini LLM for intelligent query generation, and vector embeddings for semantic similarity matching.

## Things to Work on

- Threading
- Direct in the moment saving to database

## Project Structure

```
ai-event-planner/
├── controllers/
│   ├── __init__.py
│   ├── embeddings.py          # Gemini Embeddings API with rate limiting
│   ├── llm_calls.py           # Gemini LLM for query generation
│   ├── place_embeddings.py   # Embedding similarity search
│   └── places.py              # Google Places API integration
├── db/
│   ├── __init__.py
│   ├── place_embeddings_store.py  # TiDB storage operations
│   └── tidb_vector_store.py   # Vector database operations
├── utils/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── logger.py              # Logging utilities
├── main.py                    # Main event planning pipeline
├── places_results.json        # Generated vendor search results
├── requirements.txt           # Project dependencies
├── .env                       # Environment variables
└── README.md
```

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-event-planner
```

2. Create a virtual environment and activate it:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```env
# TiDB Connection
TIDB_HOST=your_tidb_host
TIDB_PORT=4000
TIDB_USER=your_tidb_user
TIDB_PASSWORD=your_tidb_password
TIDB_DATABASE=your_tidb_database

# API Keys
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional: Gemini Model Configuration
GEMINI_MODEL=gemini-2.5-flash-lite
```


### Workflow

1. **Event Analysis**: The AI analyzes your event description and identifies required vendor categories
2. **Search Query Generation**: Creates optimized Google Places search queries for each vendor type
3. **Vendor Discovery**: Searches for vendors in your specified location
4. **Data Storage**: Stores vendor information and generates embeddings in TiDB
5. **Semantic Matching**: Finds the most relevant vendors using vector similarity
6. **Results**: Displays ranked vendor recommendations by category


## License

[MIT License](LICENSE)
