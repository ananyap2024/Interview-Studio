# AI Mock Interview Platform

An AI-powered mock interview platform that conducts personalized technical interviews based on a candidate's resume and selected technical domain.

The platform generates a structured 10-question interview consisting of 5 multiple-choice questions and 5 theoretical questions, supports voice-based interaction, evaluates theoretical answers using Gemini, and produces a final performance score with detailed feedback.

---

## Overview

The AI Mock Interview Platform is designed to provide a realistic, personalized, and cost-efficient technical interview experience.

A candidate:

1. Uploads their resume.
2. Selects a technical domain.
3. Receives 10 personalized interview questions.
4. Answers 5 MCQs and 5 theoretical questions.
5. Uses voice input/output where supported by the browser.
6. Receives an automated evaluation of their theoretical responses.
7. Gets a final score from 1–10 along with category-wise feedback.

The platform deliberately minimizes LLM usage by using AI only where it provides meaningful value and handling deterministic operations locally.

---

## Key Features

### Resume-Based Personalization

Candidates can upload a PDF or DOCX resume.

Resume text is extracted locally and analyzed to identify relevant:

- Technical skills
- Programming languages
- Frameworks
- Tools
- Projects
- Experience
- Technologies
- Domain-relevant knowledge

The extracted information is used to personalize the interview questions.

### Multiple Technical Domains

The platform currently supports:

- Cyber Security
- Python Full Stack
- Java Full Stack
- Data Analysis
- Data Science
- AI/ML Engineer

### Structured 10-Question Interview

Every interview contains exactly:

- 5 Multiple-Choice Questions
- 5 Theoretical Questions

Questions are generated based on both:

- Selected technical domain
- Candidate resume

### Voice Interaction

The interview supports browser-native voice capabilities:

- Text-to-Speech for reading questions aloud
- Speech-to-Text for capturing candidate answers

Voice processing is performed locally through browser APIs and does not require an LLM call.

### Automated Evaluation

The five theoretical answers are evaluated together in a single batched Gemini request.

The evaluation considers factors such as:

- Technical correctness
- Relevance
- Completeness
- Clarity
- Depth of understanding

### Local MCQ Evaluation

MCQs are scored locally.

The correct answers do not need to be sent to the LLM, eliminating unnecessary API usage.

### Final Performance Score

The final score is calculated locally using:

- 40% MCQ performance
- 60% theoretical-answer performance

The final score is normalized to a 1–10 scale.

### Detailed Feedback

The results provide category-level performance information and feedback to help candidates understand:

- What they performed well on
- Where they need improvement
- Which technical areas require more preparation

---

# AI Usage and Credit Optimization

One of the primary design goals of this project is to minimize Gemini API usage.

A completed interview normally requires exactly **3 logical Gemini calls**.

| Stage | Gemini Calls | Purpose |
|---|---:|---|
| Resume Analysis | 1 | Analyze candidate resume |
| Question Generation | 1 | Generate all 10 interview questions |
| Answer Evaluation | 1 | Evaluate all 5 theoretical answers |
| MCQ Scoring | 0 | Performed locally |
| Voice Input | 0 | Browser API |
| Voice Output | 0 | Browser API |
| Final Score | 0 | Local calculation |
| Navigation / UI | 0 | Local application logic |

### Why this architecture?

Instead of making an LLM request for every question or every answer, the platform batches operations wherever possible.

For example:

**Inefficient approach**

```text
Resume analysis       → 1 call
Question 1            → 1 call
Question 2            → 1 call
...
Question 10           → 1 call
Answer evaluation     → 5 calls
```

This could result in many unnecessary API requests.

**This project's approach**

```text
Resume analysis       → 1 call
All 10 questions      → 1 call
All 5 theory answers  → 1 call
```

Total:

```text
3 Gemini calls / interview
```

This significantly reduces API usage and improves response efficiency.

---

# Technology Stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- React

## Backend

- Python
- FastAPI
- Pydantic
- Pydantic Settings
- HTTPX

## AI

- Google Gemini API
- Gemini `gemini-3.5-flash-lite`
- Structured JSON/Pydantic responses

## Resume Processing

