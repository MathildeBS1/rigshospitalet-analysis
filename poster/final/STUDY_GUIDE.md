# Study Guide — Exam Preparation
## Group 15 | Rigshospitalet OR Scheduling | From Analytics to Action (42577) DTU Spring 2026

> **Exam format:** Poster pitch (max 12 min) + individual oral questioning on syllabus (45 min total for 6 students). Oral answers worth 50%. Examiners: Anders, Tanja + external censor.
> **Assessment criteria:** Answers must *clarify the pitch*, demonstrate *thorough understanding of the course*, ability to *explain, apply, and reflect on key concepts*, well-argued and clearly reasoned.

---

## HOW TO USE THIS GUIDE

The examiners will use your poster as a springboard to test whether you understand the **social science concepts behind your choices**. They are not testing data science — they are testing whether an engineer can think like a social scientist about data. Every number on your poster should connect to at least one course concept.

---

## PART 1: THE COURSE FRAMEWORK IN ONE PAGE

The course has **4 themes**, each with core concepts. Know them cold.

| Theme | Lectures | Core question |
|---|---|---|
| 1. Organizational context | 1–3 | Why do data projects fail organizationally even when technically correct? |
| 2. Making data valuable | 4–6 | How is data produced, structured, and made actionable? |
| 3. Challenges in data economy | 7–10 | What ethical, political, and social tensions arise from datafication? |
| 4. Presentation & communication | 11+ | How do you translate analytics into organizational action? |

---

## PART 2: CONCEPT DICTIONARY (What the examiners will use)

### Theme 1 — Organizational Context

**Source: Winthereik, Feb 9 Lecture**

**Affordance (Davis)**
> "What the environment *offers* to a person or group of employees."
- Mechanisms: *request, demand, encourage, discourage, refuse, allow*
- Conditions: *perception, dexterity, cultural and institutional legitimacy*
- **Your case:** The OR scheduling system *affords* zero-prep planning — it doesn't require schedulers to enter prep time. The system's design makes the bad behavior the path of least resistance. Fixing it means changing what the system *affords*.

**Invisible work (Justesen & Plesner)**
> "Activities that are informal, unaccounted for, and undervalued, but that nevertheless keep organizational performance on track."
- Includes: **connecting** data sets, **compensating** for missing/bad data, **cleaning** data
- "Accountability drains" = lack of organizational learning because invisible work is not designed for
- **Your case:** The 63.5% simultaneous-click rate on room prep timestamps is evidence of invisible work. Staff click "start" and "done" simultaneously because the system doesn't fit their workflow — they are compensating for a system that demands timestamps they cannot realistically capture.

**Organizational fabric (Winthereik)**
> "Intertwined social and technical threads to understand organizations through organizing processes."
- Implementation of technology is an *ongoing process* that makes organizations
- Consider power structures and access to technologies
- **Your case:** Rigshospitalet has 90% clinically trained management — decisions about scheduling are made by people whose professional identity is clinical, not operational. The scheduling failure reflects an organizational fabric where OR efficiency optimization is not the primary concern.

**Co-production (Jasanoff, 2004)**
> "Society and scientific knowledge influence and shape each other."
- In companies: everyday norms and routines AND systems evolve together
- **Your case:** The OR management system and OR staff practices have co-produced a situation where "zero prep" is the norm. Changing the schedule requires changing both the system AND the professional culture around it.

**Socio-technical problem / "Technical fix"**
> A "technical fix" attempts to solve a sociotechnical problem where there is little attention to organizational/social elements.
- "Technical systems and analytics do not create better performance on their own — organizations do!" (Winthereik)
- **Your case:** A lookup table alone is a technical fix. Real implementation requires organizational buy-in, workflow changes, and trust in the new allocation numbers.

**The 5 affordances of IT (Zammuto)**
1. Visualizing entire work processes
2. Real-time/flexible product and service creation
3. Virtual collaboration
4. Mass collaboration
5. **Simulation/synthetic representation** ← your poster uses this

---

### Theme 2 — Making Data Valuable

**Source: Datafication (Lecture 4, Madsen); PDD (Lecture 6, Madsen); Exploratory Data Viz (Lecture 5)**

