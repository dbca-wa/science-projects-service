# Quotes App

## Overview
Manages inspirational quotes displayed in the application.

## Architecture

### Layered Structure
- **views/** - HTTP request/response handling
- **services/** - Business logic
- **serializers.py** - Data serialization
- **models.py** - Database models

### Models
- **Quote** - Inspirational quote with text and author

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quotes/` | List quotes (paginated) |
| POST | `/api/v1/quotes/` | Create quote (auth required) |
| GET | `/api/v1/quotes/<id>/` | Get quote detail |
| PUT | `/api/v1/quotes/<id>/` | Update quote (auth required) |
| DELETE | `/api/v1/quotes/<id>/` | Delete quote (auth required) |
| GET | `/api/v1/quotes/random/` | Get random quote |
| POST | `/api/v1/quotes/load-from-file/` | Load quotes from file (admin) |

### Services

**QuoteService**
- `list_quotes()` - Get all quotes
- `get_quote(pk)` - Get quote by ID
- `get_random_quote()` - Get random quote
- `create_quote(data)` - Create new quote
- `update_quote(pk, data)` - Update quote
- `delete_quote(pk)` - Delete quote
- `load_quotes_from_file()` - Load from unique_quotes.txt
- `bulk_create_quotes(quotes_data)` - Bulk create quotes

## Testing

```bash
cd backend
poetry run python manage.py test quotes
```

## Usage

```python
from quotes.services import QuoteService

# Get random quote
quote = QuoteService.get_random_quote()

# Create quote
quote = QuoteService.create_quote({
    "text": "The only way to do great work is to love what you do.",
    "author": "Steve Jobs"
})
```
