"""
AI-powered joke generation service using OpenAI.
"""

import asyncio
import random
from typing import Dict, List, Optional
import openai
from .config import config

class JokeGenerator:
    """AI-powered dad joke generator."""
    
    def __init__(self):
        """Initialize the joke generator with OpenAI client."""
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
        # Pre-defined joke templates for fallback
        self.fallback_jokes = {
            "general": [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a fake noodle? An impasta!",
                "Why did the scarecrow win an award? He was outstanding in his field!"
            ],
            "puns": [
                "I'm reading a book about anti-gravity. It's impossible to put down!",
                "Why don't skeletons fight each other? They don't have the guts!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the math book look so sad? Because it had too many problems!",
                "What do you call a fish wearing a bowtie? So-fish-ticated!"
            ],
            "knock-knock": [
                "Knock knock. Who's there? Lettuce. Lettuce who? Lettuce in, it's cold out here!",
                "Knock knock. Who's there? Boo. Boo who? Don't cry, it's just a joke!",
                "Knock knock. Who's there? Orange. Orange who? Orange you glad I didn't say banana?",
                "Knock knock. Who's there? Atch. Atch who? Bless you!",
                "Knock knock. Who's there? Cow says. Cow says who? No, cow says moo!"
            ],
            "wordplay": [
                "I used to be a baker, but I couldn't make enough dough!",
                "Why did the bicycle fall over? Because it was two tired!",
                "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!",
                "Why don't you ever see elephants hiding in trees? Because they're really good at it!",
                "What do you call a can opener that doesn't work? A can't opener!"
            ],
            "dad-classics": [
                "Hi hungry, I'm dad!",
                "I'm not a photographer, but I can picture us together!",
                "Did you hear about the claustrophobic astronaut? He just needed a little space!",
                "Why don't dad jokes work on paper? Because they're tear-able!",
                "What do you call a dad joke that's not funny? A faux pa!"
            ],
            "food": [
                "Why did the coffee file a police report? It got mugged!",
                "What do you call a nosy pepper? Jalapeño business!",
                "Why don't you ever see elephants hiding in trees? Because they're really good at it!",
                "What do you call a fake noodle? An impasta!",
                "Why did the tomato turn red? Because it saw the salad dressing!"
            ],
            "animals": [
                "What do you call a sleeping bull? A bulldozer!",
                "Why don't fish play basketball? Because they're afraid of the net!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the chicken go to the seance? To talk to the other side!",
                "What do you call a dog magician? A labracadabrador!"
            ],
            "technology": [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "What do you call a computer that sings? A Dell!",
                "Why did the programmer quit his job? He didn't get arrays!",
                "What's a programmer's favorite hangout place? The Foo Bar!",
                "Why do Java developers wear glasses? Because they can't C#!"
            ]
        }
    
    async def generate_joke(
        self, 
        category: str = "general", 
        humor_level: str = "medium",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a dad joke using AI or fallback to pre-defined jokes.
        
        Args:
            category: Joke category
            humor_level: Level of cringe (mild, medium, extra)
            custom_prompt: Custom prompt for joke generation
            
        Returns:
            Dictionary containing the joke and metadata
        """
        try:
            # Try AI generation first
            joke = await self._generate_ai_joke(category, humor_level, custom_prompt)
            return {
                "joke": joke,
                "category": category,
                "humor_level": humor_level,
                "source": "ai"
            }
        except Exception as e:
            # Fallback to pre-defined jokes
            print(f"AI generation failed: {e}. Using fallback jokes.")
            return self._get_fallback_joke(category, humor_level)
    
    async def _generate_ai_joke(
        self, 
        category: str, 
        humor_level: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Generate a joke using OpenAI API."""
        
        # Build the prompt based on category and humor level
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_prompt(category, humor_level)
        
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a master of dad jokes. Generate clean, family-friendly dad jokes that are punny and groan-worthy. Keep responses concise and funny."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        
        joke = response.choices[0].message.content.strip()
        
        # Clean up the joke (remove quotes, extra formatting)
        joke = joke.replace('"', '').replace("'", '').strip()
        
        return joke
    
    def _build_prompt(self, category: str, humor_level: str) -> str:
        """Build a prompt for AI joke generation."""
        
        humor_descriptions = {
            "mild": "mildly punny and family-friendly",
            "medium": "moderately cringy and punny",
            "extra": "extremely cringy, groan-worthy, and over-the-top punny"
        }
        
        category_descriptions = {
            "general": "general dad jokes",
            "puns": "pun-based jokes",
            "knock-knock": "knock-knock jokes",
            "wordplay": "wordplay and double entendre jokes",
            "dad-classics": "classic dad joke formats",
            "food": "food-related puns and jokes",
            "animals": "animal-related puns and jokes",
            "technology": "technology and programming jokes"
        }
        
        humor_desc = humor_descriptions.get(humor_level, "moderately punny")
        category_desc = category_descriptions.get(category, "general dad jokes")
        
        return f"Generate a {humor_desc} {category_desc}. Make it a proper dad joke that would make people groan and roll their eyes. Keep it clean and family-friendly."
    
    def _get_fallback_joke(self, category: str, humor_level: str) -> Dict[str, str]:
        """Get a random joke from the fallback collection."""
        
        # Get jokes for the category, fallback to general if not found
        jokes = self.fallback_jokes.get(category, self.fallback_jokes["general"])
        
        # If humor level is "extra", we might want to add some extra cringe
        if humor_level == "extra" and random.random() < 0.3:
            jokes = [joke + " 😂" for joke in jokes]
        
        selected_joke = random.choice(jokes)
        
        return {
            "joke": selected_joke,
            "category": category,
            "humor_level": humor_level,
            "source": "fallback"
        }
    
    def get_categories(self) -> List[str]:
        """Get list of available joke categories."""
        return list(self.fallback_jokes.keys())
    
    def get_humor_levels(self) -> List[str]:
        """Get list of available humor levels."""
        return ["mild", "medium", "extra"]