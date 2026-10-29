/* Vigi-Track Simple: the list of symptoms the app knows, and how to spot them in a text.
   Copied from the full app (app/index.html). Used by the page and by build_seed.js. */
const LEX = {
  "nausea":/\b(nausea|nauseous|nauseated|threw up|throw up|throwing up|vomit\w*|sick to my stomach)\b/i,
  "headache":/\b(headaches?|migraines?)\b/i,
  "insomnia":/\binsomnia\b|can'?t sleep|cannot sleep|trouble sleeping|awake until/i,
  "dry mouth":/dry mouth/i,
  "dizziness":/\bdizz\w*|light-?headed/i,
  "decreased appetite":/lost my appetite|loss of appetite|no appetite|appetite loss|decreased appetite/i,
  "palpitations":/palpitation|tachycardia|heart (is |started )?(racing|pounding)|(racing|pounding) heart/i,
  "hair loss":/hair (is )?(falling out|loss|thinning)|losing (my )?hair|thinning hair|alopecia/i,
  "weight gain":/weight gain|gained weight|put on weight/i,
  "weight loss":/weight loss|lost (\d+ ?(lbs?|pounds|kg)|(some |a lot of )?weight)|los(e|ing) weight/i,
  "anxiety":/\banxi(ety|ous)\b/i,
  "fatigue":/\b(tired|fatigue|exhausted|exhausting|no energy)\b/i,
  "swelling":/\bswell\w*|swollen|\bo?edema\b/i,
  "cough":/\bcough\w*/i,
  "tinnitus":/tinnitus|ringing in (my )?ears|ears? ringing/i,
  "muscle pain":/muscle (pain|aches?|cramps?)|legs ache|sore muscles|myalgia/i,
  "drowsiness":/\b(drowsy|drowsiness|grogg\w*|sleepy|somnolence)\b/i,
  "abnormal dreams":/nightmares?|(vivid|bad|intense|horrible|strange|abnormal) dreams?/i,
  "memory problems":/memory|can'?t remember|cannot remember|forgetful|amnesia/i,
  "sleepwalking":/sleep ?walk\w*|sleep-walk\w*/i,
  "taste changes":/metallic taste|taste chang\w*|dysgeusia/i,
  "mood changes":/mood (swings?|changes?)|irritab\w*|short-tempered|aggressi\w*/i,
  "depression":/(?<!(respiratory|cns|breathing|bone marrow) )\bdepress(ed|ion|ive|ing)\b/i,
  "suicidal thoughts":/suicid\w*/i,
  "hoarse voice":/hoarse\w*/i,
  "sore throat":/sore throat/i,
  "tremor":/\btremors?\b|shak(y|ing) hands?|trembl\w*/i,
  "stomach pain":/stomach (pain|ache|cramps?)|abdominal pain|belly pain/i,
  "joint pain":/joint pain|joints? (ache|aches|hurt)|achy joints|aching joints|arthralgia/i,
  "blurred vision":/blurr?(ed|y) vision|vision (is |gets )?blurr?y|blurry/i,
  "rash":/\brash\b|\bhives\b|\bitch\w*|urticaria|pruritus/i,
  "acne":/\bacne\b|break ?outs?\b|\bpimples?\b/i,
  "diarrhea":/diarrh?o?ea|diarrhea/i,
  "constipation":/constipat\w*/i,
  "sweating":/sweating|night sweats|hyperhidrosis/i,
  "sexual dysfunction":/libido|sex drive|erectile/i,
  "irregular bleeding":/\bspotting\b|breakthrough bleed\w*|bleed\w* between periods|(irregular|heavy|prolonged|constant|non-?stop|continuous) (periods?|bleed\w*)|vaginal bleed\w*|\bbled\b|bleeding (for|every|all|non-?stop|constantly|on and off)|irregular bleeding/i
};
const DESC = {
  "palpitations":"A racing, pounding or skipping heartbeat.","hair loss":"Hair thinning or falling out.","tinnitus":"Ringing or buzzing in the ears.",
  "muscle pain":"Aching, cramping or sore muscles.","abnormal dreams":"Very intense dreams or nightmares, night after night.","memory problems":"Gaps in memory, forgetting recent events.",
  "sleepwalking":"Getting up and doing things at night without remembering.","taste changes":"A metallic or strange taste in the mouth.","mood changes":"Irritability, anger or mood swings.",
  "joint pain":"Aching knees, hips, fingers or other joints.","blurred vision":"Foggy or blurry eyesight.","weight gain":"Putting on weight.","anxiety":"Feeling anxious or nervous.",
  "fatigue":"Feeling tired or exhausted.","rash":"Skin rash, hives or itching.","sweating":"Heavy sweating, often at night.","sexual dysfunction":"Lower sex drive or erection problems.",
  "swelling":"Swollen ankles, legs or other parts of the body.","weight loss":"Losing weight without trying to.","depression":"Feeling low, sad or hopeless.",
  "suicidal thoughts":"Thoughts of self-harm or suicide.","acne":"Spots, pimples or breakouts.","irregular bleeding":"Spotting, bleeding between periods or very long periods."
};

const VOCAB = Object.keys(LEX);

/* A match does not count when a negation comes just before it, in the same part of the sentence
   ("no nausea", "never had headaches", but not "no nausea but headaches"). */
const NEG = /\b(no|not|never|without|zero|didn'?t|don'?t|haven'?t|hasn'?t|wasn'?t|isn'?t)\b/i;
function negated(before){
  const parts = before.split(/[.!?,;:]|\bbut\b|\band\b|\bthen\b/i);
  return NEG.test(parts[parts.length - 1]);
}
function findSymptoms(text){
  const found = [];
  for (const k of VOCAB){
    const re = new RegExp(LEX[k].source, "gi");
    let m;
    while ((m = re.exec(text))){
      if (!negated(text.slice(Math.max(0, m.index - 30), m.index))){ found.push([k, m.index]); break; }
    }
  }
  return found;
}
if (typeof module !== "undefined") module.exports = { LEX, DESC, VOCAB, findSymptoms };
