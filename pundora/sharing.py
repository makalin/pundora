"""
Joke sharing and social features for Pundora.
"""

import json
import base64
import qrcode
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

class JokeSharing:
    """Handle joke sharing functionality."""
    
    def __init__(self):
        """Initialize sharing system."""
        self.share_templates = {
            'twitter': "😂 New dad joke from Pundora: \"{joke}\" #DadJokes #Pundora #Puns",
            'facebook': "Just got this hilarious dad joke from Pundora: \"{joke}\" 😂",
            'linkedin': "Professional dad joke alert! 🎭 \"{joke}\" - Courtesy of Pundora",
            'whatsapp': "😂 Dad joke incoming: \"{joke}\" - From Pundora",
            'email': "Subject: Daily Dad Joke from Pundora\n\nHere's your daily dose of cringe:\n\n\"{joke}\"\n\n- Pundora Dad Joke Generator",
            'sms': "😂 Dad joke: \"{joke}\" - Pundora"
        }
    
    def generate_share_url(self, joke_data: Dict[str, Any], base_url: str = "http://localhost:8000") -> str:
        """Generate a shareable URL for a joke."""
        # Encode joke data as base64
        joke_json = json.dumps({
            'joke': joke_data['joke'],
            'category': joke_data['category'],
            'humor_level': joke_data['humor_level']
        })
        
        encoded_data = base64.b64encode(joke_json.encode()).decode()
        return f"{base_url}/share/{encoded_data}"
    
    def generate_qr_code(self, joke_data: Dict[str, Any], base_url: str = "http://localhost:8000") -> str:
        """Generate QR code for joke sharing."""
        share_url = self.generate_share_url(joke_data, base_url)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return base64.b64encode(img_bytes.getvalue()).decode()
    
    def get_share_text(self, joke_data: Dict[str, Any], platform: str) -> str:
        """Get formatted text for specific platform."""
        template = self.share_templates.get(platform, self.share_templates['twitter'])
        return template.format(joke=joke_data['joke'])
    
    def get_all_share_options(self, joke_data: Dict[str, Any], base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Get all sharing options for a joke."""
        share_url = self.generate_share_url(joke_data, base_url)
        qr_code = self.generate_qr_code(joke_data, base_url)
        
        return {
            'share_url': share_url,
            'qr_code': qr_code,
            'platforms': {
                'twitter': {
                    'text': self.get_share_text(joke_data, 'twitter'),
                    'url': f"https://twitter.com/intent/tweet?text={self.get_share_text(joke_data, 'twitter')}"
                },
                'facebook': {
                    'text': self.get_share_text(joke_data, 'facebook'),
                    'url': f"https://www.facebook.com/sharer/sharer.php?u={share_url}"
                },
                'linkedin': {
                    'text': self.get_share_text(joke_data, 'linkedin'),
                    'url': f"https://www.linkedin.com/sharing/share-offsite/?url={share_url}"
                },
                'whatsapp': {
                    'text': self.get_share_text(joke_data, 'whatsapp'),
                    'url': f"https://wa.me/?text={self.get_share_text(joke_data, 'whatsapp')}"
                },
                'email': {
                    'text': self.get_share_text(joke_data, 'email'),
                    'url': f"mailto:?subject=Daily%20Dad%20Joke&body={self.get_share_text(joke_data, 'email')}"
                },
                'sms': {
                    'text': self.get_share_text(joke_data, 'sms'),
                    'url': f"sms:?body={self.get_share_text(joke_data, 'sms')}"
                }
            }
        }
    
    def create_joke_card(self, joke_data: Dict[str, Any]) -> str:
        """Create a visual joke card (HTML/CSS)."""
        card_html = f"""
        <div style="
            background: linear-gradient(135deg, #1e40af 0%, #fbbf24 50%, #f97316 100%);
            padding: 30px;
            border-radius: 20px;
            color: white;
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 20px auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        ">
            <div style="text-align: center;">
                <h1 style="margin: 0 0 20px 0; font-size: 2.5em;">🎭 Pundora</h1>
                <div style="
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    backdrop-filter: blur(10px);
                ">
                    <p style="font-size: 1.3em; margin: 0; line-height: 1.4;">
                        "{joke_data['joke']}"
                    </p>
                </div>
                <div style="margin-top: 20px;">
                    <span style="
                        background: rgba(255,255,255,0.2);
                        padding: 8px 16px;
                        border-radius: 20px;
                        margin: 0 5px;
                        font-size: 0.9em;
                    ">{joke_data['category']}</span>
                    <span style="
                        background: rgba(255,255,255,0.2);
                        padding: 8px 16px;
                        border-radius: 20px;
                        margin: 0 5px;
                        font-size: 0.9em;
                    ">{joke_data['humor_level']}</span>
                </div>
                <p style="margin-top: 20px; font-size: 0.9em; opacity: 0.8;">
                    Generated by Pundora - Dad Joke Generator
                </p>
            </div>
        </div>
        """
        return card_html
    
    async def send_joke_email(self, joke_data: Dict[str, Any], recipient: str, sender: str = "Pundora") -> bool:
        """Send joke via email (requires email service configuration)."""
        # This is a placeholder - in a real implementation, you'd use an email service
        # like SendGrid, AWS SES, or SMTP
        try:
            subject = f"Daily Dad Joke from {sender}"
            body = f"""
            Here's your daily dose of dad jokes! 😂
            
            "{joke_data['joke']}"
            
            Category: {joke_data['category']}
            Humor Level: {joke_data['humor_level']}
            
            Generated by Pundora - The AI-powered Dad Joke Generator
            """
            
            # In a real implementation, you would send the email here
            print(f"Email sent to {recipient}: {subject}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def create_joke_meme(self, joke_data: Dict[str, Any]) -> str:
        """Create a meme-style joke image (placeholder)."""
        # This would integrate with an image generation service
        # For now, return a placeholder
        return f"🎭 MEME: {joke_data['joke']} 😂"
    
    def get_share_stats(self, joke_data: Dict[str, Any]) -> Dict[str, int]:
        """Get sharing statistics for a joke."""
        # This would track actual sharing statistics
        return {
            'total_shares': 0,
            'platform_shares': {
                'twitter': 0,
                'facebook': 0,
                'linkedin': 0,
                'whatsapp': 0,
                'email': 0,
                'sms': 0
            }
        }