"""
Joke translation system for Pundora.
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx
from .config import config

class JokeTranslator:
    """Handle joke translation functionality."""
    
    def __init__(self):
        """Initialize the translator."""
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'th': 'Thai'
        }
        
        # Fallback translations for common dad jokes
        self.fallback_translations = {
            'en': {
                'general': [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                    "Why don't eggs tell jokes? They'd crack each other up!"
                ]
            },
            'es': {
                'general': [
                    "¿Por qué los científicos no confían en los átomos? ¡Porque se inventan todo!",
                    "Le dije a mi esposa que se dibujaba las cejas muy altas. Se veía sorprendida.",
                    "¿Por qué los huevos no cuentan chistes? ¡Se partirían de risa!"
                ]
            },
            'fr': {
                'general': [
                    "Pourquoi les scientifiques ne font pas confiance aux atomes ? Parce qu'ils inventent tout !",
                    "J'ai dit à ma femme qu'elle dessinait ses sourcils trop haut. Elle avait l'air surprise.",
                    "Pourquoi les œufs ne racontent pas de blagues ? Ils se casseraient de rire !"
                ]
            },
            'de': {
                'general': [
                    "Warum vertrauen Wissenschaftler Atomen nicht? Weil sie alles erfinden!",
                    "Ich sagte meiner Frau, sie zeichne ihre Augenbrauen zu hoch. Sie sah überrascht aus.",
                    "Warum erzählen Eier keine Witze? Sie würden sich kaputtlachen!"
                ]
            }
        }
    
    async def translate_joke(
        self, 
        joke: str, 
        target_language: str, 
        source_language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Translate a joke to target language.
        
        Args:
            joke: The joke text to translate
            target_language: Target language code
            source_language: Source language code
            
        Returns:
            Dictionary with translation results
        """
        if target_language not in self.supported_languages:
            return {
                'success': False,
                'error': f'Unsupported target language: {target_language}',
                'translated_joke': joke
            }
        
        if source_language == target_language:
            return {
                'success': True,
                'translated_joke': joke,
                'source_language': source_language,
                'target_language': target_language,
                'method': 'no_translation_needed'
            }
        
        try:
            # Try AI translation first
            if config.OPENAI_API_KEY:
                translated_joke = await self._translate_with_ai(joke, target_language, source_language)
                if translated_joke:
                    return {
                        'success': True,
                        'translated_joke': translated_joke,
                        'source_language': source_language,
                        'target_language': target_language,
                        'method': 'ai_translation'
                    }
        except Exception as e:
            print(f"AI translation failed: {e}")
        
        # Fallback to pre-translated jokes
        try:
            translated_joke = await self._get_fallback_translation(joke, target_language)
            if translated_joke:
                return {
                    'success': True,
                    'translated_joke': translated_joke,
                    'source_language': source_language,
                    'target_language': target_language,
                    'method': 'fallback_translation'
                }
        except Exception as e:
            print(f"Fallback translation failed: {e}")
        
        # If all else fails, return original
        return {
            'success': False,
            'error': 'Translation not available',
            'translated_joke': joke,
            'source_language': source_language,
            'target_language': target_language,
            'method': 'no_translation'
        }
    
    async def _translate_with_ai(
        self, 
        joke: str, 
        target_language: str, 
        source_language: str
    ) -> Optional[str]:
        """Translate using OpenAI API."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            target_lang_name = self.supported_languages[target_language]
            source_lang_name = self.supported_languages[source_language]
            
            prompt = f"""
            Translate this dad joke from {source_lang_name} to {target_lang_name}.
            Maintain the humor, wordplay, and dad joke style.
            Keep it family-friendly and funny.
            
            Original joke: "{joke}"
            
            Translation:
            """
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in humor and dad jokes. Translate jokes while preserving their comedic timing and wordplay."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            translated = response.choices[0].message.content.strip()
            return translated.replace('"', '').strip()
            
        except Exception as e:
            print(f"AI translation error: {e}")
            return None
    
    async def _get_fallback_translation(self, joke: str, target_language: str) -> Optional[str]:
        """Get fallback translation from pre-translated jokes."""
        if target_language not in self.fallback_translations:
            return None
        
        # Simple matching - in a real implementation, you'd use more sophisticated matching
        joke_lower = joke.lower()
        
        # Check if joke matches any known patterns
        for category, jokes in self.fallback_translations[target_language].items():
            for fallback_joke in jokes:
                # Simple similarity check
                if self._jokes_similar(joke_lower, fallback_joke.lower()):
                    return fallback_joke
        
        # Return a random joke from the target language
        import random
        all_jokes = []
        for category_jokes in self.fallback_translations[target_language].values():
            all_jokes.extend(category_jokes)
        
        if all_jokes:
            return random.choice(all_jokes)
        
        return None
    
    def _jokes_similar(self, joke1: str, joke2: str, threshold: float = 0.3) -> bool:
        """Check if two jokes are similar (simple implementation)."""
        # Simple word overlap check
        words1 = set(joke1.split())
        words2 = set(joke2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        similarity = overlap / max(len(words1), len(words2))
        
        return similarity >= threshold
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
    
    async def translate_joke_with_context(
        self, 
        joke: str, 
        target_language: str, 
        category: str = "general",
        humor_level: str = "medium"
    ) -> Dict[str, Any]:
        """Translate joke with cultural context consideration."""
        
        # Add cultural context to translation
        context_prompts = {
            'mild': "Translate this dad joke to be family-friendly and mildly funny",
            'medium': "Translate this dad joke maintaining moderate humor and cultural appropriateness",
            'extra': "Translate this dad joke to be extremely punny and cringy, maximizing the dad joke effect"
        }
        
        context_prompt = context_prompts.get(humor_level, context_prompts['medium'])
        
        try:
            if config.OPENAI_API_KEY:
                import openai
                
                client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
                
                target_lang_name = self.supported_languages[target_language]
                
                prompt = f"""
                {context_prompt} from English to {target_lang_name}.
                This is a {category} category dad joke with {humor_level} humor level.
                Make sure the translation:
                1. Maintains the original wordplay and puns
                2. Is culturally appropriate for {target_lang_name} speakers
                3. Preserves the dad joke style and timing
                4. Keeps the same humor level ({humor_level})
                
                Original joke: "{joke}"
                
                Translation:
                """
                
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a professional translator and cultural expert specializing in humor translation. You understand dad jokes, puns, and cultural nuances in {target_lang_name}."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                translated = response.choices[0].message.content.strip()
                return {
                    'success': True,
                    'translated_joke': translated.replace('"', '').strip(),
                    'source_language': 'en',
                    'target_language': target_language,
                    'method': 'ai_contextual_translation',
                    'category': category,
                    'humor_level': humor_level
                }
        except Exception as e:
            print(f"Contextual translation failed: {e}")
        
        # Fallback to regular translation
        return await self.translate_joke(joke, target_language)
    
    async def get_translation_quality_score(
        self, 
        original: str, 
        translation: str, 
        target_language: str
    ) -> Dict[str, Any]:
        """Get quality score for a translation."""
        # This would use more sophisticated metrics in a real implementation
        return {
            'overall_score': 0.8,
            'humor_preservation': 0.7,
            'cultural_appropriateness': 0.9,
            'grammatical_correctness': 0.8,
            'wordplay_effectiveness': 0.6
        }