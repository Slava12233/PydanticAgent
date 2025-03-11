"""
מודול מסד הנתונים
"""

class LazyLoader:
    def __init__(self):
        self._db = None
        self._models = None
    
    @property
    def db(self):
        if self._db is None:
            from .database_manager import DatabaseManager
            self._db = DatabaseManager()
        return self._db
    
    @property
    def models(self):
        if self._models is None:
            from .models.base import Base
            from .models.users import User
            from .models.conversations import Conversation, Message
            from .models.documents import Document, DocumentChunk
            self._models = (Base, User, Conversation, Message, Document, DocumentChunk)
        return self._models

_loader = LazyLoader()
db = _loader.db
Base, User, Conversation, Message, Document, DocumentChunk = _loader.models

__all__ = ['db', 'Base', 'User', 'Conversation', 'Message', 'Document', 'DocumentChunk']
