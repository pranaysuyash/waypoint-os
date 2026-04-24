"""
whatsapp_formatter.py — Formats traveler-safe PromptBundles for WhatsApp.
"""

from typing import Any, Dict, List, Optional
import re

# =============================================================================
# SECTION 1: FORMATTING UTILS
# =============================================================================

def to_whatsapp_bold(text: str) -> str:
    """Wrap text in WhatsApp bold syntax (*) if not already wrapped."""
    if not text:
        return text
    # Avoid double wrapping if already bolded in some way
    if text.startswith("*") and text.endswith("*"):
        return text
    return f"*{text}*"

def clean_for_whatsapp(text: str) -> str:
    """Clean text for WhatsApp (remove MD-style headers, etc)."""
    if not text:
        return ""
    # Remove markdown headers like ### or ##
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Convert MD bold (**) to WhatsApp bold (*)
    text = text.replace("**", "*")
    return text.strip()

# =============================================================================
# SECTION 2: MAIN FORMATTER
# =============================================================================

class WhatsAppFormatter:
    """
    Formatter for converting internal traveler-safe bundles into WhatsApp messages.
    """

    EMOJI_MAP = {
        "greeting": "👋",
        "question": "❓",
        "itinerary": "🗺️",
        "budget": "💰",
        "confirmation": "✅",
        "warning": "⚠️",
        "flight": "✈️",
        "hotel": "🏨",
        "activity": "🎭",
        "policy": "📋",
        "closing": "✨",
    }

    def format_bundle(self, bundle: Any) -> str:
        """
        Format a traveler-safe PromptBundle for WhatsApp.
        
        Args:
            bundle: PromptBundle object (or dict with user_message)
        """
        user_message = getattr(bundle, "user_message", "")
        if not user_message and isinstance(bundle, dict):
            user_message = bundle.get("user_message", "")

        if not user_message:
            return ""

        # 1. Clean the message
        cleaned_message = clean_for_whatsapp(user_message)

        # 2. Add header if needed
        header = f"{self.EMOJI_MAP['greeting']} *Waypoint Concierge*"
        
        # 3. Add footer
        footer = f"\n\n---\n{self.EMOJI_MAP['closing']} *Powered by Waypoint OS*"

        return f"{header}\n\n{cleaned_message}{footer}"

    def format_itinerary_preview(self, packet: Any) -> str:
        """
        Format a brief itinerary preview for WhatsApp.
        """
        destination = packet.facts.get("resolved_destination", {}).get("value", "Your Trip")
        days = packet.facts.get("trip_duration_days", {}).get("value", "?")
        
        lines = [
            f"{self.EMOJI_MAP['itinerary']} *Itinerary Preview: {destination}*",
            f"⏱️ Duration: {days} days",
            "",
            "*Planned Highlights:*",
        ]
        
        # Add activities if available
        activities = packet.facts.get("itinerary_activities", {}).get("value", [])
        if activities:
            for act in activities[:3]: # Show top 3
                lines.append(f"• {act}")
        else:
            lines.append("• Custom planning in progress...")

        lines.append(f"\n{self.EMOJI_MAP['question']} Should we lock these in?")
        
        return "\n".join(lines)

# Create a singleton instance
whatsapp_formatter = WhatsAppFormatter()
