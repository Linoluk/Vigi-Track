"""Builds the real data shipped with the app: app/real_data.js and data/real_leaflets.csv.

Reviews: the Drugs.com review dataset (UCI, Grasser et al. 2018, 215,063 reviews), read from its
Hugging Face copy (datasets/lewtun/drug-reviews). For each selected drug, the app keeps the most
helpful reviews (highest usefulCount).
Leaflets: the side effects named in the drug's FDA label (openFDA drug label API), in the sections
boxed warning, warnings (and precautions) and adverse reactions, mapped to the app vocabulary.

Usage: python3 data/build_real_data.py [CACHE_DIR]     (needs internet, standard library only)
"""
import csv, html, json, pathlib, re, ssl, sys, time, urllib.parse, urllib.request
try:  # python.org builds on macOS ship without root certificates
    import certifi; SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL = ssl.create_default_context()
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / ".cache")
HF = "https://huggingface.co/datasets/lewtun/drug-reviews/resolve/main/{}.jsonl"
PER_DRUG = 150

# Drug name in the dataset, class shown in the app, openFDA search
DRUGS = [
    ("Mirena", "Hormonal IUD", 'openfda.brand_name:"Mirena"'),
    ("Nexplanon", "Contraceptive implant", 'openfda.brand_name:"Nexplanon"'),
    ("Ethinyl estradiol / norethindrone", "Birth control pill", None),
    ("Depo-Provera", "Contraceptive injection", 'openfda.brand_name:"Depo-Provera"'),
    ("Sertraline", "Antidepressant (SSRI)", None),
    ("Escitalopram", "Antidepressant (SSRI)", None),
    ("Citalopram", "Antidepressant (SSRI)", None),
    ("Fluoxetine", "Antidepressant (SSRI)", None),
    ("Paroxetine", "Antidepressant (SSRI)", None),
    ("Venlafaxine", "Antidepressant (SNRI)", None),
    ("Duloxetine", "Antidepressant (SNRI)", None),
    ("Bupropion", "Antidepressant", None),
    ("Vortioxetine", "Antidepressant", None),
    ("Mirtazapine", "Antidepressant", None),
    ("Trazodone", "Antidepressant, sleep", None),
    ("Amitriptyline", "Tricyclic antidepressant", None),
    ("Phentermine", "Weight loss", None),
    ("Contrave", "Weight loss", 'openfda.brand_name:"Contrave"'),
    ("Liraglutide", "Diabetes, weight loss", None),
    ("Clonazepam", "Benzodiazepine", None),
    ("Alprazolam", "Benzodiazepine", None),
    ("Buspirone", "Anxiety", None),
    ("Gabapentin", "Nerve pain, seizures", None),
    ("Pregabalin", "Nerve pain", None),
    ("Tramadol", "Opioid painkiller", None),
    ("Topiramate", "Migraine, seizures", None),
    ("Quetiapine", "Antipsychotic", None),
    ("Aripiprazole", "Antipsychotic", None),
    ("Lamotrigine", "Mood stabiliser", None),
    ("Varenicline", "Stop smoking", None),
    ("Zolpidem", "Sleeping pill", None),
    ("Lisdexamfetamine", "ADHD", None),
    ("Methylphenidate", "ADHD", None),
    ("Isotretinoin", "Acne", None),
    ("Doxycycline", "Antibiotic", None),
    ("Metronidazole", "Antibiotic", None),
    ("Nitrofurantoin", "Antibiotic", None),
]

# How each effect of the app vocabulary is written in an FDA label
LABEL = {
    "nausea": r"nausea|vomiting", "headache": r"headache|migraine", "insomnia": r"insomnia|difficulty sleeping|sleep disorder",
    "dry mouth": r"dry mouth|dryness of (the )?mouth|xerostomia", "dizziness": r"dizziness|vertigo|light-?headed",
    "decreased appetite": r"(decreased|loss of|reduced) appetite|appetite decreased|anorexia",
    "palpitations": r"palpitation|tachycardia", "hair loss": r"alopecia|hair loss", "weight gain": r"weight (gain|increase)|increased weight",
    "weight loss": r"weight (loss|decrease)|decreased weight", "anxiety": r"anxiety|nervousness", "depression": r"depress",
    "fatigue": r"fatigue|asthenia|tiredness|lethargy",
    "swelling": r"edema|swelling", "cough": r"cough", "tinnitus": r"tinnitus", "muscle pain": r"myalgia|muscle (pain|cramp|spasm)",
    "drowsiness": r"somnolence|drowsiness|sedation", "abnormal dreams": r"abnormal dreams|nightmare|vivid dreams|dream abnormal|dream disturbance",
    "memory problems": r"amnesia|memory (impairment|loss|problems|difficult|disturbance)|difficulty with memory|impaired memory|forgetful", "sleepwalking": r"sleep-?walking|complex sleep behavio",
    "taste changes": r"dysgeusia|ageusia|taste (perversion|disturbance|alteration|change|loss)|(altered|abnormal|bad|metallic|unpleasant) taste",
    "mood changes": r"mood (swings|changes|altered)|irritability|aggressi|agitation|emotional lability|affect lability|hostility",
    "suicidal thoughts": r"suicid", "hoarse voice": r"hoarse|dysphonia", "sore throat": r"pharyngitis|sore throat|throat pain",
    "tremor": r"tremor", "stomach pain": r"abdominal pain|stomach|dyspepsia", "joint pain": r"arthralgia|joint pain",
    "blurred vision": r"blurr|visual disturbance|abnormal vision|vision abnormal", "rash": r"rash|urticaria|pruritus",
    "acne": r"acne", "diarrhea": r"diarrh", "constipation": r"constipation", "sweating": r"sweating|hyperhidrosis|diaphoresis|perspiration",
    "sexual dysfunction": r"libido|sexual dysfunction|erectile|ejaculat|orgasm|impotence",
    "irregular bleeding": r"(vaginal|uterine|menstrual|breakthrough|intermenstrual|irregular) bleeding|spotting|metrorrhagia|menorrhagia|amenorrh",
}
SECTIONS = ["boxed_warning", "warnings_and_cautions", "warnings", "precautions", "adverse_reactions"]

