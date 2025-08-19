"""
Deterministic seeder that creates 240 books total:
 - First 70 keep the original distribution:
   * 15 Manga, 20 Science (course books), 25 Literature, 10 Fiction
 - Plus 170 additional books spread across the same categories

All books are created with at least 10 copies available.

Usage (from project root):
  cd librarymanagementsystem/lims_portal
  python manage.py shell -c "from lims_app.populate_books import run; run()"
"""

from django.db import transaction
from lims_app.models import Book


# Base distribution (first 70)
NUM_MANGA = 15
NUM_SCIENCE = 20      # "course books" mapped to the 'Science' category
NUM_LITERATURE = 25
NUM_FICTION = 10      # Fills the remaining 10 to reach 70 total
EXTRA_COUNT = 170     # Additional books to add (beyond the base 70)

# Titles and authors per category (curated)
MANGA_TITLES = [
    ("Crimson Blade", "Haruto Sato"),
    ("Shadow Ninja", "Aiko Tanaka"),
    ("Dragon's Path", "Ren Ito"),
    ("Tokyo Echo", "Naomi Fujii"),
    ("Moonlit Shrine", "Kaito Miyazaki"),
    ("Neon Alley", "Yui Nakamura"),
    ("Storm Samurai", "Kenji Kobayashi"),
    ("Frost Guardian", "Mika Arai"),
    ("Steel Ronin", "Takumi Watanabe"),
    ("Paper Lanterns", "Sora Hoshino"),
    ("Kitsune's Oath", "Emi Suzuki"),
    ("Last Shogun", "Riku Takahashi"),
    ("Shattered Katana", "Yoko Matsuda"),
    ("Echoes of Kyoto", "Daichi Morita"),
    ("Azure Petals", "Hana Kimura"),
]

SCIENCE_TITLES = [
    ("Quantum Foundations", "Dr. Leah Morgan"),
    ("Calculus Essentials", "Prof. Daniel Kim"),
    ("Data Structures", "Prof. Sara Ahmed"),
    ("Operating Systems", "Dr. Victor Chen"),
    ("Linear Algebra", "Dr. Priya Ramesh"),
    ("Organic Chemistry", "Dr. Emily Carter"),
    ("Physics for Engineers", "Prof. Brian Hughes"),
    ("Circuit Analysis", "Dr. Alicia Gomez"),
    ("Thermodynamics", "Prof. Marcus Reid"),
    ("Machine Learning 101", "Dr. Nina Patel"),
    ("Statistics with Python", "Dr. Oliver Grant"),
    ("Microbiology Basics", "Dr. Hannah Lee"),
    ("Biochemistry Primer", "Prof. Carla Mendes"),
    ("Discrete Mathematics", "Prof. Ethan Wright"),
    ("Computer Networks", "Dr. Ingrid Novak"),
    ("Database Systems", "Prof. Aaron Clarke"),
    ("Numerical Methods", "Dr. Sofia Marino"),
    ("Software Engineering", "Prof. Jason Park"),
    ("Probability Theory", "Dr. Monica Silva"),
    ("Modern Algebra", "Prof. Lucas Bernard"),
]

LITERATURE_TITLES = [
    ("Winds of Autumn", "Clara Whitfield"),
    ("Echoes in the Valley", "Isaac Monroe"),
    ("Midnight Letters", "Evelyn Brooks"),
    ("The Last Orchard", "Graham West"),
    ("Songs of the Sea", "Amelia Rhodes"),
    ("Dust and Dreams", "Noah Sinclair"),
    ("The Silent House", "Iris Bloom"),
    ("Winter's Promise", "Julian Hart"),
    ("Gilded Streets", "Maya Green"),
    ("Paper Moons", "Rowan Pierce"),
    ("Ashes and Embers", "Lena Hale"),
    ("The Painted Garden", "Felix Carter"),
    ("Lanterns at Dusk", "Nora Collins"),
    ("Tales of a City", "Adrian Cole"),
    ("Beneath the Cypress", "Olivia Grant"),
    ("Bright Water", "Theo Sanders"),
    ("Harvest of Stars", "Violet Shaw"),
    ("Silver Thread", "Miles Turner"),
    ("Broken Harp", "Isla Bennett"),
    ("Riverward", "Caleb Yates"),
    ("A Violet Sky", "Elise Warren"),
    ("Borrowed Time", "Owen Palmer"),
    ("The Far Country", "Greta Dawson"),
    ("Glass Wings", "Leo Whitman"),
    ("Stone of Morning", "Eva Delaney"),
]

FICTION_TITLES = [
    ("Nebula Road", "Arthur Quinn"),
    ("Crimson Harbor", "Sophie Lane"),
    ("Shadow Market", "Declan Frost"),
    ("The Clockmaker", "Ivy March"),
    ("City of Lenses", "Gideon Black"),
    ("Iron Sparrow", "Freya Dune"),
    ("The Sapphire Key", "Hugo Mercer"),
    ("Echo Harbor", "June Calloway"),
    ("Night Bazaar", "Ronan Vale"),
    ("The Fifth Door", "Tessa Rowan"),
]


def _with_count(lst, needed):
    out = []
    i = 0
    while len(out) < needed:
        out.append(lst[i % len(lst)])
        i += 1
    return out[:needed]


def _iter_all_books():
    # Base 70
    for title, author in _with_count(MANGA_TITLES, NUM_MANGA):
        yield {"title": title, "author": author, "category": "Manga"}
    for title, author in _with_count(SCIENCE_TITLES, NUM_SCIENCE):
        yield {"title": title, "author": author, "category": "Science"}
    for title, author in _with_count(LITERATURE_TITLES, NUM_LITERATURE):
        yield {"title": title, "author": author, "category": "Literature"}
    for title, author in _with_count(FICTION_TITLES, NUM_FICTION):
        yield {"title": title, "author": author, "category": "Fiction"}

    # Extra 170 (cycle categories and titles deterministically)
    CATS = [
        ("Manga", MANGA_TITLES),
        ("Science", SCIENCE_TITLES),
        ("Literature", LITERATURE_TITLES),
        ("Fiction", FICTION_TITLES),
    ]
    for i in range(EXTRA_COUNT):
        cat_name, titles = CATS[i % len(CATS)]
        title, author = titles[i % len(titles)]
        yield {"title": title, "author": author, "category": cat_name}


def _isbn_for(index):
    # Deterministic unique 13-digit numeric string
    return f"978000001{index:03d}"


def _copies_for(index):
    # Ensure at least 10 copies for every book
    return 10


@transaction.atomic
def run():
    created = 0
    counts = {"Manga": 0, "Science": 0, "Literature": 0, "Fiction": 0}
    for idx, payload in enumerate(_iter_all_books(), start=1):
        isbn = _isbn_for(idx)
        copies = _copies_for(idx)
        obj, was_created = Book.objects.get_or_create(
            isbn=isbn,
            defaults=dict(
                title=payload["title"],
                author=payload["author"],
                category=payload["category"],  # Choices: Fiction, Manga, Literature, Science, Others
                copies_available=copies,
            ),
        )
        if was_created:
            created += 1
            counts[payload["category"]] += 1
    print(f"Created {created} books total.")
    print("By category ->", counts)



