"""
External integrations module for Chatbuddy MVP.

This module contains integrations with external services:
- Database connections and operations
- Webshop API integrations
- Marketing automation services
- Social media platforms
- Vector database operations
"""

# Integration exports (will be implemented)
# from .database import supabase_client, vector_client
# from .webshop import shoprenter_client, unas_client
# from .marketing import email_service, sms_service
# from .social_media import facebook_client, whatsapp_client

# Placeholder exports for now
supabase_client = None
vector_client = None
shoprenter_client = None
unas_client = None
email_service = None
sms_service = None
facebook_client = None
whatsapp_client = None

__all__ = [
    "supabase_client",
    "vector_client",
    "shoprenter_client", 
    "unas_client",
    "email_service",
    "sms_service",
    "facebook_client",
    "whatsapp_client"
]