- PyMuPDF for PDF extraction
- python-docx for DOCX extraction
- python-multipart for file uploads

## Voice

Browser-native Web Speech APIs:

- Speech Recognition / Speech-to-Text
- Speech Synthesis / Text-to-Speech

## Testing

- Pytest
- HTTPX
- Mocked Gemini provider tests
- Frontend TypeScript/build validation

---

# System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    │                     │
                    │ Resume + Domain     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Next.js UI       │
                    │ TypeScript + React   │
                    └──────────┬──────────┘
                               │
                               │ HTTP
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI         │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │   Resume    │ │ Interview   │ │   Scoring   │
        │   Parser    │ │   Service   │ │   Service   │
        └─────────────┘ └──────┬──────┘ └─────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │   Gemini API     │
                     │  3 calls max     │
                     └──────────────────┘
```

---

# Interview Workflow

## Step 1 — Resume Upload

The candidate uploads a:

- `.pdf`
- `.docx`

The backend validates:

- File type
- File size
- Extracted content

The resume is processed locally.

The application does not permanently store the uploaded resume as part of the current interview flow.

---

## Step 2 — Domain Selection

The candidate selects one of the supported domains:

```text
Cyber Security
Python Full Stack
Java Full Stack
Data Analysis
Data Science
AI/ML Engineer
```

Domain selection is completely deterministic and does not require Gemini.

---

## Step 3 — Resume Analysis

The extracted resume content is sent to Gemini.

Gemini identifies relevant candidate information that can be used for interview personalization.

This is the first logical AI call.

---

## Step 4 — Question Generation

The system sends the selected domain and resume context to Gemini.

Gemini generates exactly:

```text
5 MCQs
+
5 theoretical questions
=
10 questions
```

The response is validated against the application's Pydantic schema before being used by the frontend.

This is the second logical AI call.

---

## Step 5 — Interview

The candidate proceeds through the generated questions.

For theoretical questions, the candidate can type an answer or use browser voice input.

Questions can also be read aloud using browser-native text-to-speech.

No Gemini request is required for these interactions.

---

## Step 6 — MCQ Evaluation

MCQ answers are evaluated locally.

For each MCQ:

```text
candidate answer == correct answer
```

The result is calculated immediately without an LLM call.

---

## Step 7 — Theoretical Answer Evaluation

After the candidate completes the interview, all five theoretical answers are sent together to Gemini.

Gemini evaluates the responses and returns structured evaluation data.

This is the third and final logical Gemini call.

---

## Step 8 — Final Score

The backend combines:

- MCQ score
- Theoretical evaluation score

The final score is calculated locally.

Current weighting:

```text
MCQ          = 40%
Theory       = 60%
```

The resulting performance is represented on a 1–10 scale.

---

# API Overview

The backend exposes API endpoints for the main interview workflow.

### Health Check

```http
GET /health
```

Used to verify that the backend is running.

Example:

```json
{
  "status": "ok"
}
```

### Domain List

```http
GET /api/domains
```

Returns the supported interview domains.

### Resume Upload

```http
POST /api/resume/upload
```

Accepts PDF/DOCX resume uploads and extracts their text locally.

### Interview Workflow

The backend also provides endpoints for:

- Creating an interview
- Loading interview state
- Retrieving generated questions
- Saving answers
- Submitting an interview
- Retrieving evaluation results

The exact route definitions are maintained in the FastAPI router implementation.

---

# Project Structure

The project follows a frontend/backend separation.

```text
ai-mock-interview/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── .env
├── .env.example
├── .gitignore
├── README.md
└── ...
```

> The exact file structure may evolve as additional production features are added.

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash-lite
```

Never commit the actual `.env` file or API key to Git.

The repository should contain only a placeholder configuration in `.env.example`.

Example:

```env
GEMINI_API_KEY=
LLM_MODEL=gemini-3.5-flash-lite
```

---

# Installation

## Prerequisites

Make sure the following are installed:

- Python 3.13+
- Node.js
- npm
- Git

---

# Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# Frontend Setup

Open another terminal and navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

---

# Running the Application

## Start Backend

From the project root:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Start Frontend

In another terminal:

