"""
מודול שירותים - מכיל שירותים שונים לשימוש במערכת
"""

# ייבוא שירותי WooCommerce
from src.services.woocommerce import (
    WooCommerceAPI, 
    CachedWooCommerceAPI, 
    get_cached_woocommerce_api,
    get_woocommerce_api
)

# ייבוא שירותי RAG
from src.services.rag_service import (
    RAGService,
    rag_service,
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
    'RAGService',
    'rag_service',
    'add_document_from_file',
    'add_document_from_text',
    'search_documents',
    'list_documents',
    'delete_document',
    'get_document_by_id'
] 