**Datafication (Mejias & Couldry, 2019)**
> "Something is made into data" — *it's a verb*
- Data = "material produced by abstracting the world into categories, measures and other representational forms" (Kitchin, 2014)
- Datafication ≠ digitization. "Digitalization turbocharges datafication, but is not a substitute." (Cukier & Schönberger, 2013)
- **Your case:** The OR management system *datafied* surgical workflows — converting operations (patient entry, procedure start, room cleaning) into timestamps. The choice of *which* timestamps to capture, and how, shapes what can be analyzed. The simultaneous-click problem is a direct consequence of a datafication design that didn't fit staff reality.

**"Raw data is an oxymoron and a bad idea" (Geoffrey Bowker)**
- Data is always produced under specific conditions, classifications, and interests
- **Your case:** The 66% corrupted prep timestamps are not a neutral "data quality problem" — they reflect a datafication design choice about what to measure and how.

**Four analytical moments of datafication (Flyverbom & Madsen)**
| Moment | Definition | Your case |
|---|---|---|
| **Production** | Human conduct translated into a data stream | Timestamps recorded (or not) by OR staff |
| **Structuring** | Choices about databases, classification, metadata | How "prep time" was defined (or left undefined) in the OR system |
| **Distribution** | How access to data is negotiated | Your team received 2 years of data from the analytics team |
| **Visualization** | Turning data into insights | Your diverging bar chart, heatmap, Gantt |

Central datafication questions the examiners may ask:
- "How was your data made and how is it now made available to you? Could it be otherwise?"
- "Who made it and with what interests?"
- "What would need to change on the level of production/structuring/distribution for you to best address the challenge?"

**Data as tool / commodity / practice / algorithmic intelligence (Xu et al., 2024)**
- *Data as tool*: emphasis on data literacy
- *Data as commodity*: data as source of profit
- *Data as practice*: embedding data in repeatable processes
- *Data as algorithmic intelligence*: replacing/enhancing human decision-making
- **Your case:** You propose data as *practice* (lookup table embedded in the scheduling workflow) + data as *algorithmic intelligence* (the gradient boosting model as future refinement).

**Value requires 'fit' with context (Datafication lecture)**
- Data analysis must align with organizational context to be actionable
- **Your case:** You explicitly chose the lookup table over ML *because* it fits the hospital's current context (no ML infrastructure, clinical staff need to trust it).

**Participatory Data Design (PDD) (Jensen et al., 2021; Madsen, 2024)**
> "Involvement of stakeholders in data science projects — active participation, typically upstream, influencing choices relating to datafication, analysis, and/or presentation."
- Often through **data sprints**: workshops where pilot projects are co-developed
- "Visualization can do the same work that cheap materials like cardboard boxes and Lego bricks did in the Scandinavian tradition of participatory design"
- **Boundary object**: data as something that allows different stakeholders to work together despite different interests
- Professional intuition ↔ Data patterns (iterative cycle)
- **Your case:** The examiners may ask: *"To what extent did you involve Rigshospitalet stakeholders in your analysis?"* Your honest answer: Maja (from the analytics team) gave you the data and framing. You did not run data sprints with OR schedulers or clinical staff. This is a legitimate limitation.

**Exploratory Data Viz (Lecture 5, Sapienza & Lehmann, 2021)**
> "The process of investigating datasets and discovering questions through that investigation."
- Data scientists are *not* purely hypothesis-driven — "we form informal theories of what might be driving the patterns we see"
- ML types recap: Rule-based (hypothesis-driven) → Supervised ML → Unsupervised ML (explorative)
- **Your case:** You started with EDA (looking at distributions, outlier rates) before settling on the prep allocation analysis. The 63.5% simultaneous-click discovery is a finding that came from EDA, not a prior hypothesis.

---

### Theme 3 — Challenges in the Data Economy

**Source: Ethics (Lecture 7, March 16); Resistance (Lecture 9, April 13); Environmental Impact (Lecture 10)**

