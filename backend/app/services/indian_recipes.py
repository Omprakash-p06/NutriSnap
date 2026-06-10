"""Curated Indian recipe helper used by chat for deterministic recipe responses."""

from __future__ import annotations

import re

RECIPE_INTENT_KEYWORDS = (
    "recipe",
    "how to make",
    "ingredients",
    "cook",
    "preparation",
    "steps",
)

INDIAN_RECIPE_BOOK = {
    "butter chicken": {
        "aliases": ["murgh makhani"],
        "ingredients": "chicken, yogurt, ginger-garlic paste, tomato puree, butter, cream, garam masala, chili powder",
        "steps": [
            "Marinate chicken with yogurt, ginger-garlic, salt, chili powder for 30 minutes.",
            "Cook chicken until lightly charred.",
            "Simmer tomato puree with butter, spices, and a little water for 10-12 minutes.",
            "Add chicken, finish with cream and kasuri methi, then serve hot.",
        ],
    },
    "chole bhature": {
        "aliases": ["chana bhatura", "chole"],
        "ingredients": "chickpeas, onion, tomato, ginger-garlic, chole masala, flour, yogurt, oil",
        "steps": [
            "Pressure-cook soaked chickpeas until soft.",
            "Make masala with onion, tomato, ginger-garlic, and chole spices.",
            "Simmer chickpeas in masala for 15 minutes.",
            "Knead bhature dough with flour, yogurt, and salt; rest, roll, and deep-fry.",
        ],
    },
    "masala dosa": {
        "aliases": ["dosa"],
        "ingredients": "dosa batter, potatoes, onions, mustard seeds, curry leaves, turmeric, oil",
        "steps": [
            "Prepare potato masala with onions, mustard, curry leaves, turmeric, and boiled potatoes.",
            "Spread dosa batter thinly on a hot griddle.",
            "Drizzle oil, cook until crisp.",
            "Place masala in center, fold, and serve with chutney and sambar.",
        ],
    },
    "idli sambar": {
        "aliases": ["idli", "sambar"],
        "ingredients": "idli batter, toor dal, mixed vegetables, tamarind, sambar powder",
        "steps": [
            "Steam idlis in molds for 10-12 minutes.",
            "Cook dal and vegetables separately.",
            "Combine with tamarind water, sambar powder, and tempering.",
            "Simmer until flavors combine and serve warm.",
        ],
    },
    "rajma chawal": {
        "aliases": ["rajma"],
        "ingredients": "kidney beans, onion, tomato, ginger-garlic, cumin, garam masala, rice",
        "steps": [
            "Pressure-cook soaked rajma until soft.",
            "Prepare onion-tomato masala with spices.",
            "Add rajma and simmer for 20 minutes.",
            "Serve with steamed rice and garnish with coriander.",
        ],
    },
    "palak paneer": {
        "aliases": [],
        "ingredients": "spinach, paneer, onion, tomato, garlic, ginger, cream, spices",
        "steps": [
            "Blanch spinach and blend into a smooth puree.",
            "Cook onion-tomato masala with ginger-garlic and spices.",
            "Add spinach puree and simmer 8-10 minutes.",
            "Add paneer cubes and finish with cream.",
        ],
    },
    "paneer tikka": {
        "aliases": [],
        "ingredients": "paneer, yogurt, ginger-garlic, chili powder, garam masala, capsicum, onion",
        "steps": [
            "Mix yogurt with spices to make marinade.",
            "Coat paneer and vegetables, marinate 30 minutes.",
            "Skewer and grill/air-fry until edges char.",
            "Serve with mint chutney and lemon.",
        ],
    },
    "biryani": {
        "aliases": ["chicken biryani", "veg biryani", "hyderabadi biryani"],
        "ingredients": "basmati rice, meat/vegetables, yogurt, fried onion, biryani masala, saffron",
        "steps": [
            "Parboil basmati rice with whole spices.",
            "Cook marinated meat or vegetables with masala.",
            "Layer rice and masala with fried onions and saffron milk.",
            "Dum cook on low heat for 20-25 minutes.",
        ],
    },
    "poha": {
        "aliases": [],
        "ingredients": "flattened rice, onion, mustard seeds, peanuts, turmeric, curry leaves",
        "steps": [
            "Rinse poha briefly and set aside.",
            "Temper mustard seeds, curry leaves, onion, chilies, and peanuts.",
            "Add turmeric and poha, toss gently.",
            "Finish with lemon juice and coriander.",
        ],
    },
    "upma": {
        "aliases": [],
        "ingredients": "semolina, onion, green chili, mustard, urad dal, curry leaves, water",
        "steps": [
            "Dry roast semolina and keep aside.",
            "Temper mustard, urad dal, curry leaves, onion, and chilies.",
            "Add hot water and salt, then slowly stir in semolina.",
            "Cook until fluffy and serve hot.",
        ],
    },
    "dal tadka": {
        "aliases": ["yellow dal"],
        "ingredients": "toor/moong dal, onion, tomato, garlic, cumin, ghee, chili",
        "steps": [
            "Pressure-cook dal until soft.",
            "Cook onion-tomato masala with spices.",
            "Mix in dal and simmer.",
            "Top with ghee tadka of garlic, cumin, and chili.",
        ],
    },
    "aloo paratha": {
        "aliases": [],
        "ingredients": "wheat flour, boiled potatoes, green chili, coriander, spices, ghee",
        "steps": [
            "Knead a soft wheat dough.",
            "Mix boiled potatoes with spices for stuffing.",
            "Stuff, roll gently, and cook on tawa with ghee.",
            "Serve with curd and pickle.",
        ],
    },
    "pav bhaji": {
        "aliases": [],
        "ingredients": "mixed vegetables, onion, tomato, capsicum, pav bhaji masala, butter, pav",
        "steps": [
            "Boil and mash vegetables.",
            "Cook onion, tomato, capsicum with pav bhaji masala.",
            "Add vegetables and mash while simmering with butter.",
            "Toast pav in butter and serve with bhaji.",
        ],
    },
    "samosa": {
        "aliases": [],
        "ingredients": "flour, potatoes, peas, cumin, garam masala, oil",
        "steps": [
            "Prepare stiff dough with flour, oil, and salt.",
            "Make spiced potato-peas filling.",
            "Shape cones, fill, seal, and deep-fry on medium heat.",
            "Serve with tamarind and mint chutney.",
        ],
    },
    "kadhai paneer": {
        "aliases": [],
        "ingredients": "paneer, capsicum, onion, tomato, kadhai masala, ginger, garlic",
        "steps": [
            "Saute onion and capsicum on high heat.",
            "Cook tomato gravy with kadhai masala.",
            "Add paneer and vegetables, toss for 3-4 minutes.",
            "Garnish with ginger juliennes.",
        ],
    },
    "bhindi masala": {
        "aliases": ["okra fry"],
        "ingredients": "bhindi (okra), onion, tomato, turmeric, coriander powder, amchur",
        "steps": [
            "Saute chopped bhindi until non-sticky and set aside.",
            "Cook onion-tomato masala with spices.",
            "Add bhindi and toss gently until coated.",
            "Finish with amchur and coriander.",
        ],
    },
    "fish curry": {
        "aliases": ["goan fish curry", "meen curry"],
        "ingredients": "fish, coconut milk, onion, tomato, turmeric, chili, tamarind",
        "steps": [
            "Make curry base with onion, tomato, spices, and coconut milk.",
            "Bring to a gentle simmer.",
            "Add fish pieces and cook 6-8 minutes.",
            "Finish with tamarind or kokum for tang.",
        ],
    },
    "chicken curry": {
        "aliases": ["indian chicken curry"],
        "ingredients": "chicken, onion, tomato, ginger-garlic, turmeric, chili, coriander powder",
        "steps": [
            "Brown onions and cook with ginger-garlic.",
            "Add tomatoes and spices; cook to a thick masala.",
            "Add chicken, sear, then add water and simmer until tender.",
            "Adjust salt and garnish with coriander.",
        ],
    },
    "khichdi": {
        "aliases": ["khichri"],
        "ingredients": "rice, moong dal, turmeric, cumin, ghee, vegetables (optional)",
        "steps": [
            "Wash rice and dal together.",
            "Temper cumin in ghee, add rice-dal and turmeric.",
            "Pressure-cook with water until soft.",
            "Serve with ghee and yogurt.",
        ],
    },
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _has_recipe_intent(query: str) -> bool:
    q = _normalize(query)
    return any(key in q for key in RECIPE_INTENT_KEYWORDS)


def _format_recipe(dish: str, details: dict) -> str:
    steps = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(details["steps"])])
    return (
        f"Recipe: {dish.title()}\n"
        f"Ingredients: {details['ingredients']}\n"
        f"Steps:\n{steps}\n"
        "Tip: Pair this with salad or curd for a more balanced meal."
    )


def find_indian_recipe_reply(query: str) -> str | None:
    """Return a deterministic recipe response when a matching Indian dish is requested."""
    if not query:
        return None

    q = _normalize(query)
    wants_recipe = _has_recipe_intent(q)
    asks_indian_list = "indian" in q and (
        "dish" in q or "dishes" in q or "recipes" in q
    )

    for dish, details in INDIAN_RECIPE_BOOK.items():
        aliases = details.get("aliases", [])
        dish_tokens = [dish, *aliases]
        if any(token in q for token in dish_tokens) and (wants_recipe or "recipe" in q):
            return _format_recipe(dish, details)

    if asks_indian_list or (wants_recipe and "indian" in q):
        sample = ", ".join(
            sorted([name.title() for name in INDIAN_RECIPE_BOOK.keys()])[:14]
        )
        return (
            "I can help with Indian recipes. Try asking like: "
            "'recipe for palak paneer' or 'how to make biryani'.\n"
            f"Available examples: {sample}."
        )

    return None
