# AI Event Planner

A modular Python application for collecting, enriching, and storing event vendor data. This project uses Google Places API for vendor information and Gemini Embedding API for text embeddings. **Now with AI-powered event planning functionality!**

## Features

- 🏪 Search for decoration vendors using Google Places API
- 🧠 Generate embeddings using Gemini embedding-001 model with built-in rate limiting (100 RPM)
- 💾 Store vendor data with embeddings in a TiDB database
- 🎯 **NEW: AI Event Planning** - Describe your event and get personalized vendor recommendations
- 🔍 **Smart Search** - Convert event descriptions to optimized search queries using Gemini LLM
- 📊 **Similarity Matching** - Find top 20 vendors using embedding similarity scores
- 🏗️ Modular architecture for maintainability and extensibility

## New Event Planning Functionality

### Quick Start for Event Planning

```bash
# Simple CLI for event planning
python plan_event.py "birthday party for 8-year-old with superhero theme"

# Or run interactively
python plan_event.py
```

### How It Works

1. **Describe Your Event**: Tell the AI what kind of event you want to organize
2. **Smart Query Generation**: Gemini LLM converts your description into an optimized search query
3. **Embedding Similarity**: The system finds vendors whose descriptions are most similar to your needs
4. **Top 20 Results**: Get ranked vendor recommendations with similarity scores

### Example Event Types

- `"corporate conference for 200 people with modern decorations"`
- `"outdoor wedding reception with floral arrangements"`
- `"baby shower with pastel color theme"`
- `"birthday party for 5-year-old with princess theme"`
- `"anniversary celebration with elegant decorations"`

## Project Structure

```
ai-event-planner/
├── src/
│   ├── api/
│   │   ├── places.py          # Google Places API integration
│   │   ├── embeddings.py      # Gemini Embeddings API integration
│   │   └── __init__.py
│   ├── db/
│   │   ├── database.py        # Database operations
│   │   └── __init__.py
│   ├── models/
│   │   ├── vendor.py          # Vendor data model
│   │   └── __init__.py
│   ├── services/
│   │   ├── vendor_collector.py # Vendor collection service
│   │   ├── event_planner.py   # NEW: AI event planning service
│   │   └── __init__.py
│   ├── utils/
│   │   ├── config.py          # Configuration settings
│   │   ├── logger.py          # Logging utilities
│   │   └── __init__.py
│   └── __init__.py
├── main.py                    # Main script with menu options
├── plan_event.py              # NEW: Simple CLI for event planning
├── requirements.txt           # Project dependencies
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
```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GEMINI_API_KEY=your_gemini_api_key
TIDB_HOST=your_tidb_host
TIDB_PORT=4000
TIDB_USER=your_tidb_user
TIDB_PASSWORD=your_tidb_password
TIDB_DATABASE=your_tidb_database
```

## Database Setup

Create the necessary table in your TiDB database:

```sql
CREATE TABLE gurugram_decoration_vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    place_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255),
    name VARCHAR(255),
    display_name JSON,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    formatted_address VARCHAR(512),
    short_formatted_address VARCHAR(255),
    plus_code_global VARCHAR(20),
    plus_code_compound VARCHAR(50),
    primary_type VARCHAR(100),
    business_types JSON,
    rating DECIMAL(3, 2),
    user_rating_count INT,
    price_level INT,
    business_status VARCHAR(50),
    national_phone VARCHAR(30),
    international_phone VARCHAR(30),
    website_uri VARCHAR(512),
    google_maps_uri VARCHAR(512),
    delivery BOOLEAN,
    takeout BOOLEAN,
    opening_hours JSON,
    utc_offset_minutes INT,
    accepts_cash_only BOOLEAN,
    accepts_nfc BOOLEAN,
    accepts_credit_cards BOOLEAN,
    photos_count INT,
    specialties VARCHAR(255),
    embedding JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Usage

Run the main script to collect vendors:

```bash
python collect_vendors_gemini.py
```

## API Rate Limiting

The application includes built-in rate limiting mechanisms:

- **Gemini Embeddings API**: Limited to 100 requests per minute (100 RPM) using a token bucket algorithm
- Token bucket automatically refills based on elapsed time
- No manual delay or sleep required in the vendor collection process

This ensures the application respects API usage limits while maximizing throughput.

## License

[MIT License](LICENSE)
