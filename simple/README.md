# Vigi-Track Simple

A lighter version of Vigi-Track, made to practise a real app structure: a page, a database, hosting, and an AI that runs only when a key is there.

**Live:** https://linoluk.github.io/Vigi-Track/simple/

The idea in one line: **search a drug, then read the side effects people report, or report your own.**
It keeps the look of the full app (`app/index.html`): same logo, colours, fonts, tiles and quotes.

## What is on the page

| Part | What it does |
|---|---|
| **Hero and search** | What Vigi-Track is, and a search box that filters the drug tiles. |
| **Choose a drug** | The 37 drugs as coloured tiles. A badge shows how many reports a drug has. Typing an unknown drug offers to report for it. |
| **Read symptoms** | For one drug: side effects found in the Drugs.com reviews plus the reports made here, most frequent first. A red *Not in the leaflet* tag marks the ones the FDA label does not list. Open one to read the quotes. |
| **Report a symptom** | Tick what you felt, add a note, send. Saved without a name in Supabase, visible to everyone at once. |
| **Describe it in your own words (AI)** | At the top of Report. The AI reads a free sentence and ticks the matching symptoms. The user checks, then sends. |
| **How it works** | The app in 4 steps, and its limits. |
| **Why AI** | The full app's demo: keyword search vs AI on the same sentence. |

## Where the AI runs

The AI uses the same extraction prompt as the full app (see `PROMPTS.md`, 1.1).

- **Inside claude.ai**, it uses the viewer's Claude. Nothing to set up.
- **Anywhere else** (GitHub Pages, your computer), it needs an Anthropic API key, pasted in the page. The key stays in the browser tab and is only sent to `api.anthropic.com`. One field fills the other: a key typed under *Why AI* also works in *Report*.
- **Without a key**, both AI features stay visible. Their examples show an answer computed in advance, and a grey *AI needs a key* badge says why your own sentence is not read.

A real product would not ask visitors for a key: a small server function (for example a Supabase Edge Function) would hold it and call Claude for them.

## Files

| File | What it does |
|---|---|
| `index.html` | The whole page: layout, styles and code. Start reading here. |
| `config.js` | Your Supabase address and public key. Empty = demo mode (reports stay in your browser). |
| `vocab.js` | The 37 symptoms the app knows, and the keyword rules to find them in a text. Taken from the full app. |
| `seed.js` | Symptoms found in the 5,550 Drugs.com reviews, per drug, with two quotes each. Generated, do not edit. |
| `build_seed.js` | Rebuilds `seed.js` from `../app/real_data.js`. Run `node simple/build_seed.js` from the repo root. |
| `../supabase/setup.sql` | Creates the `reports` table and its security rules in Supabase. |

## Run it

**On your computer.** From the repo root, run `python3 -m http.server`, then open http://localhost:8000/simple/.

**Online, with GitHub Pages.** In the repo on GitHub: Settings > Pages > Source: *Deploy from a branch*,
pick the branch and `/ (root)`, Save. After a minute the app is at `https://<user>.github.io/<repo>/simple/`.

## Connect the database (Supabase, free plan)

1. Create a free account on supabase.com, then a new project. Pick a region in Europe.
2. Open **SQL Editor**, paste all of `supabase/setup.sql`, click **Run**. You now have a `reports` table.
3. Open **Project Settings > API Keys**. Copy the **Project URL** and the **publishable** key.
4. Paste them in `config.js`, commit, push. The badge at the top of the page now says *Shared database*.
5. Send a report from the app, then look at it in Supabase: **Table Editor > reports**.

Good to know: a free project goes to sleep after a week without visits. Wake it up from the dashboard before a demo.

## How it works inside

- **Read.** For the chosen drug, the page loads its reports from Supabase and adds them to the Drugs.com mentions from `seed.js`.
- **Report.** One report = one row in the `reports` table: drug, symptoms, optional note. A typed symptom is matched to the vocabulary when possible ("throwing up" becomes "nausea").
- **Security.** The public key in `config.js` is visible to everyone, and that is normal. What it allows is set by the row level security rules in `setup.sql`: read and add reports, never change or delete them.
- **Limits.** Drugs.com mentions in this version come from keyword search, so some are false matches ("my acne is gone"). The full app reads every review with the AI.

## Ideas to go further

- Run `data/precompute_ai.py` once and build `seed.js` from the AI results instead of keywords.
- Move the API key to a Supabase Edge Function, so the AI works for every visitor.
- Ask how strong the effect was (mild, moderate, severe) and show it in Read.
- A small chart: reports per month for a drug.
