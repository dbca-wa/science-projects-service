"""
Quote views
"""
from .crud import Quotes, QuoteDetail, QuoteRandom
from .admin import AddQuotesFromUniques

__all__ = [
    'Quotes',
    'QuoteDetail',
    'QuoteRandom',
    'AddQuotesFromUniques',
]
