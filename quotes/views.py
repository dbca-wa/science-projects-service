"""
Quote views - Compatibility layer
"""
from .views.crud import Quotes, QuoteDetail, QuoteRandom
from .views.admin import AddQuotesFromUniques

__all__ = [
    'Quotes',
    'QuoteDetail',
    'QuoteRandom',
    'AddQuotesFromUniques',
]
