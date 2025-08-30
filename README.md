# AI Event Planner

An intelligent Python application that helps plan events by analyzing event descriptions and finding the most suitable vendors using AI-powered semantic matching. The system leverages Google Places API for vendor discovery, Gemini LLM for intelligent query generation, and vector embeddings for semantic similarity matching.

## ✨ Key Features

- **🚀 Multithreaded Processing**: Concurrent LLM requests, embedding generation, and API calls for optimal performance
- **🎯 AI-Powered Analysis**: Intelligent event description analysis using Gemini LLM
- **🔍 Smart Vendor Discovery**: Automated Google Places API searches with rate limiting
- **📊 Semantic Matching**: Vector similarity search for finding the most relevant vendors
- **💾 Efficient Storage**: TiDB vector database for scalable embedding storage
- **⚡ Rate Limiting**: Built-in rate limiting for all API calls to respect service limits

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


## 🔧 Multithreading Architecture

The application uses multithreading to significantly improve performance while respecting API rate limits:

### Threading Configuration
```python
THREADING_CONFIG = {
    'max_llm_workers': 5,           # Max concurrent LLM requests
    'max_embedding_workers': 10,    # Max concurrent embedding requests  
    'max_places_workers': 5,        # Max concurrent place searches
    'max_place_detail_workers': 10  # Max concurrent place detail fetches
}
```

### Performance Improvements
- **LLM Batch Processing**: Process multiple prompts concurrently with rate limiting
- **Embedding Generation**: Batch embedding creation for multiple texts simultaneously
- **Places API**: Concurrent place searches and detail fetching
- **Rate Limiting**: Token bucket algorithm ensures API limits are respected

### Testing Performance
Run the multithreading performance tests:
```bash
python test_multithreading.py
```

## 🔄 Workflow

1. **Event Analysis**: The AI analyzes your event description and identifies required vendor categories
2. **Search Query Generation**: Creates optimized Google Places search queries for each vendor type  
3. **Concurrent Vendor Discovery**: Searches for vendors in parallel across multiple threads
4. **Batch Data Processing**: Generates embeddings for all vendors concurrently
5. **Efficient Storage**: Stores vendor information and embeddings in TiDB
6. **Semantic Matching**: Finds the most relevant vendors using vector similarity
7. **Results**: Displays ranked vendor recommendations by category


## 🛡️ Rate Limiting

All API integrations include sophisticated rate limiting to prevent hitting service limits:

### Token Bucket Algorithm
- **Gemini LLM**: 60 requests per minute
- **Gemini Embeddings**: 100 requests per minute  
- **Google Places**: 100 requests per second

### Implementation Features
- Thread-safe token bucket with automatic refill
- Graceful waiting when rate limits are reached
- Configurable rate limits per service
- Detailed logging of rate limit events

## 🚀 Usage

Run the main event planning pipeline:
```bash
python main.py
```

The application will:
1. Analyze the sample event description
2. Generate vendor search queries
3. Search for vendors using multithreading
4. Store results with concurrent embedding generation
5. Perform semantic matching
6. Display ranked recommendations

## 📊 Performance Benefits

With multithreading enabled, you can expect:
- **2-5x faster** LLM processing for multiple queries
- **3-10x faster** embedding generation for large datasets
- **2-4x faster** place searches and detail fetching
- Maintained API rate limit compliance
- Better resource utilization

## License

[MIT License](LICENSE)
