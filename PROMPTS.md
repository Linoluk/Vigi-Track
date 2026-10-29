# Use of AI tools and prompts

This file lists where and how we used AI tools, and the exact prompts.

| Tool | Where | What for |
|---|---|---|
| **Claude** (Anthropic) | Building the project | Wrote and tested the app code, wrote the 66 demo reviews, designed the app and the animated video scenes, wrote the video and music scripts, drafted this documentation. |
| **Claude**, inside the app | Running the app | Reads the reviews and extracts side effects (zero-shot, JSON output). Powers the agent, which calls the app's tools and writes reports. |
| **Playwright** and **ffmpeg** | Video | Filmed the app automatically and encoded the video. |
| **Python (numpy)** | Video | Generated the background music from code. |

## Part 1. Prompts used inside the app

### 1.1 Side effect extraction (one call per batch of 20 reviews, fast model)

```text
You are a pharmacovigilance assistant reading patient reviews of the drug "{drug}".
For each review, list the side effects the patient says they actually experienced while taking this drug.
Rules:
- Ignore effects the patient denies ("no nausea"), only fears, or did not have.
- Ignore symptoms of the illness being treated, and the effect the drug is taken for (for example weight loss with a weight loss pill), unless the patient blames the drug.
- Use short lowercase medical terms. Use one of these terms when it fits: {37 vocabulary terms}. Otherwise write a short standard term (for example "chest pain").
- An empty list is fine.
Reply with only a JSON array, one object per review, like [{"id":"r1","effects":["nausea"]}].

Reviews:
[{id}] {review text}
...
```

Why it is written this way. The rules about denied and feared effects fix the main weakness of keyword search. The fixed vocabulary keeps the dashboard clean. The JSON format lets the app read the answer without errors.

### 1.2 Agent instructions (sent with every question)

```text
You are the Vigi-Track pharmacovigilance agent. You help a drug safety team read weak signals found in patient reviews.
Use your tools to read the analysis results and the reviews behind a signal before you answer. Only use this data.
Be factual and short (under 220 words). Patient reviews are unverified and cannot prove the drug caused an effect: say so when you recommend action, and recommend checking official sources (EudraVigilance, ANSM, FDA FAERS). Never give medical advice to patients.
The data is a demo sample with fictional drug names. Mention it once.   (only with demo data)
The reviews are real, from the public Drugs.com dataset. The leaflet is the drug's FDA label.   (only with the built-in real data)
Write plain text in short paragraphs. You may use **bold** and numbered lines. No headings with #.

Drug: {drug}. Question: {question}
```

### 1.3 Tools the agent can call

| Tool | Description given to the model |
|---|---|
| `get_signal_summary` | Returns the current analysis: drug, number of reviews analysed, the leaflet's known effects, and every detected effect with its number of reviews, share and whether it is in the leaflet. |
| `get_reviews_for_effect` | Returns up to 8 patient reviews (id, rating, text) in which the given side effect was detected. Use it to quote or describe what patients say. Input: `effect`, `limit`. |

### 1.4 Suggested questions in the app

- Write a short safety signal report for the safety team.
- Which alert should we investigate first, and why?
- Summarise what patients say about the effects that are not in the leaflet.

## Part 2. Build prompt given to Claude

We used Claude to write the code, the demo data and the video. Below is the request we gave it, written as one prompt.

```text
Build "Vigi-Track", a web app with an AI agent for pharmacovigilance, from our project concept.

Concept. Drugs are tested on a few thousand patients before launch. Rare side effects
appear later, and most are never reported. Patients describe them online. The app reads
patient reviews of a drug and flags the side effects that are missing from the official leaflet.

User steps.
1. Load patient reviews (a demo sample, or the public Drugs.com dataset from Kaggle).
2. Choose a drug.
3. Tick the side effects already listed in the leaflet.
4. Run the analysis. A zero-shot language model reads each review and lists the side effects
   the patient really had. It must understand negation ("no nausea at all").
5. See the results, with the effects that are not in the leaflet highlighted as alerts.
Also include a keyword search mode to show why the AI is better, and an agent that can
read the results and write a short signal report for a drug safety team.

Requirements.
- Go beyond the course content (the course covered bag of words and supervised learning).
- Reproducible from the code. One self-contained file, with a way to run the AI outside Claude.
- Visual and attractive, like a real consumer app, easy for anyone to use.
- Deliver: the code, the data, a user guide, and this prompt report.
- A demo video under 5 minutes, professional and dynamic, with strong wording and background
  music. It must explain the purpose of the app, its catchy name, and the value it would
  create if it were widely used. Everything in English.
```

We then reviewed each version and asked for changes, mainly a more dynamic video and a more visual app.

## What Claude decided, and what we checked

- The built-in real data (37 drugs, 150 most helpful reviews each) and the FDA label leaflets are produced by `data/build_real_data.py`, from the Drugs.com dataset and the openFDA label API. No prompt is involved: the label effects are found with fixed patterns, listed in the script.

- Claude chose the stack (one HTML file, no server), the fictional drug names for the demo data, the term vocabulary (37 terms today) and the two agent tools.
- The demo reviews are invented. They were written to include tricky cases on purpose: negations ("no nausea at all"), fears ("I was scared of weight gain"), and paraphrases ("my heart is doing flips").
- The dataset size in the video (215,063 reviews) is the size of the UCI Drugs.com dataset.
- The under-reporting figure in the video (94% median) comes from Hazell and Shakir, "Under-reporting of adverse drug reactions: a systematic review", Drug Safety, 2006.
- In the video, the AI answers were produced by `video-tools/mock.js` so the demo could be filmed offline. They match what the app shows with the demo data. The live app calls the real Claude.

## Part 3. The lighter version (`simple/`)

Built after the main project with Claude, as an exercise in app structure: a page, a Supabase database and GitHub Pages hosting.

- Claude wrote `simple/index.html`, `vocab.js`, `build_seed.js` and `supabase/setup.sql`, reusing the full app's design, vocabulary and extraction prompt (1.1). We asked for a simpler page (search a drug, then read or report symptoms), the same look as the full app, the *Why AI* section, a *How it works* section, and one AI feature that is easy to understand.
- **Describe it in your own words** uses prompt 1.1 on one free sentence and ticks the symptoms it returns. The user checks them before sending.
- The answers shown for the built-in examples (3 in *Why AI*, 2 in *Report*) were written in advance, so the page works without a key. They are labelled as such on the page.
- Drugs.com counts in this version come from keyword search, not from the AI (see `simple/README.md`).
