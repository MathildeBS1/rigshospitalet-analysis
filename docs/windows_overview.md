# OR Timeline — Analysis Windows

## Full OR Timeline (chronological)

```mermaid
graph LR
    subgraph PLANNED["PLANNED TIMESTAMPS"]
        P1["Planlagt stue<br/>klargøring start"]
        P2["Patient på stuen<br/>(Planlagt)"]
        P3["Patient forlader<br/>stuen (Planlagt)"]
    end

    subgraph ACTUAL["ACTUAL TIMESTAMPS"]
        A1["Stue klargøring<br/>start"]
        A2["Stue klargjort"]
        A3["Patient på stuen"]
        A4["Anæstesistart"]
        A5["Anæstesi<br/>melder klar"]
        A6["Procedure start"]
        A7["Procedure slut"]
        A8["Patient klar<br/>til afgang"]
        A9["Patient forlader<br/>stuen"]
        A10["Stue rengøring<br/>start"]
        A11["Stue rengjort"]
    end

    P1 --> A1 --> A2 --> A3
    P2 -.-> A3
    A3 --> A4 --> A5 --> A6 --> A7 --> A8 --> A9
    P3 -.-> A9
    A9 --> A10 --> A11
```

## The Windows

```mermaid
graph TB
    subgraph TIMELINE["OR TIMELINE (left to right = chronological)"]
        direction LR
        T1["Planlagt stue<br/>klargøring start<br/><i>99.7%</i>"]
        T2["Patient på stuen<br/>(Planlagt)<br/><i>99.7%</i>"]
        T3["Patient på stuen<br/>(Actual)<br/><i>99.6%</i>"]
        T4["Procedure start<br/><i>99.4%</i>"]
        T5["Procedure slut<br/><i>99.4%</i>"]
        T6["Patient forlader<br/>stuen<br/><i>99.6%</i>"]

        T1 --> T2 --> T3 --> T4 --> T5 --> T6
    end

    subgraph W1["W1: PLANNED PREP ALLOCATION"]
        direction LR
        W1a["Planlagt stue klargøring start"]
        W1b["Patient på stuen (Planlagt)"]
        W1a -->|"planned_prep_min"| W1b
    end

    subgraph W1D["W1b: START DELAY"]
        direction LR
        W1Da["Patient på stuen (Planlagt)"]
        W1Db["Patient på stuen (Actual)"]
        W1Da -->|"start_delay_min"| W1Db
    end

    subgraph W2["W2: PATIENT-SIDE PREP"]
        direction LR
        W2a["Patient på stuen (Actual)"]
        W2b["Procedure start"]
        W2a -->|"patient_prep_min"| W2b
    end

    subgraph MATH["MATHILDE'S WINDOW (DROPPED)"]
        direction LR
        Ma["Stue klargøring start"]
        Mb["Patient på stuen (Actual)"]
        Ma -->|"room_prep_min"| Mb
    end

    subgraph CLEAN["CLEANING (DROPPED)"]
        direction LR
        Ca["Stue rengøring start"]
        Cb["Stue rengjort"]
        Ca -->|"cleaning_min"| Cb
    end

    style W1 fill:#d4edda,stroke:#28a745,stroke-width:2px
    style W1D fill:#d4edda,stroke:#28a745,stroke-width:2px
    style W2 fill:#d4edda,stroke:#28a745,stroke-width:2px
    style MATH fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style CLEAN fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

## Window Comparison

```mermaid
graph TB
    subgraph GOOD["USABLE WINDOWS (green)"]
        direction TB

        subgraph W1_BOX["W1: PLANNED PREP ALLOCATION"]
            W1_DEF["Planlagt stue klargøring start → Patient på stuen (Planlagt)<br/><b>Both planned timestamps — what the schedule allocates for prep</b>"]
        end
        W1_COV["Coverage: 99.7%<br/>120,474 cases"]
        W1_FIND["80.9% get 0 min<br/>Mean: 3.1 min<br/>Median: 0 min"]
        W1_STR["No data quality issues<br/>Both from scheduling system<br/>Full population"]
        W1_BOX --> W1_COV --> W1_FIND --> W1_STR

        subgraph W1B_BOX["W1b: START DELAY"]
            W1B_DEF["Patient på stuen (Planlagt) → Patient på stuen (Actual)<br/><b>How late the patient actually enters OR vs plan</b>"]
        end
        W1B_COV["Coverage: 99.5%<br/>120,237 cases"]
        W1B_FIND["Zero-prep: +26.7 min late, 81.5% late<br/>20+ min prep: -8.9 min EARLY<br/>= Hospital's own Forsinkelse (corr=1.0)"]
        W1B_STR["Identical to hospital's delay metric<br/>Not an invented measure<br/>Monotonic relationship with W1"]
        W1B_BOX --> W1B_COV --> W1B_FIND --> W1B_STR

        subgraph W2_BOX["W2: PATIENT-SIDE PREP"]
            W2_DEF["Patient på stuen (Actual) → Procedure start<br/><b>What prep actually costs once patient is in OR</b>"]
        end
        W2_COV["Coverage: 99.3%<br/>120,043 cases"]
        W2_FIND["Mean: 32 min | Median: 27 min<br/>With anesthesia: 44 min<br/>Without anesthesia: 11 min"]
        W2_STR["Shows what schedule SHOULD allocate<br/>Anesthesia known before surgery<br/>Directly actionable"]
        W2_BOX --> W2_COV --> W2_FIND --> W2_STR
    end

    subgraph BAD["DROPPED WINDOWS (red)"]
        direction TB

        subgraph M_BOX["MATHILDE: ROOM PREP"]
            M_DEF["Stue klargøring start → Patient på stuen (Actual)<br/><b>Time from room prep start to patient arrival</b>"]
        end
        M_COV["Coverage: 90.0%<br/>108,732 cases"]
        M_PROB["63.5% have prep_start == prep_done<br/>(simultaneous click)<br/>Clean subset: only 32.6% of data"]
        M_BIAS["Bias: clean subset has 79.2% anesthesia<br/>vs 62.4% in full population<br/>Not representative"]
        M_BOX --> M_COV --> M_PROB --> M_BIAS

        subgraph C_BOX["CLEANING"]
            C_DEF["Stue rengøring start → Stue rengjort<br/><b>Room cleaning duration between cases</b>"]
        end
        C_COV["Coverage: 41.5%<br/>50,160 cases"]
        C_PROB["79.7% have start == done<br/>(simultaneous click)<br/>Median duration: 0 min"]
        C_BIAS["Even worse quality than room prep<br/>Less than half of cases<br/>Unreliable for any analysis"]
        C_BOX --> C_COV --> C_PROB --> C_BIAS
    end

    style GOOD fill:#f0fff0,stroke:#28a745,stroke-width:3px
    style BAD fill:#fff5f5,stroke:#dc3545,stroke-width:3px
    style W1_BOX fill:#d4edda,stroke:#28a745
    style W1B_BOX fill:#d4edda,stroke:#28a745
    style W2_BOX fill:#d4edda,stroke:#28a745
    style M_BOX fill:#f8d7da,stroke:#dc3545
    style C_BOX fill:#f8d7da,stroke:#dc3545
