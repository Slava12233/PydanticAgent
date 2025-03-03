"""
מודול handlers - מכיל מודולים לטיפול בפקודות ואירועים שונים
"""

from src.handlers.store_handler import (
    handle_store_dashboard,
    handle_connect_store_start,
    handle_store_url,
    handle_consumer_key,
    handle_consumer_secret,
    handle_confirmation,
    handle_store_stats,
    handle_store_orders,
    handle_store_products,
    handle_store_callback,
    handle_store_customers,
    handle_store_inventory,
    WAITING_FOR_STORE_URL,
    WAITING_FOR_CONSUMER_KEY,
    WAITING_FOR_CONSUMER_SECRET,
    WAITING_FOR_CONFIRMATION
)

from src.handlers.admin_handler import (
    handle_admin_command,
    handle_admin_users,
    handle_admin_stats,
    handle_admin_docs,
    handle_admin_models,
    handle_admin_config,
    handle_admin_notify,
    handle_admin_callback,
    handle_list_users,
    handle_grant_admin,
    handle_revoke_admin,
    handle_block_user,
    handle_unblock_user,
    admin_required
)

from src.handlers.error_handler import (
    ErrorType,
    handle_misunderstanding,
    handle_api_error,
    generate_clarification_questions,
    suggest_similar_intents,
    get_error_response
)

__all__ = [
    # מ-store_handler
    'handle_store_dashboard',
    'handle_connect_store_start',
    'handle_store_url',
    'handle_consumer_key',
    'handle_consumer_secret',
    'handle_confirmation',
    'handle_store_stats',
    'handle_store_orders',
    'handle_store_products',
    'handle_store_callback',
    'handle_store_customers',
    'handle_store_inventory',
    'WAITING_FOR_STORE_URL',
    'WAITING_FOR_CONSUMER_KEY',
    'WAITING_FOR_CONSUMER_SECRET',
    'WAITING_FOR_CONFIRMATION',
    
    # מ-admin_handler
    'handle_admin_command',
    'handle_admin_users',
    'handle_admin_stats',
    'handle_admin_docs',
    'handle_admin_models',
    'handle_admin_config',
    'handle_admin_notify',
    'handle_admin_callback',
    'handle_list_users',
    'handle_grant_admin',
    'handle_revoke_admin',
    'handle_block_user',
    'handle_unblock_user',
    'admin_required',
    
    # מ-error_handler
    'ErrorType',
    'handle_misunderstanding',
    'handle_api_error',
    'generate_clarification_questions',
    'suggest_similar_intents',
    'get_error_response'
] 