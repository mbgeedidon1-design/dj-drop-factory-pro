"""DJ Drop Factory Pro v5.0 - AI Drop Script Generator"""
import random
from config import Config

class DropGenerator:
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self):
        return {
            "intro": {
                "hype": [
                    "Yo yo yo! It's your boy {dj_name} in the building! You already know what time it is! Let's get this party STARTED!",
                    "Ladies and gentlemen, boys and girls! {dj_name} is in the house and we about to TURN UP!",
                    "Wake up! Wake up! {dj_name} on the decks and we going ALL NIGHT LONG!",
                    "Yeah yeah yeah! It's {dj_name} and I'm taking over! Let's GO!",
                    "Buckle up! {dj_name} is about to drop something CRAZY!",
                ],
                "luxury": [
                    "Welcome to an exclusive experience. You are now in the world of {dj_name}. Sit back and enjoy the finest selection.",
                    "Elegance. Sophistication. {dj_name}. This is premium sound at its absolute best.",
                    "You have arrived. {dj_name} presents a curated journey through sound. Welcome.",
                    "The wait is over. {dj_name} is here with nothing but the finest beats.",
                ],
                "aggressive": [
                    "BOW DOWN! {dj_name} is in the building and I'm taking NO PRISONERS!",
                    "SHUT IT DOWN! {dj_name} on the attack! This is WAR!",
                    "You are NOT ready for this! {dj_name} about to DESTROY these decks!",
                    "NO MERCY! {dj_name} is here and it's about to get VIOLENT!",
                    "Step aside! {dj_name} is coming through and NOTHING can stop me!",
                ],
                "dark": [
                    "The lights go down. The crowd goes silent. {dj_name} emerges from the shadows.",
                    "Welcome to the dark side. {dj_name} is your guide through the underground.",
                    "They fear what they don't understand. {dj_name} brings the darkness.",
                    "In the depths of the night, {dj_name} calls. Will you answer?",
                ],
                "smooth": [
                    "Smooth operator {dj_name} in the mix. Just relax and let the music flow.",
                    "Easy does it. {dj_name} here to set the perfect mood.",
                    "No rush, no stress. Just {dj_name} and good vibrations.",
                    "Let the groove take over. {dj_name} got you covered.",
                ],
                "festival": [
                    "FESTIVAL MODE ACTIVATED! {dj_name} on the main stage! ARE YOU WITH ME?!",
                    "Thousands of voices, one heartbeat. {dj_name} controls the energy!",
                    "This is the moment! {dj_name} on the biggest stage in the world!",
                    "Hands up! Voices loud! {dj_name} is about to make HISTORY!",
                ],
            },
            "sweeper": {
                "hype": [
                    "You're listening to {dj_name}! The hottest DJ in the game right now!",
                    "Don't touch that dial! {dj_name} got more heat coming your way!",
                    "It's {dj_name}! Keeping it live and direct!",
                ],
                "luxury": [
                    "An exclusive presentation by {dj_name}. Only the finest.",
                    "You are experiencing {dj_name}. Pure class, pure sound.",
                ],
                "aggressive": [
                    "WARNING! {dj_name} incoming! Clear the dancefloor!",
                    "Sound the alarm! {dj_name} is taking over!",
                ],
                "dark": [
                    "From the underground... {dj_name}.",
                    "The darkness speaks... through {dj_name}.",
                ],
                "smooth": [
                    "Smooth sounds by {dj_name}.",
                    "Your smooth ride with {dj_name} continues.",
                ],
                "festival": [
                    "Festival vibes with {dj_name}!",
                    "Main stage energy! {dj_name}!",
                ],
            },
            "hype": {
                "hype": [
                    "LET'S GOOOOO! {dj_name} IS HERE!",
                    "TURN IT UP! {dj_name} ABOUT TO GO CRAZY!",
                    "EVERYBODY JUMP! {dj_name}!",
                ],
                "aggressive": [
                    "DESTROY! {dj_name}!",
                    "ATTACK! {dj_name}!",
                    "NO FEAR! {dj_name}!",
                ],
                "festival": [
                    "FESTIVAL! {dj_name}!",
                    "MAIN STAGE! {dj_name}!",
                ],
            },
            "promo": {
                "hype": [
                    "This is {dj_name}! Catch me live every weekend! Follow the movement!",
                    "You want the heat? You got {dj_name}! Bookings open now!",
                ],
                "luxury": [
                    "Experience {dj_name}. Premium events. Premium sound. Exclusive bookings.",
                    "For the discerning ear. {dj_name}. Available for select engagements.",
                ],
            },
            "producer_tag": {
                "aggressive": [
                    "{dj_name} on the beat!",
                    "You already know... {dj_name}!",
                    "That's {dj_name} production!",
                ],
                "hype": [
                    "{dj_name}! FIRE!",
                    "{dj_name} made this!",
                ],
            },
            "radio_id": {
                "smooth": [
                    "You're tuned in to {dj_name}. Your favorite DJ, your favorite station.",
                    "This is {dj_name} on your radio. Thanks for listening.",
                ],
                "luxury": [
                    "A premium broadcast featuring {dj_name}.",
                    "The {dj_name} show. Exclusive radio content.",
                ],
            },
            "crowd_call": {
                "hype": [
                    "SAY MY NAME! {dj_name}! LOUDER! {dj_name}!",
                    "I can't hear you! {dj_name}! LET ME HEAR YOU!",
                    "When I say {dj_name}, you say FIRE! {dj_name}! FIRE!",
                ],
                "festival": [
                    "PUT YOUR HANDS UP FOR {dj_name}!",
                    "SCREAM IF YOU LOVE {dj_name}!",
                ],
            },
        }

    def generate_script(self, dj_name, genre, drop_type, mood, energy, city=None, 
                       use_stutter=False, user_stutter=None, training_example=None):
        """Generate a DJ drop script"""

        # Get templates for drop type and mood
        type_templates = self.templates.get(drop_type, self.templates["intro"])
        mood_templates = type_templates.get(mood, type_templates.get("hype", type_templates.get("aggressive", list(type_templates.values())[0])))

        if not mood_templates:
            mood_templates = ["{dj_name} in the mix!"]

        # Select random template
        template = random.choice(mood_templates)

        # Fill in variables
        script = template.format(dj_name=dj_name)

        # Add city reference if provided
        if city and random.random() > 0.3:
            city_phrases = [
                f" Repping {city}!",
                f" Straight outta {city}!",
                f" {city} stand up!",
                f" From {city} to the world!",
            ]
            script += random.choice(city_phrases)

        # Add genre-specific flavor
        genre_flavor = {
            "amapiano": [" Amapiano to the world!", " Piano piano!", " The Yanos!"],
            "dancehall": [" Dancehall massive!", " Pull up!", " Big riddim!"],
            "afrobeat": [" Afrobeat takeover!", " From the motherland!", " Afro-fusion!"],
            "trap": [" Trap shit!", " 808s and heartbreak!", " Straight trap!"],
            "club_banger": [" Club banger!", " This one's for the club!", " Turn the club up!"],
        }

        if genre in genre_flavor and random.random() > 0.5:
            script += random.choice(genre_flavor[genre])

        # Apply stutter if requested
        if use_stutter or user_stutter:
            if user_stutter:
                script = f"{user_stutter}! {script}"
            else:
                # Auto-stutter on DJ name
                first_letter = dj_name[0] if dj_name else "D"
                stutter = f"{first_letter}-{first_letter}-{first_letter}-{dj_name}!"
                script = f"{stutter} {script}"

        # Energy-based modifications
        if energy >= 9:
            script = script.upper().replace("!", "!!!")
        elif energy <= 3:
            script = script.lower()

        return script.strip()

    def generate_training_based(self, dj_name, training_example):
        """Generate a script based on training example"""
        # Simple pattern extraction and replacement
        # Replace names in the example with the new DJ name
        import re

        # Find common DJ name patterns in the example
        words = training_example.split()
        potential_names = [w for w in words if w[0].isupper() and len(w) > 2 and w not in ["The", "DJ", "MC", "And", "You", "Are"]]

        if potential_names:
            # Replace the most common capitalized word (likely the DJ name)
            name_to_replace = potential_names[0]
            script = training_example.replace(name_to_replace, dj_name)
        else:
            script = training_example

        return script

generator = DropGenerator()
