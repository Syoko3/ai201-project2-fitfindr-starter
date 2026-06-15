# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

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
A result contains a list of matching listing dicts, sorted by relevance (best match first).

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

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
After running the search_listings tool, it checks whether the result is an empty list or not. If it is an empty list, then it returns just an error message. Otherwise, it selects the most relevant listing and checks if a user wardrobe context is available. Then, it runs the suggest_outfit tool, and returns a 1-2 outfit combinations as a string. If the wardrobe is empty, then it creates a general styling advice for the item. Then, it runs the create_fit_card tool, and builds a shareable outfit caption for social media. If the outfit is empty, then it returns a descriptive error message.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
My agent stores the user input, then extracts the filters and runs the search_listings tool, then accesses the listings.json to find the matches as the list. The extracted search parameters (description, size, max_price) are tracked in the search_listings tool. Then, the list is passed to the suggest_outfit tool call by selecting the best-matching item and fetching the wardrobe context. It ensures that the state of the wardrobe data is populated, and then it calls the suggest_outfit tool. The selected_item and the wardrobe_data are tracked in the suggest_outfit tool. After that, the agent calls the create_fit_card tool with generated outfit from the result of the suggest_outfit tool call and selected item. The selected_item and the generated_outfit are tracked in the create_fit_card tool. Then, the final caption is presented to the user. 

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | It stops the progression to the styling phase, and prints a message stating no exact items matched the current combination of description, size, or price filters. Then, it attempts for the suggestion of loosening the parameters to the user. |
| suggest_outfit | Wardrobe is empty | It uses the personalized wardrobe matching loop and independent metadata of the thrifted item to generate the structural styling advice. |
| create_fit_card | Outfit input is missing or incomplete | It generates a caption that includes independent item metadata to ensure the user still walks away with a ready-to-post social media caption. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User Input
    │
    v
Planning Loop ─────────────────────────────────────────────────────────────────┐
    │                                                                          │
    ├──> Initialize Session State (Load `wardrobe`)                            │
    │                                                                          │
    ├──> search_listings(description, size, max_price)                         │
    │        │                                                                 │
    │        ├──> [results == []] ──> [ERROR] "No listings found" ──> return ──┤
    │        │                                                                 │
    │        └──> [results != []] ──> State: selected_item = results[0]        |
    │                                        |                                 │
    |                                        v                                 |
    ├──> suggest_outfit(selected_item, wardrobe_data)                          │
    │        │                                                                 │
    │        ├──> [wardrobe['items'] == []] ──> Standalone Styling             |
    │        │                                  (Metadata Mode)                │
    │        │                                                                 │
    │        ├──> [wardrobe['items'] != []] ──> Personalized Closet            │
    │        |                                  Cross-Reference                │
    │        |                                                                 |
    │        v                                                                 │
    │    State: outfit_suggestion = "..."                                      │
    │        |                                                                 |
    |        v                                                                 │
    └──> create_fit_card(outfit_suggestion, selected_item)                     │
             │                                                                 │
             ├──> [outfit_suggestion == ""] ──> Baseline Fallback              |
             │                                  Caption Code                   │
             │                                                                 │
             ├──> [outfit_suggestion != ""] ──> Fully Customized               │
             |                                  Platform Caption               │
             |                                                                 |
             v                                                                 │
         State: fit_card = "..."                                               │
             │                                                                 │
             v                                                                 └─ error path returns here
         Return Session 

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will give Claude my Tool 1 spec and ask it to implement search_listings() using load_listings() from the data loader. Then, I will test it against 3 queries before trusting it. After that, I will give Claude my Tool 2 spec and ask it to implement suggest_outfit() using load_wardrobe_schema() from the data loader. After that, I will give Claude my Tool 3 spec and ask it to implement create_fit_card().

**Milestone 4 — Planning loop and state management:**
I will give ChatGPT my planning loop and state management spec and ask it to implement run_agent() in agent.py and handle_query() in app.py using the numbered steps in the respective files.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

FitFindr needs to filter and search through available vintage listings across popular platforms. It also needs to traverse the user's current closet with newly found pieces to eliminate purchase friction.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent uses the search_listings tool first to find the relevant pieces. The description is "vintage graphic tee", size is "None", and the max_price is "30.00".

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The tool returns the list of matching items under $30, and the planning loop isolates the top match, which has the id "lst_002" in the listings.json. This item is stored in the selected_item. The agent then calls the get_example_wardrobe() from the data loader and updates the wardrobe_data. After that, it calls the suggest_outfit tool to find the best outfit.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The tool looks the metadata against the user's closet tags, and it generates the detailed string and saves it to the generated_outfit. After that, the agent calls the create_fit_card tool with the generated_outfit and selected_item as the new_item.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user actually sees a 2-4 sentence string containing the item match, the styling, and the ready-to-post social media caption.