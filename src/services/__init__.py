"""
מודול שירותים - מכיל שירותים שונים לשימוש במערכת
"""

# ייבוא שירותי WooCommerce
from src.services.store.woocommerce import (
    WooCommerceAPI, 
    CachedWooCommerceAPI, 
    get_cached_woocommerce_api,
    get_woocommerce_api
)

# ייבוא שירותי RAG
from src.services.ai import (
    RAGCore,
    RAGSearch,
    RAGDocument,
    rag_core,
    rag_search,
    rag_document,
    add_document_from_file,
    add_document_from_text,
    search_documents,
    list_documents,
    delete_document,
    get_document_by_id
)

__all__ = [
    # שירותי WooCommerce
    'WooCommerceAPI',
    'CachedWooCommerceAPI',
    'get_cached_woocommerce_api',
    'get_woocommerce_api',
    
    # שירותי RAG
    'RAGCore',
    'RAGSearch',
    'RAGDocument',
    'rag_core',
    'rag_search',
    'rag_document',
    'add_document_from_file',
    'add_document_from_text',
    'search_documents',
    'list_documents',
    'delete_document',
    'get_document_by_id'
] 