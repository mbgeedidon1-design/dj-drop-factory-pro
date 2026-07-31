"""DJ Drop Factory Pro v5.0 - Discover Screen Static Data"""

DISCOVER_DATA = {
    "dj_groups": [
        {"name": "Major Lazer", "origin": "USA/Jamaica", "style": "Dancehall / EDM", "activities": "Global touring, Mad Decent label"},
        {"name": "Black Coffee", "origin": "South Africa", "style": "Deep House / Afro", "activities": "Grammy winner, Soulistic Music"},
        {"name": "Diplo", "origin": "USA", "style": "Multi-genre", "activities": "Mad Decent, Major Lazer, Silk City"},
        {"name": "DJ Snake", "origin": "France", "style": "EDM / Trap", "activities": "Premiere Classe label, global hits"},
        {"name": "Kabza De Small", "origin": "South Africa", "style": "Amapiano", "activities": "Piano Hub, Scorpion Kings"},
        {"name": "DJ Maphorisa", "origin": "South Africa", "style": "Amapiano / Gqom", "activities": "BlaqBoy Music, hit producer"},
        {"name": "Daft Punk (Legacy)", "origin": "France", "style": "Electronic", "activities": "Influenced modern EDM production"},
        {"name": "Swedish House Mafia", "origin": "Sweden", "style": "Progressive House", "activities": "Reunion tours, stadium shows"},
        {"name": "Tiësto", "origin": "Netherlands", "style": "Trance / EDM", "activities": "Musical Freedom, global residencies"},
        {"name": "David Guetta", "origin": "France", "style": "EDM / Pop", "activities": "Jack Back Records, festival headliner"},
        {"name": "DJ Khaled", "origin": "USA", "style": "Hip-Hop", "activities": "We The Best Music, anthems"},
        {"name": "Calvin Harris", "origin": "UK", "style": "EDM / Pop", "activities": "Fly Eye Records, hitmaker"},
    ],
    "streaming_apps": [
        {"name": "Spotify", "category": "Music", "price": "Free / Premium", "platform": "All", "free_tier": True},
        {"name": "Apple Music", "category": "Music", "price": "$10.99/mo", "platform": "All", "free_tier": False},
        {"name": "Tidal", "category": "Hi-Fi Music", "price": "$10.99-$19.99/mo", "platform": "All", "free_tier": False},
        {"name": "SoundCloud", "category": "Independent", "price": "Free / Pro", "platform": "All", "free_tier": True},
        {"name": "Beatport", "category": "DJ Music", "price": "Per track", "platform": "Web/Desktop", "free_tier": False},
        {"name": "Bandcamp", "category": "Independent", "price": "Per track", "platform": "All", "free_tier": True},
        {"name": "Deezer", "category": "Music", "price": "Free / Premium", "platform": "All", "free_tier": True},
        {"name": "Amazon Music", "category": "Music", "price": "Free / Unlimited", "platform": "All", "free_tier": True},
        {"name": "YouTube Music", "category": "Music/Video", "price": "Free / Premium", "platform": "All", "free_tier": True},
        {"name": "Audiomack", "category": "Hip-Hop/Afrobeats", "price": "Free / Premium", "platform": "All", "free_tier": True},
    ],
    "dj_software": [
        {"name": "Serato DJ Pro", "category": "Professional", "platform": "Mac/Win", "price": "$149"},
        {"name": "Rekordbox", "category": "Pioneer DJ", "platform": "Mac/Win", "price": "Free / $120"},
        {"name": "Traktor Pro 3", "category": "Professional", "platform": "Mac/Win", "price": "$99"},
        {"name": "VirtualDJ", "category": "Beginner-Pro", "platform": "All", "price": "Free / $299"},
        {"name": "DJay Pro AI", "category": "AI-Powered", "platform": "Mac/iOS", "price": "$49.99"},
        {"name": "Ableton Live 12", "category": "Production", "platform": "Mac/Win", "price": "$99-$749"},
        {"name": "FL Studio 21", "category": "Production", "platform": "Win/Mac", "price": "$99-$499"},
        {"name": "Logic Pro", "category": "Production", "platform": "Mac", "price": "$199.99"},
        {"name": "Mixxx", "category": "Open Source", "platform": "All", "price": "Free"},
        {"name": "Engine DJ", "category": "Denon DJ", "platform": "Hardware", "price": "Hardware"},
    ],
    "festivals": [
        {"name": "Tomorrowland 2026", "location": "Boom, Belgium", "dates": "July 17-19 & 24-26", "genre": "EDM"},
        {"name": "Ultra Music Festival", "location": "Miami, USA", "dates": "March 27-29", "genre": "EDM"},
        {"name": "Coachella 2026", "location": "California, USA", "dates": "April 10-12 & 17-19", "genre": "Multi-genre"},
        {"name": "Afro Nation", "location": "Portimao, Portugal", "dates": "July 2026", "genre": "Afrobeats"},
        {"name": "Amapiano Festival", "location": "Johannesburg, SA", "dates": "December 2026", "genre": "Amapiano"},
        {"name": "Glastonbury", "location": "UK", "dates": "June 24-28", "genre": "Multi-genre"},
        {"name": "EDC Las Vegas", "location": "Las Vegas, USA", "dates": "May 16-18", "genre": "EDM"},
        {"name": "Creamfields", "location": "UK", "dates": "August 2026", "genre": "EDM"},
        {"name": "Notting Hill Carnival", "location": "London, UK", "dates": "August 2026", "genre": "Caribbean"},
        {"name": "Sónar", "location": "Barcelona, Spain", "dates": "June 2026", "genre": "Electronic"},
    ],
    "theater_streaming": [
        {"name": "NT Live", "content_type": "Theater / Drama", "region": "UK / Global"},
        {"name": "BroadwayHD", "content_type": "Musicals / Theater", "region": "USA / Global"},
        {"name": "Marquee TV", "content_type": "Arts / Dance", "region": "Global"},
        {"name": "Digital Theatre", "content_type": "Plays / Musicals", "region": "UK"},
        {"name": "On The Boards", "content_type": "Experimental", "region": "USA"},
        {"name": "Berliner Philharmoniker", "content_type": "Classical Music", "region": "Germany / Global"},
        {"name": "Met Opera on Demand", "content_type": "Opera", "region": "USA / Global"},
        {"name": "Royal Opera House Stream", "content_type": "Ballet / Opera", "region": "UK / Global"},
    ],
    "music_networks": [
        {"name": "Mixcloud", "focus": "DJ sets and radio shows", "region": "Global", "type": "Streaming"},
        {"name": "Boomplay", "focus": "Afrobeats and African music", "region": "Africa", "type": "Streaming"},
        {"name": "Audiomack", "focus": "Independent releases and discovery", "region": "Global", "type": "Music"},
        {"name": "Beatport", "focus": "Club-ready tracks and charts", "region": "Global", "type": "DJ Music"},
        {"name": "Resident Advisor", "focus": "Club events and scene discovery", "region": "Global", "type": "Community"},
        {"name": "Traxsource", "focus": "House, techno, and underground music", "region": "Global", "type": "DJ Music"},
    ],
}

def search_discover(query):
    """Search across all discover categories"""
    query = (query or "").strip().lower()
    results = {}

    if not query:
        return DISCOVER_DATA

    for category, items in DISCOVER_DATA.items():
        category_label = category.replace("_", " ").lower()
        if query in category_label:
            results[category] = items
            continue

        matches = []
        for item in items:
            item_text = " ".join(str(v) for v in item.values()).lower()
            if query in item_text:
                matches.append(item)
        if matches:
            results[category] = matches

    return results