**Data ethics of power (Hasselbalch, 2021)**
> "Addresses the distribution of power and power relations in the Big Data Society."
- Key questions: *Whose interests are prioritized? Who is empowered? Who is disempowered?*
- Data interest analysis: **micro** (design), **meso** (organization), **macro** (culture, geopolitics)
- **Your case:** Who benefits from the current zero-prep scheduling? The system is easier to manage if you never allocate prep time — schedulers face no constraint. Who is harmed? Patients (surgery overruns cascade into their day), OR staff (working against an impossible plan), hospital management (the overrun metric "55% of cases overrun" is dominated by a planning error, not operational failure — making it noise rather than signal).

**Data governance models (Micheli et al., 2020)**
| Model | Who controls | Goal |
|---|---|---|
| Data Sharing Pools (DSP) | Multiple orgs share | Innovation |
| Data Cooperatives (DC) | Citizens collectively | Empower citizens |
| **Public Data Trusts (PDT)** | Public institutions | Responsible public policy |
| Personal Data Sovereignty (PDS) | Individuals | Self-determination |
- **Your case:** Rigshospitalet's data sits within a **Public Data Trust** model — Region Hovedstaden manages patient and operational data for public good. This limits what can be done with the data and who can access it.

**ALTAI (Assessment List for Trustworthy AI — EU High-Level Expert Group)**
Seven requirements for trustworthy AI:
1. Human agency and oversight
2. Technical robustness and safety
3. Privacy and data governance
4. Transparency
5. Diversity, non-discrimination and fairness
6. Environmental and societal well-being
7. Accountability
- "Any one of these ethical requirements could be a design choice (and a form of innovation)"
- **Your case:** Your *recommendation of the lookup table over ML* directly addresses requirements 1, 3, 4, and 7 — the table is transparent, auditable, and keeps humans in the loop. Frame it this way if asked about AI ethics.

**Three categories of unethical data use (Ethics lecture)**
1. Misuse of personal data (Cambridge Analytica)
2. Manipulation of data systems (Volkswagen Dieselgate)
3. Abuse of data access (Uber "God View")
- **Your case:** Your data is aggregate operational data, not personal patient data. However, the *simultaneous-click* behavior could be seen as staff *subversion* of the recording system — a mild form of resistance.

**Resistance in the data-driven society (Milan, 2024)**
> "Intentional actions taken in opposition to someone or something, arising from a refusal to conform to social norms or accept the status quo."

Where resistance happens:
- In data *collection* (what people choose to share)
- In data *generation* (how they behave because of systems)
- In *system interaction* (workarounds)

Why data systems generate resistance:
- They *simplify reality*, enforce categories, reward certain behaviors

Resistance types:
- **Defensive:** self-defence, subversion, avoidance
- **Productive:** literacy, counter-imagination, advocacy campaigning

**Your case — this is very directly relevant (examiners literally asked it in Lecture 9):**
> *"What forms of resistance to datafication can you envision related to the cases you work on (Rigshospitalet)?"*

Strong answer: 
1. *Subversion*: The 63.5% simultaneous-click rate IS resistance — staff click both timestamps at once because the system demands they record something they cannot realistically track. They are working around an impossible requirement.
2. *Avoidance*: 80.9% of cases get zero planned prep because schedulers don't enter prep time — this is avoidance of a field they don't trust or see value in completing.
3. If a lookup table is implemented, expect *resistance from schedulers* who don't trust the numbers — they will want to verify values against their own experience (hence the explainability argument for the lookup table over ML).
4. *Meaningless work*: If the scheduling system forces staff to enter unrealistic prep times to satisfy a system requirement without actual workflow change, it becomes meaningless work.

**Meaningless work (Hoeyer & Wadmann, 2020)**
> "Experiences of meaningless work partly result from technologically mediated ways of making sense of work."
- Organizational environment creates *interconnectedness through data*: being seen as doing important work requires standardized data that can travel across contexts
- Consequences: financial costs, epistemic doubt, changed moral landscape
- "'Good data' are no longer justified with reference to their support of clinical outcome" (p.447)
- **Your case:** OR staff recording timestamps simultaneously = meaningless work. The data entry requirement exists to satisfy a system, not to improve clinical decisions. Your fix (validation rule enforcing minimum time between timestamps) directly addresses this.