```

## How the Three Good Windows Tell the Story

```mermaid
flowchart TD
    ROOT["THE QUESTION:<br/><b>Why do surgeries start late?</b>"]

    ROOT --> W1
    W1["W1: PLANNED PREP<br/><b>80.9% of cases get 0 min prep allocation</b><br/>The schedule pretends prep doesn't exist"]

    W1 --> W1B
    W1B["W1b: START DELAY<br/><b>Zero-prep cases start +26.7 min late (81.5%)</b><br/>With 20+ min prep → starts 8.9 min EARLY<br/><i>= Hospital's own Forsinkelse metric</i>"]

    W1B --> CASCADE
    CASCADE["DELAY AMPLIFIES<br/>Start delay +26.7 → Overrun +30.7<br/><b>The delay doesn't get absorbed, it grows</b>"]

    ROOT --> W2
    W2["W2: PATIENT-SIDE PREP<br/><b>Actual prep takes mean 32 min</b><br/>With anesthesia: 44 min<br/>Without: 11 min"]

    W2 --> FIX
    CASCADE --> FIX
    FIX["THE FIX:<br/><b>Allocate prep time based on known features</b><br/>Anesthesia (yes/no) is known before surgery<br/>A simple lookup table closes most of the gap"]

    ACUTE["IMPORTANT:<br/>84% of PLANNED cases get zero prep<br/><b>Not an acute-case artifact</b>"]
    W1 --> ACUTE

    style ROOT fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style W1 fill:#d4edda,stroke:#28a745,stroke-width:2px
    style W1B fill:#d4edda,stroke:#28a745,stroke-width:2px
    style W2 fill:#d4edda,stroke:#28a745,stroke-width:2px
    style CASCADE fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style FIX fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px
    style ACUTE fill:#fff3cd,stroke:#ffc107,stroke-width:2px
```

## Quick Reference

| Window | Formula | Coverage | Quality | Role |
|--------|---------|----------|---------|------|
| **W1** | `Patient på stuen (Planlagt)` - `Planlagt stue klargøring start` | 99.7% | Clean | Root cause: schedule allocates no prep |
| **W1b** | `Patient på stuen` - `Patient på stuen (Planlagt)` | 99.5% | Clean, = Forsinkelse | Consequence: cases start late |
| **W2** | `Procedure start` - `Patient på stuen` | 99.3% | Clean | What prep actually costs |
| ~~Mathilde~~ | `Stue klargøring start` → `Patient på stuen` | 90.0% | 63.5% simultaneous click | Dropped — biased subset |
| ~~Cleaning~~ | `Stue rengøring start` → `Stue rengjort` | 41.5% | 79.7% simultaneous click | Dropped — unusable |
