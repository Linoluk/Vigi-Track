# Vigi-Track

**Patients say it before the leaflet does.**

An AI agent that reads patient reviews and flags the drug side effects missing from the official leaflet.

Final project, AI for Business, ESSEC.

> **New:** a lighter version, where people can read and report symptoms for a drug, with a Supabase database. See [`simple/`](simple/README.md).

Before launch, a drug is tested on a few thousand patients. After launch, millions of people take it for years, and rare side effects only show up then. Most of them are never reported to the authorities. Patients do talk about them online.

Vigi-Track reads patient reviews of a drug. An AI agent lists the side effects each patient really had. The app compares them with the official leaflet and turns every effect that is **not in the leaflet** into an alert for the safety team. The agent can then write a short signal report.

![Vigi-Track](docs/img/overview.png)

![An alert](docs/img/alert.png)

## What is in this folder

| Folder | Content |
|---|---|
| `app/index.html` | The whole app in one file (HTML, CSS, JavaScript). |
| `app/real_data.js` | The built-in real data: 5,550 Drugs.com reviews of 37 drugs and their FDA label side effects. Loaded by the app. |
| `app/real_ai.js` | AI results computed in advance on the real reviews. Empty until `data/precompute_ai.py` is run. |
| `data/demo_reviews.csv` | 66 demo reviews for 5 **fictional** drugs, in the same format as the Drugs.com dataset. |
| `data/leaflet_known_effects.csv` | The side effects listed in each demo leaflet. |
| `data/real_leaflets.csv` | The side effects named in the FDA label of each real drug. |
| `data/build_real_data.py` | Rebuilds `app/real_data.js` and `data/real_leaflets.csv` from the Drugs.com dataset and openFDA. |
| `data/precompute_ai.py` | Runs the AI extraction once on all real reviews and writes `app/real_ai.js`. Needs an Anthropic API key. |
| `tests/test_app.py` | End-to-end tests of the app in headless Chromium. Fakes the Claude API, so no key is needed. |
| `docs/USER_GUIDE.pdf` | Step by step user guide with screenshots. |
| `docs/guide/` | Source of the user guide (`USER_GUIDE.html`) and `build_guide.py`, which turns it into the PDF. |
| `PROMPTS.md` | Every prompt used, in the app and to build the project. |
| `video/Vigi-Track-demo.mp4` | The demo video (1080p, 2 min 37, with music). |
| `video-tools/` | Scripts that filmed the demo (`film.html` for the animated scenes, `record.py`) and generated the music (`music.py`). |

## Try it now