**Supply chain capitalism of AI (Tsing, 2009 / Lecture 10)**
- AI has environmental and labor costs: mines, data centres, e-waste, data annotators
- "Algorithmic harm" = understanding resources and labor to make data available
- **Your case:** Your recommendation of a lookup table over a continuously retrained ML model has an environmental argument — simpler tools have smaller compute footprints.

---

### Theme 4 — Presentation & Communication

**"Numbers rarely speak for themselves" (Shapin & Schaffer, 1985)**
> "In the self-evident method of inquiry, the presuppositions of our own culture's routine practices are not regarded as in need of explanation."
- Statistics are rarely self-evident — cultural bias toward numbers as requiring no proof
- We need to understand not just the technology and methodology, but also the *cultural assumptions* to provide a good translation from analytics to action.

**"Numbers that speak for themselves" vs. "Stories that resonate"**
- Data analysts must learn to tell stories to aptly illustrate a situation
- Role of *ethical storytellers*: if data analysts are aware of this role, it makes for actionable data that resonates with organizational strategies
- **Your case:** Your three-panel poster is a story: Problem → Fix → Impact. That structure is deliberate and course-aligned.

**The data we have vs. the data we would like to have**
- Slide from intro lecture: small circle (data we have) vs. large circle (data we would like to have)
- **Your case:** You want clean room prep timestamps — you have corrupted ones. Your data quality recommendation closes this gap. Frame it explicitly this way.

---

## PART 3: LIKELY EXAM QUESTIONS AND STRONG ANSWERS

### On datafication

**Q: How was your data produced, and what choices in that production process shaped your analysis?**

A: The OR management system datafied surgical workflows into timestamps. The key structuring choice was how "prep time" was defined — the system has a `planned prep` field that 80.9% of schedulers leave at zero, and a `room prep` window where 63.5% of records show simultaneous start and done clicks. These datafication choices created the core tension: the analysis we could do confidently (W1 + W2, full coverage) versus the analysis that would have been most complete (room prep, only 32.5% usable). The four analytical moments framework (Flyverbom & Madsen) helps explain this: *production* (staff clicking timestamps), *structuring* (how the system defines prep fields), *distribution* (us receiving the data), and *visualization* (our three charts).

---

### On organizational context

**Q: Your recommendation is a lookup table. What organizational barriers might prevent it from being adopted?**

A: Several using course concepts:
1. *Affordance* — the current scheduling system doesn't require prep time entry. Implementing the table requires changing what the system affords: adding validation, making prep time a mandatory field.
2. *Invisible work* — schedulers have developed invisible compensating routines around the current system's gaps. A new allocation requirement disrupts those routines without being designed for the compensating work it creates.
3. *Organizational fabric* — Rigshospitalet has 90% clinically trained management. OR scheduling efficiency is secondary to clinical priorities. The table needs clinical endorsement to travel through the organizational hierarchy.
4. *Resistance* — Milan (2024): staff who see prep allocation as another meaningless data entry task (Hoeyer & Wadmann, 2020) will enter whatever number satisfies the system, not a thoughtful estimate.

---

### On ethics

**Q: Who benefits and who is disadvantaged by your proposed change?**

A: Using the data interest analysis framework (Hasselbalch, micro/meso/macro):
- *Micro (design)*: The lookup table benefits schedulers who currently work against an impossible plan. It disadvantages schedulers who currently avoid thinking about prep time.
- *Meso (organization)*: Management benefits — the delay metric becomes signal rather than noise. But implementing a validation rule creates new work for IT and requires policy change.
- *Macro (culture/geopolitics)*: The analysis could create pressure on clinical staff to adhere to stricter time windows, potentially increasing surveillance of their work. The "meaningless work" critique (Hoeyer & Wadmann) is relevant: if the data entry becomes a compliance exercise rather than a genuine planning tool, it makes clinical work worse, not better.

---

### On the simulation/impact claim

**Q: Your poster says "~20,600 fewer overruns." That seems like a very strong claim. Is it justified?**

A: It is a *counterfactual simulation*, the standard methodology in OR scheduling research (Dexter & Macario). It holds actual events fixed — same patients, same procedure durations — and recomputes the overrun metric under the new prep allocation. The "~20,600" means those cases would flip from "overrun" to "on time" purely because the plan now accounts for prep time. Mean overrun shifts from +9.5 min to −19.5 min; the overrun rate drops from 55% to 38%.