def get(url, path):
    if not path.exists():
        print("download", url); path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, context=SSL) as r: path.write_bytes(r.read())
    return path

def fda_label(name, query):
    if not query:
        parts = [p.strip() for p in name.split("/")]
        query = " AND ".join(f'openfda.generic_name:"{p}"' for p in parts)
        n_parts = len(parts)
    else:
        n_parts = None
    url = "https://api.fda.gov/drug/label.json?" + urllib.parse.urlencode(
        {"search": f"({query}) AND _exists_:adverse_reactions", "limit": 50})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60, context=SSL) as r: res = json.load(r)["results"]; break
        except Exception as e:
            print("  retry", name, e); time.sleep(2)
    else:
        sys.exit(f"openFDA did not answer for {name}. Check the connection and run again.")
    def ok(r):  # same number of active ingredients, so "sertraline" does not pick a combination product
        if n_parts is None: return True
        g = " ".join(r.get("openfda", {}).get("generic_name", [""])).lower()
        return g.count(" and ") + 1 == n_parts
    res = sorted([r for r in res if ok(r)] or res, key=lambda r: r.get("effective_time", ""), reverse=True)
    return res[0] if res else None

def clean_cond(c):
    if not c or "</span>" in c or c.startswith("Not Listed"): return ""
    for a, b in (("Disorde", "Disorder"), ("ibromyalgia", "Fibromyalgia"), ("mance Anxiety", "Performance Anxiety")):
        if c.endswith(a) or c == a: c = c[: -len(a)] + b
    return c

def main():
    rows = []
    for split in ("train", "test"):
        for line in open(get(HF.format(split), CACHE / f"{split}.jsonl")):
            rows.append(json.loads(line))
    totals = Counter(r["drugName"] for r in rows)
    drugs, reviews, conds, leaf_rows = [], [], [], []
    for di, (name, cls, query) in enumerate(DRUGS):
        mine = sorted((r for r in rows if r["drugName"] == name), key=lambda r: (-r["usefulCount"], r["Unnamed: 0"]))
        seen, keep = set(), []
        for r in mine:
            text = html.unescape(r["review"]).strip().strip('"').strip()
            if not text or text in seen: continue
            seen.add(text)
            cond = clean_cond(r["condition"])
            if cond not in conds: conds.append(cond)
            keep.append([str(r["Unnamed: 0"]), di, int(r["rating"]), int(r["usefulCount"]), conds.index(cond), text])
            if len(keep) == PER_DRUG: break
        reviews += keep
        lab = fda_label(name, query)
        known, label = [], None
        if lab:
            text = " ".join(" ".join(lab.get(s, [])) for s in SECTIONS).lower()
            known = [k for k, rx in LABEL.items() if re.search(rx, text)]
            words = re.sub(r"[^a-z]+", " ", text).split()   # kept so the app can check effects outside the vocabulary
            text = " ".join(w for i, w in enumerate(words) if i == 0 or w != words[i - 1])
            of = lab.get("openfda", {})
            label = {"title": (of.get("brand_name") or of.get("generic_name") or [name])[0], "set_id": lab.get("set_id"),
                     "date": lab.get("effective_time", "")[:8], "text": text}
        top = Counter(conds[k[4]] for k in keep if conds[k[4]])
        drugs.append({"name": name, "cls": cls, "total": totals[name], "cond": [c for c, _ in top.most_common(2)],
                      "leaflet": known, "label": label})
        for k in known: leaf_rows.append((name, k))
        print(f"{name:36s} {len(keep):4d}/{totals[name]:5d} reviews  label: {label and label['title']} {label and label['date']}  {len(known)} effects")
    data = {"source": "Drugs.com review dataset (UCI ML Repository, Grasser et al. 2018), most helpful reviews per drug. "
                      "Leaflet: side effects named in the FDA label (openFDA).",
            "dataset_size": len(rows), "per_drug": PER_DRUG, "conds": conds, "drugs": drugs, "reviews": reviews}
    out = ROOT / "app" / "real_data.js"
    out.write_text("/* Generated by data/build_real_data.py. Real patient reviews from the Drugs.com dataset, leaflets from openFDA. */\n"
                   "window.VT_REAL=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    with open(ROOT / "data" / "real_leaflets.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["drugName", "known_side_effect"]); w.writerows(leaf_rows)
    print(out, round(out.stat().st_size / 1e6, 2), "MB,", len(reviews), "reviews,", len(drugs), "drugs")

if __name__ == "__main__":
    main()
