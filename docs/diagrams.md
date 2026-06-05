# NeuraCore — Architecture & UML

> All diagrams are [Mermaid](https://mermaid.js.org). They render automatically
> on GitHub, in VS Code (Markdown Preview Mermaid extension), or at
> <https://mermaid.live>.

---

## 1 · System flow — *the pipeline that speaks for itself*

```mermaid
flowchart TD
    subgraph Client["🖥️  Client (React PWA)"]
      EDU["Educator: upload / review / analytics"]
      STU["Student: quiz · learn · signals"]
    end

    subgraph API["⚙️  FastAPI Core API"]
      AUTH["/auth  · JWT"]
      DOC["/documents"]
      PROF["/profiles  · quiz → weights"]
      TR["/transforms  · request / review / deliver"]
      SES["/sessions  · append-only events"]
      AN["/analytics"]
    end

    subgraph Work["🧵  Task runner (inline threads or Celery)"]
      ING["Ingestion: parse → atomise → tag"]
      TRW["Transform: format-select → LLM/local → validate"]
      ADP["Adapt: weekly recalibration"]
    end

    subgraph Data["🗄️  Data"]
      DB[("PostgreSQL / SQLite")]
      FS[("File store (S3-shaped)")]
    end

    EDU -->|"PDF/DOCX/PPTX/TXT"| DOC --> FS
    DOC --> ING --> DB
    STU -->|"onboarding quiz"| PROF --> DB
    STU -->|"request"| TR --> TRW --> DB
    TRW -->|"pending"| RQ{{"Educator review queue"}}
    EDU -->|"approve / reject"| RQ --> DB
    STU -->|"fetch approved"| TR
    STU -->|"atom_start / complete / skip / exit"| SES --> DB
    DB --> ADP -->|"nudge weights + snapshot"| DB
    EDU -->|"engagement"| AN --> DB

    classDef c fill:#eef0ff,stroke:#5b4bdb,color:#1d2030;
    class EDU,STU,AUTH,DOC,PROF,TR,SES,AN,ING,TRW,ADP c;
```

---

## 2 · Sequence (UML) — upload → adaptive delivery

```mermaid
sequenceDiagram
    autonumber
    actor T as Teacher
    actor S as Student
    participant API as FastAPI
    participant W as Worker
    participant LLM as Transform engine
    participant DB as Database

    T->>API: POST /documents (file)
    API->>DB: SourceDocument(parse_status=pending)
    API-->>T: 202 { document_id, task_id }
    API->>W: run_ingestion(document_id)
    W->>W: parse → atomise → classify (Bloom/subject/grade)
    W->>DB: insert CurriculumAtoms, status=complete

    S->>API: POST /profiles/{id}/quiz
    API->>DB: CognitiveProfile(weights)

    S->>API: POST /transforms { document_id }
    API->>W: run_transform(document_id, student_id)
    loop each atom
        W->>LLM: select_output_format(weights) + render prompt
        LLM-->>W: transformed_text
        W->>LLM: validate_transform_output()
        alt fails
            LLM->>LLM: strict retry / local fallback
        end
        W->>DB: TransformedAtom(review_status=pending)
    end

    T->>API: POST /transforms/{id}/review (approve)
    API->>DB: review_status=approved

    S->>API: GET /transforms?document_id (approved only)
    API-->>S: personalised atoms
    S->>API: POST /sessions/{id}/events (signals)
    API->>DB: append SessionEvent

    Note over W,DB: Weekly Beat job
    W->>DB: recalibrate_profile() → snapshot + new weights
```

---

## 3 · Domain model (UML class diagram)

```mermaid
classDiagram
    class Institution {
      +id: UUID
      +name: str
      +lms_type: enum
      +auto_approve_transforms: bool
    }
    class User {
      +id: UUID
      +email: str
      +role: educator|student|admin
      +parental_consent: bool
    }
    class SourceDocument {
      +id: UUID
      +file_type: pdf|docx|pptx|txt
      +parse_status: enum
      +page_count: int
    }
    class CurriculumAtom {
      +id: UUID
      +sequence_index: int
      +raw_text: str
      +subject: str
      +bloom_level: enum
      +estimated_reading_minutes: float
    }
    class CognitiveProfile {
      +adhd_weight: float
      +dyslexia_weight: float
      +asd_weight: float
      +profile_version: int
      +calibration_source: enum
    }
    class CognitiveProfileSnapshot {
      +profile_version: int
      +snapshot_reason: str
    }
    class TransformedAtom {
      +output_format: enum
      +transformed_text: str
      +audio_script: str
      +review_status: enum
      +llm_model: str
      +prompt_version: str
    }
    class LearningSession {
      +started_at: datetime
      +atoms_completed: int
    }
    class SessionEvent {
      +event_type: enum
      +time_on_atom_ms: int
      +retry_count: int
    }

    Institution "1" o-- "many" User
    Institution "1" o-- "many" SourceDocument
    User "1" --> "0..1" CognitiveProfile : student
    CognitiveProfile "1" o-- "many" CognitiveProfileSnapshot
    SourceDocument "1" *-- "many" CurriculumAtom
    CurriculumAtom "1" --> "many" TransformedAtom
    User "1" --> "many" TransformedAtom : student
    User "1" --> "many" LearningSession
    LearningSession "1" *-- "many" SessionEvent
    CurriculumAtom "1" --> "many" SessionEvent
    TransformedAtom "1" --> "many" SessionEvent
```

---

## 4 · Format selection (decision logic)

```mermaid
flowchart TD
    A["Profile weights (ADHD, Dyslexia, ASD)"] --> B{"dominant &lt; 0.20 ?"}
    B -- yes --> D["asd_structured<br/>(safe, low-stimulation default)"]
    B -- no --> C{"dominant − second ≤ 0.15 ?"}
    C -- yes --> E["blended<br/>(merge top two supports)"]
    C -- no --> F{"which trait is dominant?"}
    F -- ADHD --> G["adhd_gamified"]
    F -- Dyslexia --> H["dyslexia_audio"]
    F -- ASD --> I["asd_structured"]
```

---

## 5 · Profile lifecycle (UML state diagram)

```mermaid
stateDiagram-v2
    [*] --> Unset
    Unset --> Onboarding : student takes quiz
    Onboarding --> Active : weights computed
    Active --> EducatorOverride : teacher adjusts (snapshot saved)
    EducatorOverride --> Active
    Active --> Recalibrating : weekly job, ≥10 signals
    Recalibrating --> Active : Δ ≥ 0.02 → snapshot + version++
    Recalibrating --> Active : Δ &lt; 0.02 → no change
    Active --> [*] : right-to-erasure (cascade delete)
```

---

## 6 · Accessibility transform matrix (what each profile receives)

```mermaid
flowchart LR
    SRC["Curriculum atom<br/>(raw text)"] --> R{Profile}
    R -->|ADHD| A["⚡ Gamified<br/>• 3–5 min micro-segments<br/>• one explicit goal<br/>• visual anchor first<br/>• progress bar + token<br/>• micro-poll<br/>• Pomodoro / focus mode / sticky pad"]
    R -->|Dyslexia| D["🔤 Audio-first<br/>• OpenDyslexic font<br/>• colour-coded syllables<br/>• highlighted key words<br/>• chunked + numbered<br/>• word-by-word TTS"]
    R -->|ASD| S["🧩 Structured<br/>• numbered visual schedule<br/>• identical template every time<br/>• idioms rewritten literally<br/>• no autoplay / no surprises<br/>• rubric shown first<br/>• real-world example button"]
    R -->|Blended| B["🌈 Mixed<br/>gamified structure +<br/>structured predictability"]
```