**[Open Vigi-Track in Claude](https://claude.ai/artifact/DgS7dT4zHKniHtZe1xF8pX)**. Nothing to install. The AI agent runs on your own Claude account.

## How to run it

**Option 1. In Claude (easiest).** Open the [published app](https://claude.ai/artifact/DgS7dT4zHKniHtZe1xF8pX) in claude.ai. The AI agent runs on your Claude account. Nothing to install.

**Option 2. On your computer.**
1. Download this folder.
2. Open `app/index.html` in Chrome, Edge or Firefox. Keep `real_data.js` next to it: it holds the real reviews.
3. Keyword mode works straight away.
4. To turn on the AI agent, go to **Data and settings**, paste an Anthropic API key and click **Use key**. The key stays in the browser tab. It is only sent to `api.anthropic.com`.

The app needs an internet connection for its fonts, the CSV reader (Papa Parse, from cdnjs) and the AI calls. To open the demo sample directly, add `?demo` to the address.

## Data

**Real data, built in.** The app opens on real patient reviews. For 37 widely used drugs (birth control, antidepressants, painkillers, weight loss, ADHD, antibiotics and more), it ships with the 150 most helpful reviews of each drug from the public **Drugs.com review dataset** (UCI Machine Learning Repository, Gräßer et al. 2018, 215,063 reviews). Nothing to download.

**Real leaflets, built in.** For each of these drugs, the leaflet is pre-filled from its official **FDA label** (openFDA, the same labels as DailyMed). The side effects named in the boxed warning, warnings and adverse reactions sections are ticked automatically, and the app links to the label it used. When the AI names an effect outside the app vocabulary, the app also searches the full label text before raising an alert. You can still tick or untick effects by hand, and your changes are kept for each drug.

To rebuild this data (for example with other drugs, or more reviews per drug), edit the list at the top of `data/build_real_data.py` and run:

```bash
python3 data/build_real_data.py
```

It downloads the dataset from its Hugging Face copy (`datasets/lewtun/drug-reviews`) and queries the openFDA label API. Standard library only, plus `certifi` if your Python has no root certificates.

**AI results computed in advance.** Run this once, with an Anthropic API key, to read all 5,550 real reviews with the AI (about 300 calls to the fast model):

```bash
ANTHROPIC_API_KEY=sk-ant-... python3 data/precompute_ai.py
```

It writes `app/real_ai.js`. The app then opens with AI results for every real drug, and alert badges on every tile, even for viewers without Claude or a key. It uses the same prompt, vocabulary and model as the app, read from `app/index.html`. An interrupted run continues where it stopped.

**Any other drug.** To study any of the 3,671 drugs, download `drugsComTrain_raw.csv` (or the `.tsv`) from UCI or Kaggle ("UCI ML Drug Review dataset") and load it with **Upload a file** in Data and settings. The app reads the columns `drugName`, `condition`, `review`, `rating` and `usefulCount`. For uploaded files, you tick the known effects yourself.

**Demo sample.** The 66 demo reviews were written for the demo video. The drug names (Zentrolix, Calmarin, Dormexa, Asmira, Glucovia) are invented. Switch to them with **Demo sample**.

## How it works

1. **Reviews** come from the built-in Drugs.com data, the demo sample or an uploaded Drugs.com file.
2. **AI extraction.** A large language model (Claude) reads the reviews in batches of 20. For each review, it returns the side effects the patient really had, as JSON. It ignores effects the patient denies ("no nausea"), only fears, or that belong to the illness. This is zero-shot: no training data is needed.
3. **Normalisation.** Terms are mapped to a shared vocabulary of 37 effects (for example "heart racing" becomes palpitations).
4. **Leaflet check.** Each effect is marked "in leaflet" or "not in leaflet". For real drugs, the leaflet is the FDA label.
5. **Alerts.** One card per effect not in the leaflet, with counts, share of reviews and the patients' own words. A live tester compares the AI with a keyword search on any sentence.
6. **Agent with tools.** The agent can call two functions of the app, `get_signal_summary` and `get_reviews_for_effect`. It reads the results and the reviews, then answers the safety team.

Keyword mode uses regular expressions on the same vocabulary. It is the baseline, close to the bag of words seen in class. The "Why AI" section shows its errors, like negations it counts by mistake and paraphrases it misses.

## Going beyond the course

In class we built a bag of words and counted words. Vigi-Track uses a large language model that reads the whole sentence, plus an agent that decides which tools to call before it answers. The app also keeps a human in the loop. The agent advises, and experts decide.

## Limits

- A weak signal is a hypothesis, not a proof. It must be checked against official data (ANSM, EMA EudraVigilance, FDA FAERS).
- Online reviews are unverified, and reviewers are not a random sample of patients.
- The AI can make mistakes. Every signal links back to the real quotes so people can check.
- Not medical advice.

## Tests

```bash
pip install playwright && python3 -m playwright install chromium
python3 tests/test_app.py
```

The tests open the app in headless Chromium and check the demo, the built-in real data, the keyword search, the AI extraction, the agent and its tools, errors, the stop button, file upload, escaping of untrusted text, mobile width and dark mode. The Claude API is faked, so no key is needed.

## Reproduce the demo video

```bash
cd video-tools
npm install          # Papa Parse and the fonts used offline
pip install playwright numpy
python3 record.py    # films intro, app and outro, adds the music, writes video/Vigi-Track-demo.mp4
```

`record.py` needs Chromium (via Playwright) and ffmpeg. During filming, `mock.js` stands in for Claude so the video can be recorded offline with the same answers every time. The published app uses the real Claude. `music.py` generates the background music from code, so it is royalty free.
