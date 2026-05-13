"""
Phasmophobia map data.
Each entry: (display_name, size)
Size must match a key in the TIMERS map_sizes dict: "Small", "Medium", "Large"
Add or rename maps here without touching the main timer code.
"""

MAPS = [
    # Small maps
    ("42 Edgefield Road", "Small"),
    ("Grafton Farmhouse", "Small"),
    ("Nell's Diner", "Small"),
    ("10 Ridgeview Court", "Small"),
    ("6 Tanglewood Drive", "Small"),
    ("13 Willow Street", "Small"),
    ("Camp Woodwind", "Small"),

    # Medium maps
    ("Bleasdale Farmhouse", "Medium"),
    ("Maple Lodge Campsite", "Medium"),
    ("Point Hope", "Medium"),
    ("Prison", "Medium"),
    ("SM Restricted - Courtyard", "Medium"),
    ("SM Restricted - Female Wing", "Medium"),
    ("SM Restricted - Hospital", "Medium"),
    ("SM Restricted - Male Wing", "Medium"),
    ("SM Restricted - Restricted", "Medium"),

    # Large maps
    ("Brownstone High School", "Large"),
    ("Sunny Meadows", "Large"),
]

# Group maps by size for easy lookup
MAPS_BY_SIZE = {}
for name, size in MAPS:
    MAPS_BY_SIZE.setdefault(size, []).append(name)
