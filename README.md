# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tool Inventory

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool searches the mock listings dataset for items matching the description, optional size, and optional price ceiling.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for
- `size` (str): Size string to filter by, or None to skip size filtering. Matching is case-insensitive
- `max_price` (float): Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
It returns a result contains a list of matching listing dicts, sorted by relevance (best match first).

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
It returns an empty list if nothing matches. It does not raise an exception.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool is to suggest 1-2 complete outfits with a given thrifted item and the user's wardrobe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict (the item the user is considering buying).
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts.

**What it returns:**
<!-- Describe the return value -->
It returns a non-empty string with outfit suggestions.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, it offers a general styling advice for the item rather than raising an exception or returning an empty string.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool generates a short, shareable outfit caption for the thrifted find.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string from suggest_outfit().
- `new_item` (dict): The listing dict for the thrifted item.

**What it returns:**
<!-- Describe the return value -->
It returns a 2–4 sentence string usable as an Instagram/TikTok caption.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or missing, it returns a descriptive error message string. It does not raise an exception.

---

## Planning Loop

My planning loop shows that the user query is extracted into a description, size, and max_price, and these three parameters are passed for the search_listings tool call. After running the search_listings tool, it checks whether the result is an empty list or not. If it is an empty list, then it returns just an error message. Otherwise, it selects the most relevant listing and checks if a user wardrobe context is available. Then, it runs the suggest_outfit tool, and returns a 1-2 outfit combinations as a string. If the wardrobe is empty, then it creates a general styling advice for the item. Then, it runs the create_fit_card tool, and builds a shareable outfit caption for social media. If the outfit is empty, then it returns a descriptive error message.

---

## State Management Approach



---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | It stops the progression to the styling phase, and prints a message stating no exact items matched the current combination of description, size, or price filters. Then, it attempts for the suggestion of loosening the parameters to the user. |
| suggest_outfit | Wardrobe is empty | It uses the personalized wardrobe matching loop and independent metadata of the thrifted item to generate the structural styling advice. |
| create_fit_card | Outfit input is missing or incomplete | It generates a caption that includes independent item metadata to ensure the user still walks away with a ready-to-post social media caption. |

---

## Spec Reflection

**One way the spec helped you during implementation:**


**One way your implementation diverged from the spec, and why:**


---

## AI Usage

**Instance 1**

- *What I gave the AI:* 
- *What it produced:* 
- *What I changed or overrode:* 

**Instance 2**

- *What I gave the AI:* 
- *What it produced:* 
- *What I changed or overrode:* 