The key distinction: we are making the *schedule tell the truth*, not changing what physically happens in the OR. A surgery that currently takes 90 min still takes 90 min — but if the schedule now allocates 30 min of prep before it, what was a 30-min overrun becomes on time. The causal question (does a better plan lead to fewer *actual* overruns through behaviour change?) would require a before/after study — which we recommend as a follow-up.

In course terms (Shapin & Schaffer): "numbers rarely speak for themselves." The 20,600 number needs this story to be honest.

---

### On data quality

**Q: Your analysis excludes 67.5% of room prep data. Doesn't that bias your results?**

A: Yes, and we explicitly flag it. The clean room prep subset (32.5%) is not a random sample — it has a 79.2% anesthesia rate versus 62.4% in the full population, and skews toward more complex procedures. Using this subset to build predictions would introduce selection bias. That is why we pivoted to W2 (patient-side prep), which has 99.3% coverage and only 2.1% simultaneous-click issues — a data quality problem an order of magnitude smaller.

The data quality recommendation (add validation in the OR management software enforcing a minimum time between "start" and "done" clicks) is a direct application of the datafication lecture's central questions: "What would need to change on the level of production and structuring for us to best address the challenge?" It is a software change, not a workflow change.

---

### On participatory data design

**Q: Did you involve Rigshospitalet stakeholders in your analysis? Should you have done more?**

A: We had contact with the analytics team (Maja, Maia, Majken, Jeanette) who defined the problem and provided data. We did not run formal data sprints with OR schedulers, head nurses, or clinical staff. According to PDD (Jensen et al., 2021), upstream involvement — before key datafication and analysis choices are made — is where stakeholder input matters most. In retrospect, a data sprint with OR schedulers early on might have revealed the simultaneous-click behavior sooner and shaped which windows we analyzed. The iterative cycle (professional intuition ↔ data patterns) was partially present through Maja's expertise, but it was mediated rather than direct.

---

### On the lookup table vs. ML

**Q: Why recommend a lookup table when a gradient boosting model has R²=0.699 vs. R²=0.576?**