```bash
cd frontend
npm run dev
```

The frontend will normally be available at:

```text
http://127.0.0.1:3000
```

---

# Testing

The backend includes automated tests for the core application workflow.

Run the test suite:

```bash
pytest -v
```

---

# Deploying to Vercel

The root `vercel.json` configures this repository as a Vercel Services deployment:

- `frontend/` is the Next.js service and receives `/` and non-API routes.
- `backend/` is the FastAPI service and receives `/api/*` without changing the
  request path.

In the Vercel project settings, select **Services** as the framework. Vercel
Services are currently in beta. Deploy the repository root so Vercel can read
the root `vercel.json` and build both services.

The browser calls relative `/api/...` paths in production, so both services use
the same deployment origin and no production backend URL or service binding is
needed. During local development, the frontend defaults to `http://localhost:8000`;
`NEXT_PUBLIC_API_URL` can optionally override that local API base.

Set `GEMINI_API_KEY` as a secret environment variable on the **backend service
only**. Never create a `NEXT_PUBLIC_GEMINI_API_KEY` variable or put the Gemini
key in any frontend environment variable. `LLM_MODEL` is optional; the backend
defaults to `gemini-3.5-flash-lite`. `FRONTEND_ORIGINS` is optional for this
same-origin deployment; the existing CORS middleware is retained for local
development and any separately hosted frontend. `SUPABASE_DB_URL` is currently
unused by the application.

## Deployment state limitation

Interview records and per-interview locks currently live in backend process
memory. Vercel Functions may restart or handle requests in different instances,
so an in-progress interview is not guaranteed to be available to a later
request. Treat this deployment as suitable for evaluation or demos only until
interview state is moved to a shared persistent store. This deployment setup
does not change the current state architecture.

The Gemini-dependent workflow is tested using mocked provider responses so that normal development and CI testing do not consume Gemini API credits.

The project also validates:

- Backend health
- Domain configuration
- Resume upload
- Resume extraction
- Interview workflow
- Structured AI responses
- MCQ scoring
- Theoretical evaluation
- Final scoring
- Error handling

---

# Gemini Integration

The application communicates with Gemini through the backend.

The frontend never receives the Gemini API key.

The API key is loaded server-side through environment configuration.

The backend uses structured responses so that AI-generated content is validated before being passed into the interview workflow.

A successful controlled integration test confirmed:

```text
Model:              gemini-3.5-flash-lite
HTTP Status:        200
Structured Output:  true
API Calls:          1
```

The test used a single minimal generation request rather than executing a complete interview.

---

# Error Handling

The application is designed to avoid exposing provider errors or sensitive configuration to users.

The backend handles cases including:

- Invalid resume files
- Unsupported file types
- Oversized uploads
- Missing configuration
- Gemini API failures
- Invalid structured responses
- Network errors
- Timeouts
- Invalid interview state

AI responses are validated before being accepted by the application.

---

# Security

Security considerations include:

- Gemini API key stored only in environment variables
- API key excluded from Git
- No frontend exposure of Gemini credentials
- Resume upload validation
- File-size restrictions
- Server-side AI communication
- Structured response validation
- Safe error responses

The `.env` file must never be committed.

---

# Cost-Efficient AI Design

The platform intentionally follows a deterministic-first architecture.

### AI is used for:

- Resume understanding
- Personalized question generation
- Theoretical answer evaluation

### AI is NOT used for:

- Domain selection
- MCQ scoring
- Final numerical score calculation
- Interview navigation
- Timers
- Voice input
- Voice output
- Basic validation

This keeps the application both faster and significantly more economical than an architecture that sends every interaction to an LLM.

---

# Design Principles

The project follows several core principles.

### 1. AI Where It Adds Value

Use an LLM for semantic tasks rather than deterministic operations.

### 2. Batch LLM Operations

Generate all interview questions together and evaluate all theoretical answers together.

### 3. Validate AI Output

AI-generated data is validated using typed schemas before entering the application workflow.

### 4. Keep Secrets Server-Side

The Gemini API key never belongs in frontend code.

### 5. Local Processing Where Possible

Resume extraction, voice processing, MCQ scoring, and final scoring are handled without additional AI calls.

