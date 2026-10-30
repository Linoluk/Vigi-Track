# Changes

## Lighter version (`simple/`), after the submission

- New page `simple/index.html`, live at https://linoluk.github.io/Vigi-Track/simple/. Search a drug, then read the side effects people report or report your own. Same design as the full app.
- Reports are saved in a Supabase database (`supabase/setup.sql`). Without one, the page runs in demo mode and keeps reports in the browser.
- Read counts the Drugs.com reviews by keyword (`simple/seed.js`, built by `simple/build_seed.js`) plus the reports made on the page, and flags effects that are not in the FDA leaflet.
- AI: *Describe it in your own words* ticks symptoms from a free sentence, and the *Why AI* demo is back. Both run with Claude inside claude.ai, or with an Anthropic API key elsewhere. Their examples work without a key.
- Menu and *How it works* section. `tests/test_simple.py`: 32 checks, all pass. The full app (`app/`) is unchanged.

## Earlier changes (full app)

Made on top of `f3265c5`, before the submission.

## Real data, built in

- The app now opens on **real patient reviews**: the 150 most helpful Drugs.com reviews of 37 widely used drugs (5,550 reviews), in `app/real_data.js`. Before, users had to download and upload the Kaggle file themselves.
- Each real drug's **leaflet is pre-filled from its FDA label** (openFDA). The app links to the label it used. When the AI names an effect outside the vocabulary, the app also searches the full label text before raising an alert.
- `data/build_real_data.py` rebuilds this data. It needs no key.
- The demo sample is still one click away (**Demo sample**, or `?demo` in the address). File upload still works for the other 3,634 drugs.
- The hero quotes are now real reviews, each about an effect missing from the drug's FDA label.

## Ready to run, needs an API key

- `data/precompute_ai.py` runs the AI extraction once on all real reviews and writes `app/real_ai.js`. The app then shows AI results and alert badges at once, for every viewer. Until then, `app/real_ai.js` is an empty placeholder, and the app shows the keyword search first.

## Bugs fixed

- Picking another drug while the AI was reading mixed results: one drug's reviews were shown under another drug's name and compared with the wrong leaflet. A new drug now cancels the running work.
- Picking another drug while the agent was answering left the Ask button on, with a wrong "Done" status.
- Tile alert badges did not update after ticking or unticking a leaflet effect.
- Leaflet edits were lost when switching drugs. They are now kept for each drug.
- A refused API key showed "Claude was not allowed for this page". It now says the key was refused.
- The drug list showed only the first 400 drugs of an uploaded file.
- "ankle swelling" caught every kind of swelling. Renamed to "swelling".
- White text on 4 tile colours was below the WCAG AA contrast ratio. The colours are darker.
- An AI answer with ids written like `[z1]` lost those reviews.
- The extraction prompt now tells the model to ignore the effect the drug is taken for (for example weight loss with a weight loss pill).
- Vocabulary: 32 to 37 terms (weight loss, depression, suicidal thoughts, acne, irregular bleeding), plus medical synonyms (tachycardia, alopecia, oedema, urticaria…) so AI terms map correctly.
- Docs said "25 effects". `mock.js` answered the Calmarin question with the Zentrolix report.

## Tests

`tests/test_app.py`: 61 end-to-end checks in headless Chromium, with the Claude API faked. All pass.

## Finished after review

- Vocabulary: "irregular bleeding" no longer catches every bleeding (rectal or gum bleeding stays a separate effect), and "depression" no longer catches "respiratory depression".
- `docs/img/*.png` redone at 1440 px on the new version. The overview, drug tiles, FDA leaflet, AI tester and data screenshots use the real data. The alert, results and agent screenshots use the demo sample, read by the AI, because the real data has no AI results yet.
- `docs/USER_GUIDE.pdf` regenerated. Its source is now in the repo: `docs/guide/USER_GUIDE.html` and `docs/guide/build_guide.py`.
- The published claude.ai artifact runs this version, with `real_data.js` and `real_ai.js` next to the page.
- 61 tests pass.

## Not done

- `data/precompute_ai.py` was not run (it needs a paid Anthropic API key). `app/real_ai.js` is still the empty placeholder, so the real data opens on the keyword search. In Claude, "Read with AI" runs the AI live on the viewer's own account.
- The demo video still films the demo sample. It is still accurate, since the demo sample works as before.