A: Three reasons, all grounded in course concepts:
1. *Organizational fit*: The hospital has no ML infrastructure. Building and maintaining a model requires resources they don't have today. A table requires none. This is data as *practice* (Xu et al., 2024) — embedding in repeatable processes.
2. *Trust and affordance*: A head nurse can verify "anesthesia cases in my specialty average 44 min" against her experience. She cannot verify "the model says 47.3 min." For adoption, the tool must *afford trust* (Winthereik's affordance framework).
3. *Marginal gain vs. adoption cost*: The lookup table already flips mean overrun from +9.5 to −19.5 min and cuts the overrun rate from 55% to 38%. The additional gain from ML is smaller than the organizational cost of implementing it. The course principle: value requires *fit* with context (Datafication lecture).

ML is positioned as a *future refinement*, not a rejection.

---

## PART 4: KEY AUTHORS AND READINGS — QUICK REFERENCE

| Author(s) | Reading | Key concept to know |
|---|---|---|
| **Mejias & Couldry (2019)** | *Datafication* | Datafication = process, "it's a verb"; social battles; production separated from external infrastructure and value generation |
| **Flyverbom & Madsen (2015)** | *Sorting data out* | 4 analytical moments: Production, Structuring, Distribution, Visualization |
| **Xu et al. (2024)** | *Time to reassess data value* | 4 roles of data: tool, commodity, practice, algorithmic intelligence |
| **Jensen et al. (2021)** | *Participatory Data Design* | PDD definition; data sprints; boundary objects; flexible visualizations |
| **Madsen (2024)** | *Digital methods as 'experimental a priori'* | How to navigate vague empirical situations; experimental approach |
| **Hoeyer & Wadmann (2020)** | *Meaningless work* | Datafication reshapes professional judgment; "good data" no longer justified by clinical outcome |
| **Milan (2024)** | *Resistance in the data-driven society* | Defensive/productive resistance; resistance degrades data quality and signals misalignment |
| **Justesen & Plesner (2024)** | *Invisible digi-work* | Invisible work: connecting, compensating, cleaning; blind angles of digital spaces |
| **Sapienza & Lehmann (2021)** | *A view from data science* | Data scientists not hypothesis-driven; learn questions from the data |
| **Micheli et al. (2020)** | *Emerging models of data governance* | 4 models: DSP, DC, PDT, PDS |
| **Mützel (2025)** | *Big Data and ML methods* | Topic modeling (LDA), word embeddings (Word2Vec), BERT, LLMs; "we are augmented social scientists" |
| **Zammuto et al. (2007)** | *IT and the changing fabric of organization* | 5 affordances of IT; organizational fabric |
| **Hasselbalch (2021)** | *Data Ethics of Power* | Power relations in Big Data society; data interest analysis (micro/meso/macro) |
| **Flyverbom & Murray (2018)** | *Datastructuring* | How data is ordered and made ready for systematic analysis |

---

## PART 5: CONNECTIONS BETWEEN YOUR POSTER AND COURSE CONCEPTS

| Poster element | Course concept | Lecture |
|---|---|---|
| 80.9% zero planned prep | Datafication: structuring choices shape what is measurable | L4 |
| 63.5% simultaneous clicks | Invisible work, resistance/subversion, datafication production failures | L2, L9 |
| Lookup table recommendation over ML | Affordance (trust), data as practice, value requires fit | L2, L3, L4 |
| Simulation = "metric fix" (overrun, not actual events) | "Numbers rarely speak for themselves"; ethical storytelling | L1, L11 |
| Data quality note on poster | Datafication: production-level change needed | L4 |
| Zero-prep → +14.9 min overrun; prep allocated → finishes early | Datafication consequences; socio-technical problem framing | L2, L4 |
| Rigshospitalet org structure (90% clinical mgmt) | Organizational fabric, power structures | L2, L7 |
| ~20,600 fewer overruns | Simulation/synthetic representation (5th affordance of IT) | L2 |
| Why the fix won't guarantee actual improvement | "Technical fixes won't save bad company performance" | L2 |
| Overrun cascades through OR day | Co-production: scheduling norms and actual OR performance co-evolve | L2 |

---

## PART 6: NUMBERS TO KNOW COLD

### The problem
| Metric | Value |
|---|---|
| Total cases | **120,868** across **32** specialties, **129** OR rooms, **2024–2025** |
| Zero planned prep | **81%** of cases |
| Mean overrun, zero-prep cases | **+14.9 min** |
| Mean overrun, 1–10 min prep allocated | **−13.9 min** (finishes early) |
| Mean overrun, 11–20 min prep allocated | **−13.5 min** (finishes early) |
| Mean overrun, 20+ min prep allocated | **−10.7 min** (finishes early) |
| Mean overrun, all cases currently | **+9.5 min** |
| % of cases currently overrunning | **55%** |

### The fix
| Metric | Value |
|---|---|
| Room prep simultaneous-click rate | **63.5%** → only 32.5% usable |
| W2 with anesthesia | **44 min** (n=75,033) |
| W2 without anesthesia | **12 min** (n=44,929) |
| Lookup table R² | **0.576** (64-cell: specialty × anesthesia) |
| ML model R² | **0.699** (gradient boosting, 6 features) |

### The impact (counterfactual simulation)
| Metric | Current | With lookup |
|---|---|---|
| Mean overrun | **+9.5 min** | **−19.5 min** |
| % overrunning | **55%** | **38%** |
| Fewer overruns | — | **~20,600** |

### Specialty examples from the heatmap (no anesthesia / with anesthesia)
| Specialty | No anesthesia | With anesthesia |
|---|---|---|
| Arthroplasty | 12 min | **80 min** |
| Ophthalmology | 8 min | 32 min |
| Breast surgery | 44 min | 65 min |
| Tumor orthopedics | 24 min | 65 min |
| Urology | 28 min | 49 min |

---

*Source for slides: Course_material/Slides/ — Lectures 1–10, Spring 2026. Source for poster analysis: poster/final/poster_analysis.md.*
