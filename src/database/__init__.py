"""
Database module
"""

class LazyLoader:
    def __init__(self):
        self._db = None
        self._models = None
    
    @property
    def db(self):
        if self._db is None:
            from .database import db
            self._db = db
        return self._db
    
    @property
    def models(self):
        if self._models is None:
            from src.models.database import Base, User, Conversation, Message, Document, DocumentChunk
            self._models = (Base, User, Conversation, Message, Document, DocumentChunk)
        return self._models

_loader = LazyLoader()
db = _loader.db
Base, User, Conversation, Message, Document, DocumentChunk = _loader.models

__all__ = ['db', 'Base', 'User', 'Conversation', 'Message', 'Document', 'DocumentChunk']
