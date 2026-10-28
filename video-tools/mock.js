// Recording only: stands in for Claude so the demo video can be filmed offline with stable answers.
(function(){
const GOLD={
 z1:["nausea"],z2:["palpitations"],z3:[],z4:["dry mouth","dizziness"],z5:["hair loss"],z6:["palpitations"],z7:["insomnia"],
 z8:["headache"],z9:["palpitations"],z10:["headache","nausea"],z11:["hair loss"],z12:["insomnia"],z13:["palpitations"],z14:["decreased appetite"],
 c1:["ankle swelling"],c2:["tinnitus"],c3:["fatigue"],c4:["muscle pain"],c5:[],c6:["tinnitus"],c7:["dizziness"],c8:["muscle pain"],
 c9:["cough"],c10:["headache"],c11:[],c12:["tinnitus"],c13:["fatigue","muscle pain"],c14:[],
 d1:["drowsiness"],d2:["abnormal dreams"],d3:["memory problems"],d4:[],d5:["sleepwalking","memory problems"],d6:["dry mouth","taste changes"],
 d7:["abnormal dreams"],d8:["headache"],d9:["sleepwalking"],d10:["abnormal dreams"],d11:["memory problems"],d12:["nausea"],d13:[],d14:["drowsiness","dizziness"],
 a1:["hoarse voice"],a2:["abnormal dreams"],a3:["sore throat"],a4:["mood changes"],a5:[],a6:["abnormal dreams"],a7:["tremor"],a8:["mood changes"],
 a9:["headache"],a10:["abnormal dreams"],a11:["mood changes"],a12:[],
 g1:["diarrhea"],g2:["joint pain"],g3:["stomach pain"],g4:["blurred vision"],g5:[],g6:["decreased appetite"],g7:["joint pain"],g8:["nausea"],
 g9:["blurred vision"],g10:["headache"],g11:["joint pain"],g12:[]
};
function live(text){
  const t=text.toLowerCase(), out=[];
  if(/nightmare|dreams?/.test(t)) out.push("abnormal dreams");
  if(/heart is doing flips|heart (is )?(racing|pounding)/.test(t)) out.push("palpitations");
  if(/exhausted|tired/.test(t)) out.push("fatigue");
  if(/calves hurt|muscle/.test(t)) out.push("muscle pain");
  if(/hair/.test(t)&&!/no hair/.test(t)) out.push("hair loss");
  return out;
}
const ANSWERS={
 Asmira:`**Safety signal report · Asmira** (demo data, fictional drug)

The agent read 12 patient reviews. Two effects reported by patients are not in the leaflet.

1. **Abnormal dreams**, 3 reviews (25%). Parents describe children who wake up screaming or have nightmares every night. Priority high, because children are involved.
2. **Mood changes**, 3 reviews (25%). Patients report irritability, anger and mood swings that started with the treatment. Priority high.

The other effects found (hoarse voice, sore throat, tremor, headache) are already in the leaflet.

**Next step.** Check both signals against official reports in EudraVigilance and the ANSM database. Patient reviews are unverified and cannot prove the drug caused these effects.`,
 Zentrolix:`**Safety signal report · Zentrolix** (demo data, fictional drug)

The agent read 14 patient reviews. Two effects reported by patients are not in the leaflet.

1. **Palpitations**, 4 reviews (29%). A racing or pounding heart, sometimes at rest. One patient stopped the treatment. Priority high.
2. **Hair loss**, 2 reviews (14%). It appears after about two months. Priority medium.

**Next step.** Check these signals against EudraVigilance and the ANSM database. Reviews are unverified and cannot prove causality.`,
 Dormexa:`**Investigate memory problems first.** (demo data, fictional drug)

Memory problems appear in 3 of 14 reviews (21%) and are not in the leaflet. Two patients did things at night with no memory of them, like a full conversation or eating at 2am. That is a safety risk.

**Sleepwalking** is linked to it, with 2 reviews (14%). Review both together, as complex night behaviours. **Abnormal dreams** (3 reviews) come next.

Before any action, compare with official reports (EudraVigilance, ANSM). Reviews are unverified and cannot prove causality.`,
 Glucovia:`**Investigate joint pain first.** (demo data, fictional drug)

Joint pain appears in 3 of 12 reviews (25%) and is not in the leaflet. One patient stopped walking because of hip pain. **Blurred vision** follows with 2 reviews (17%).

Before any action, compare with official reports (EudraVigilance, ANSM). Reviews are unverified and cannot prove causality.`
};
ANSWERS.Calmarin=ANSWERS.Zentrolix;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function stream(text,onText){ let out=""; const parts=text.match(/\S+\s*/g)||[]; for(const p of parts){ out+=p; onText&&onText({text:out,delta:p}); await sleep(24);} return out; }
async function sample(input,opts={}){
  const turns=Array.isArray(input)?input:[{role:"user",content:input}];
  const last=turns[turns.length-1].content;
  const drug=(last.match(/Drug: (\w+)/)||[])[1]||"Zentrolix";
  if(opts.tools){
    await sleep(800);
    const sum=await opts.tools.find(t=>t.name==="get_signal_summary").execute({});
    await sleep(600);
    const t2=opts.tools.find(t=>t.name==="get_reviews_for_effect");
    for(const e of sum.effects.filter(x=>!x.in_leaflet).slice(0,2)){ await t2.execute({effect:e.effect,limit:6}); await sleep(550); }
  }
  const text=await stream(ANSWERS[drug]||ANSWERS.Zentrolix,opts.onText);
  return {text,truncated:false,modelTierApplied:"default"};
}
sample.json=async(prompt)=>{
  const lines=[...prompt.matchAll(/^\[(\w+)\] (.*)$/gm)];
  await sleep(lines.length===1?900:1500);
  return lines.map(m=>({id:m[1],effects:m[1]==="live"?live(m[2]):(GOLD[m[1]]||[])}));
};
sample.limits=async()=>({maxPromptBytes:262144,tools:{maxCount:8}});
window.claude={use:async n=>n==="sample"?sample:null};
})();
