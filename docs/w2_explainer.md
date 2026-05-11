# W2 Explainer — What It Measures, Why It Matters, How To Use It

## What W2 measures

```mermaid
graph LR
    subgraph OR_ROOM["INSIDE THE OPERATING ROOM"]
        direction LR
        A["Patient enters OR"]
        B["Anesthesia<br/>induction"]
        C["Positioning<br/>& draping"]
        D["Equipment<br/>check & timeout"]
        E["Surgeon<br/>starts procedure"]

        A --> B --> C --> D --> E
    end

    style OR_ROOM fill:#e8f4fd,stroke:#1565c0,stroke-width:2px
    style A fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style E fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style B fill:#fff3cd,stroke:#ffc107
    style C fill:#fff3cd,stroke:#ffc107
    style D fill:#fff3cd,stroke:#ffc107
```

```
W2 = ts_procedure_start − ts_patient_in_or

Mean: 32 min  |  With anesthesia: 44 min  |  Without: 11 min
Coverage: 99.3%  |  Data quality issues: none
```

---

## The scheduling problem W2 exposes

```mermaid
flowchart TD
    subgraph SCHEDULE["WHAT THE SCHEDULE SAYS"]
        direction LR
        S1["Room prep start<br/>08:00"]
        S2["Patient enters<br/>08:00"]
        S3["Patient leaves<br/>10:00"]
        S1 -->|"0 min prep<br/>(81% of cases)"| S2
        S2 -->|"2 hours OR time"| S3
    end

    subgraph REALITY["WHAT ACTUALLY HAPPENS"]
        direction LR
        R1["Room prep start<br/>07:52"]
        R2["Room ready<br/>08:10"]
        R3["Patient enters<br/>08:28"]
        R4["Setup complete<br/>09:00"]
        R5["Procedure<br/>09:00–10:15"]
        R1 -->|"staff start early"| R2
        R2 -->|"patient arrives<br/>once room ready"| R3
        R3 -->|"W2: 32 min setup<br/>before surgery"| R4
        R4 --> R5
    end

    SCHEDULE --> GAP
    REALITY --> GAP
    GAP["START DELAY: +28 min<br/>The schedule promised 08:00<br/>The patient entered at 08:28"]

    style SCHEDULE fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#000
    style REALITY fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style GAP fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#000
```

---

## W2 vs Mathilde's room prep window

```mermaid
flowchart LR
    subgraph TIMELINE["OR TIMELINE"]
        direction LR
        T1["Staff start<br/>prepping room"]
        T2["Room ready"]
        T3["Patient<br/>enters OR"]
        T4["Procedure<br/>starts"]
        T5["Procedure<br/>ends"]
        T1 --> T2 --> T3 --> T4 --> T5
    end

    subgraph MATHILDE["MATHILDE'S WINDOW"]
        direction TB
        M1["Room prep start → Patient enters"]
        M2["❌ 63.5% bad timestamps"]
        M3["❌ Only 32% of data usable"]
        M4["❌ R² = 0.02 lookup / 0.18 ML"]
        M5["❌ r = 0.013 with start delay"]
        M1 --- M2 --- M3 --- M4 --- M5
    end

    subgraph W2BOX["OUR WINDOW (W2)"]
        direction TB
        W1["Patient enters → Procedure starts"]
        W2["✓ 99.3% coverage, clean data"]
        W3["✓ Predictable: R² = 0.58 lookup"]
        W4["✓ Only needs specialty + anesthesia"]
        W5["✓ Directly fixable in schedule"]
        W1 --- W2 --- W3 --- W4 --- W5
    end

    T1 -.->|"measures<br/>this"| MATHILDE
    T3 -.->|"measures<br/>this"| W2BOX

    style MATHILDE fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#000
    style W2BOX fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style TIMELINE fill:#f0f0f0,stroke:#666,stroke-width:1px,color:#000
```

---

## From analysis to action

```mermaid
flowchart TD
    DIAGNOSE["<b>1. DIAGNOSE</b><br/>81% of cases get 0 min<br/>planned prep time"]
    
    MEASURE["<b>2. MEASURE THE COST</b><br/>Zero-prep cases start +28 min late<br/>82.8% start late"]

    PREDICT["<b>3. PREDICT WHAT'S NEEDED</b><br/>W2 tells us in-room setup time<br/>Mean 32 min (44 with anesthesia, 11 without)"]

    LOOKUP["<b>4. BUILD THE FIX</b><br/>64-cell lookup table<br/>Specialty × Anesthesia<br/>R² = 0.575"]

    RESULT["<b>5. SIMULATED RESULT</b><br/>Mean delay: +21 min → ~0 min<br/>Late starts: 73% → 46%<br/>33,000 fewer late starts/year"]

    DIAGNOSE --> MEASURE --> PREDICT --> LOOKUP --> RESULT

    NOTE["Same cases. Same rooms. Same staff.<br/>The schedule just allocates realistic time."]
    RESULT --> NOTE

    style DIAGNOSE fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    style MEASURE fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#000
    style PREDICT fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style LOOKUP fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style RESULT fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px,color:#000
    style NOTE fill:#f0f0f0,stroke:#666,stroke-width:1px,color:#000
```

---

## Why W2 is predictable and room prep is not

```mermaid
flowchart LR
    subgraph KNOWN["KNOWN BEFORE SURGERY DAY"]
        K1["Specialty"]
        K2["Anesthesia yes/no"]
    end

    subgraph W2PRED["W2: IN-ROOM SETUP"]
        direction TB
        W2a["Determined by:<br/>case complexity,<br/>anesthesia type,<br/>specialty protocols"]
        W2b["R² = 0.575 with just<br/>specialty + anesthesia"]
    end

    subgraph RPRED["ROOM PREP"]
        direction TB
        Ra["Determined by:<br/>which nurse,<br/>prior case leftovers,<br/>supply availability"]
        Rb["R² = 0.02 with<br/>all available features"]
    end

    KNOWN -->|"predicts well"| W2PRED
    KNOWN -->|"cannot predict"| RPRED

    style KNOWN fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    style W2PRED fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#000
    style RPRED fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#000
```