### 6. Modular Architecture

Frontend, backend, AI provider, resume processing, interview logic, and scoring are separated into manageable components.

---

# Current Limitations

The current implementation has some limitations that should be considered before production deployment.

### Interview State

The current interview state is maintained in backend memory.

This means state can be lost if the FastAPI process is restarted.

A production deployment should move interview persistence to a database such as PostgreSQL/Supabase.

### Browser Voice Support

Voice recognition depends on browser support for the Web Speech API.

Availability and behavior can vary between browsers and operating systems.

### AI Evaluation

The theoretical evaluation is generated by an LLM and therefore should be treated as automated assistance rather than an authoritative human assessment.

### Production Deployment

Additional production hardening may be required for:

- Authentication
- Persistent database storage
- Rate limiting
- Production logging
- Monitoring
- File storage policies
- User/session management
- Deployment infrastructure

---

# Future Improvements

Potential future enhancements include:

- User authentication
- Persistent interview history
- PostgreSQL/Supabase integration
- Candidate dashboards
- Interview history and progress tracking
- Difficulty selection
- Adaptive questioning
- Job-description-based interviews
- Recruiter dashboard
- Interview analytics
- Skill-gap analysis
- Improved evaluation rubrics
- Multi-language voice support
- Production-grade observability
- Rate limiting and abuse prevention

---

# Development Status

Current implementation status:

| Component | Status |
|---|---|
| Next.js frontend | Complete |
| FastAPI backend | Complete |
| Domain selection | Complete |
| Resume upload | Complete |
| Local PDF/DOCX extraction | Complete |
| Resume analysis | Complete |
| 10-question generation | Complete |
| 5 MCQs + 5 theory | Complete |
| Voice input | Complete |
| Voice output | Complete |
| Local MCQ scoring | Complete |
| AI theory evaluation | Complete |
| Local final scoring | Complete |
| Structured Gemini responses | Verified |
| Gemini connection | Verified |
| Automated tests | Passing |
| Production persistence | Future enhancement |
| Phase 12 hardening/deployment | Pending |

---

# Example Interview Flow

```text
                    START
                      │
                      ▼
               Upload Resume
                      │
                      ▼
              Extract Resume Text
                      │
                      ▼
             Select Interview Domain
                      │
                      ▼
              Gemini: Analyze Resume
                      │
                      ▼
          Gemini: Generate 10 Questions
                      │
                      ▼
             ┌───────────────────┐
             │   5 MCQs +        │
             │   5 Theory        │
             └─────────┬─────────┘
                       │
                       ▼
                Conduct Interview
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
          MCQ Answers      Theory Answers
              │                 │
              ▼                 ▼
        Local Scoring      Gemini Evaluation
              │                 │
              └────────┬────────┘
                       ▼
                Final Score 1–10
                       │
                       ▼
               Detailed Feedback
                       │
                       ▼
                      END
```

---

# Why This Project?

Traditional mock interview platforms often provide generic questions or rely heavily on fixed question banks.

This platform combines:

```text
Candidate Resume
       +
Technical Domain
       +
Generative AI
       +
Voice Interaction
       +
Automated Evaluation
       +
Cost-Efficient Architecture
```

to create a personalized technical interview experience while deliberately minimizing unnecessary LLM usage.

---

# Conclusion

The AI Mock Interview Platform demonstrates how generative AI can be integrated into a practical full-stack application without making every application operation dependent on an LLM.

The architecture focuses on:

- Personalization
- Structured AI outputs
- Low API usage
- Deterministic local processing
- Voice interaction
- Modular backend services
- Automated testing
- Secure API-key handling

The result is a foundation for a scalable AI-assisted interview platform that can be extended with persistent user accounts, analytics, adaptive interviews, recruiter workflows, and production infrastructure.

---

## License

Add the appropriate license for your repository, such as MIT, if you intend to make the project open source.

---

## Author

Built as an AI/ML full-stack project demonstrating:

- Generative AI integration
- Full-stack development
- FastAPI backend development
- Next.js frontend development
- Structured LLM outputs
- Voice interfaces
- API optimization
- Automated testing
- AI-assisted evaluation