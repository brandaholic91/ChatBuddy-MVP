"""
Social Media Agent - Facebook Messenger & WhatsApp Business Integration.

This module implements the social media agent for handling
Facebook Messenger and WhatsApp Business communications.
"""

from .agent import create_social_media_agent, SocialMediaDependencies, SocialMediaResponse

__all__ = [
    "create_social_media_agent",
    "SocialMediaDependencies", 
    "SocialMediaResponse"
]
