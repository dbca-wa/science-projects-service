"""
Quote views
"""

from .admin import AddQuotesFromUniques
from .crud import QuoteDetail, QuoteRandom, Quotes

__all__ = [
    "Quotes",
    "QuoteDetail",
    "QuoteRandom",
    "AddQuotesFromUniques",
]
