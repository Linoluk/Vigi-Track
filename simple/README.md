# Vigi-Track Simple

A lighter version of Vigi-Track, made to practise a real app structure: a page, a database, and hosting.

One idea only: **search a drug, then read the symptoms people report, or report your own.**

## Files

| File | What it does |
|---|---|
| `index.html` | The whole page: layout, styles and code. Start reading here. |
| `config.js` | Your Supabase address and public key. Empty = demo mode. |
| `vocab.js` | The 37 symptoms the app knows, and the keyword rules to find them in a text. Taken from the full app. |
| `seed.js` | Symptoms found in the 5,550 Drugs.com reviews, per drug, with two quotes each. Generated, do not edit. |
| `build_seed.js` | Rebuilds `seed.js` from `../app/real_data.js`. Run `node simple/build_seed.js` from the repo root. |
| `../supabase/setup.sql` | Creates the `reports` table and its security rules in Supabase. |

## Run it

**On your computer.** From the repo root, run `python3 -m http.server`, then open http://localhost:8000/simple/.
Without Supabase, it runs in demo mode: your reports stay in your browser.

**Online, with GitHub Pages.** In the repo on GitHub: Settings > Pages > Source: *Deploy from a branch*,
pick this branch and `/ (root)`, Save. After a minute the app is at `https://<user>.github.io/<repo>/simple/`.

## Connect the database (Supabase, free plan)

1. Create a free account on supabase.com, then a new project. Pick a region in Europe.
2. Open **SQL Editor**, paste all of `supabase/setup.sql`, click **Run**. You now have a `reports` table.
3. Open **Project Settings > API Keys**. Copy the **Project URL** and the **publishable** key.
4. Paste them in `config.js`, commit, push. The badge at the top of the page now says *Shared database*.
5. Send a report from the app, then look at it in Supabase: **Table Editor > reports**.

Good to know: a free project goes to sleep after a week without visits. Wake it up from the dashboard before a demo.

## How it works

- **Read.** For the chosen drug, the page loads its reports from Supabase and adds them to the Drugs.com mentions from `seed.js`. Symptoms are sorted by frequency. A red *Not in leaflet* tag marks the ones the FDA label does not list: that is the core idea of Vigi-Track.
- **Report.** The user ticks symptoms (or types another one, which is matched to the vocabulary when possible: "throwing up" becomes "nausea") and can add a note. One report = one row in the `reports` table.
- **Security.** The public key in `config.js` is visible to everyone, and that is normal. What it allows is set by the row level security rules in `setup.sql`: read and add reports, never change or delete them.
- **Limits.** Drugs.com mentions come from keyword search, so some are false matches ("my acne is gone"). The full app (`app/index.html`) uses Claude to read reviews properly. Plugging that AI into this version is a good next step.

## Ideas to go further

- Ask how strong the effect was (mild, moderate, severe) and show it in Read.
- Use Claude to turn the free note into standard symptoms.
- A small chart: reports per month for a drug.
