AI Mock Interview Platform
An AI-powered mock interview platform that creates personalized technical interviews from a candidate's resume and selected technical domain.
The platform analyzes the uploaded resume, generates exactly 10 interview questions, supports both voice input and voice output, evaluates theoretical answers using Gemini, scores MCQs locally, and produces a detailed interview assessment.
Live Demo
Production deployment: YOUR_VERCEL_URL
Replace YOUR_VERCEL_URL with the actual Vercel production URL.
Features
- Resume upload with local text extraction
- Resume-aware interview personalization
- Six technical domains:
  - Cyber Security
  - Python Full Stack
  - Java Full Stack
  - Data Analysis
  - Data Science
  - AI/ML Engineer
- Exactly 10 questions per interview:
  - 5 Multiple Choice Questions (MCQs)
  - 5 Theoretical questions
- Question difficulty variation
- Browser-based voice input using Web Speech API
- Browser-based question read-aloud using SpeechSynthesis
- Local MCQ scoring
- AI evaluation of theoretical answers
- Overall score from 1–10
- Category-wise assessment
- Strengths and weaknesses
- Recommended topics for improvement
- Detailed feedback for theoretical answers
- Safe error handling and retry control
- No permanent resume-file storage
- Production deployment using Vercel Services
Interview Workflow
Select Domain
      ↓
Upload Resume
      ↓
Local Resume Parsing
      ↓
Gemini Resume Analysis
      ↓
Generate 10 Personalized Questions
      ↓
Answer 5 MCQs + 5 Theoretical Questions
      ↓
MCQs Scored Locally
      ↓
5 Theoretical Answers Evaluated in One Batched Gemini Call
      ↓
Final Score + Category Scores + Feedback
AI Usage and Credit Optimization
The application was intentionally designed to minimize Gemini usage.
For one normally completed interview, there are exactly 3 logical Gemini stages:
1. Resume analysis
2. Generation of all 10 questions
3. Batched evaluation of all 5 theoretical answers
MCQ evaluation does not use Gemini.
Voice input and voice output use browser-native APIs and do not use Gemini.
Final score calculation is performed locally.
Automated tests mock Gemini calls and do not consume Gemini API credits.
Retry policy
Each AI stage allows at most one additional provider attempt when required.
The application also prevents duplicate interview submission from the frontend.
Technology Stack
Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- Web Speech API
- SpeechSynthesis API
Backend
- FastAPI
- Python
- Pydantic
- HTTPX
- PyMuPDF
- python-docx
AI
- Google Gemini API
- Default model: gemini-3.5-flash-lite
- Structured JSON/Pydantic-based responses
Deployment
- Vercel Services
- GitHub
- Next.js frontend service
- FastAPI backend service
Project Structure
Interview-Studio/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── schemas/
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── vercel.json
├── .env.example
├── .gitignore
└── README.md
Prerequisites
- Python 3.10+
- Node.js 18+
- npm
- Git
- Gemini API key
Local Development
1. Clone the repository
git clone https://github.com/ananyap2024/Interview-Studio.git
cd Interview-Studio
2. Backend setup
Create a virtual environment:
Windows
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
macOS/Linux
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
3. Configure environment variables
Create a .env file in the repository root:
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash-lite
Optional:
FRONTEND_ORIGINS=http://localhost:3000
SUPABASE_DB_URL=
SUPABASE_DB_URL is currently unused.
Never commit .env or expose GEMINI_API_KEY in frontend code.
Do not use:
NEXT_PUBLIC_GEMINI_API_KEY=
The Gemini API key must remain server-side.
4. Start the backend
From the repository root:
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
The backend will run at:
http://127.0.0.1:8000
Health endpoint:
http://127.0.0.1:8000/api/health
5. Start the frontend
Open a second terminal:
cd frontend
npm install
npm run dev
The frontend will normally run at:
http://localhost:3000
During local development, the frontend can use the optional:
NEXT_PUBLIC_API_URL=http://localhost:8000
In production, the frontend uses same-origin /api/... routes.
Resume Handling
The backend accepts supported resume files and extracts text locally.
Supported formats include:
- PDF
- DOCX
The application validates the uploaded file and applies a size limit before processing.
Resume content is used to personalize the interview and is not intended to be permanently stored as an uploaded binary file.
Scoring
The platform uses two scoring components.
MCQ score
MCQs are scored locally using the stored answer key.
Gemini is not called for MCQ scoring.
Theoretical score
The five theoretical answers are evaluated together in one Gemini request.
The evaluation considers answer quality and technical relevance and returns structured feedback.
Overall score
The final score is calculated locally using:
Overall Score = 40% MCQ Score + 60% Theoretical Score
The result is presented on a 1–10 scale.
The platform also displays category-level assessment, strengths, weaknesses, and recommended topics.
Voice Features
The platform uses browser-native speech capabilities.
Text-to-Speech
Questions can be read aloud using the browser's SpeechSynthesis API.
Speech-to-Text
Users can answer theoretical questions using browser speech recognition where supported.
The speech layer does not require a Gemini API call.
Browser support and permissions may affect speech recognition availability.
API Overview
The backend exposes endpoints for:
- Health checking
- Domain retrieval
- Resume upload
- Interview creation
- Question generation
- Answer saving
- Interview completion/evaluation
- Result retrieval
Production requests are routed through the Vercel /api/... path to the FastAPI service.
Vercel Deployment
The application is deployed as a Vercel Services project.
Architecture:
                    Vercel
                      │
              ┌───────┴────────┐
              │                │
        Frontend Service   Backend Service
          Next.js            FastAPI
              │                │
              └────── /api ────┘
                       │
                 Gemini API
The root vercel.json defines:
- frontend/ as the Next.js service
- backend/ as the FastAPI service
- FastAPI entrypoint: app.main:app
- /api/* routing to the backend
- remaining routes to the frontend
The frontend uses same-origin /api/... calls in production, so a separate public backend URL is not required.
Vercel Environment Variables
Set the following on the backend service:
GEMINI_API_KEY=your_gemini_api_key
Optional:
LLM_MODEL=gemini-3.5-flash-lite
FRONTEND_ORIGINS=
SUPABASE_DB_URL=
Do not add the Gemini key as a frontend/public environment variable.
Git and Automatic Deployment
The repository is connected to Vercel through GitHub.
Typical workflow:
git add .
git commit -m "docs: update README"
git push origin main
A push to the production branch triggers a new Vercel deployment automatically.
For README-only changes, no manual "Redeploy" action is required.
Testing
The project includes backend tests covering:
- API behavior
- Resume handling
- Interview flow
- Gemini provider behavior
- Structured output handling
- Retry behavior
- Validation failures
- Timeout/network failures
- Scoring behavior
Run backend tests:
cd backend
pytest -q
Frontend TypeScript check:
cd frontend
npx tsc --noEmit
Frontend production build:
npm run build
Before deployment, verify:
Backend tests pass
Frontend TypeScript check passes
Frontend production build passes
git diff --check passes
Security
Important security practices:
- Gemini API key is server-side only
- .env is gitignored
- No Gemini API key is exposed to the frontend
- Resume uploads are validated
- Uploaded resume binaries are not intended for permanent storage
- Raw provider errors are not exposed directly to users
- Provider/API credentials are not logged
- Interview answer content and resume content are not included in diagnostic logs
- Structured responses are validated with Pydantic
If a Gemini API key has ever been exposed publicly or committed accidentally, revoke/rotate it and replace it in the deployment environment.
Current Deployment Limitation
Interview state and locks are currently maintained in backend process memory.
This is suitable for a demo/hackathon deployment, but it is not a fully durable production architecture.
On Vercel, backend requests may be handled by different function instances or after a restart. Therefore, an in-progress interview is not guaranteed to persist across every request.
A future production version should move interview state to a persistent database such as PostgreSQL/Supabase.
Error Handling
The application includes controlled handling for:
- Invalid resume files
- Oversized uploads
- Invalid AI responses
- Structured-output failures
- Pydantic validation failures
- Provider HTTP errors
- Network failures
- Timeouts
- AI-stage retry exhaustion
- Duplicate interview submission
The frontend prevents duplicate submission while an evaluation request is in progress.
Known Limitations
- Interview state is currently in memory.
- Persistent database storage is not yet used for interview sessions.
- Browser speech recognition support varies by browser.
- Voice functionality depends on microphone permission and browser support.
- Gemini response quality depends on the selected model and provider availability.
- Production deployment may require persistent state for reliable multi-instance operation.
Future Improvements
Potential next steps:
- PostgreSQL/Supabase persistence
- User authentication
- Interview history
- Dashboard with previous scores
- Persistent candidate profiles
- More detailed analytics
- Interview timers
- Adaptive difficulty
- More domain-specific evaluation criteria
- Better speech recognition fallback
- Rate limiting
- Production-grade distributed state management
- Admin analytics
- Resume version management
Development Philosophy
The project follows a deterministic-first approach:
Use local computation whenever possible
            ↓
Use browser-native APIs for voice
            ↓
Batch AI operations
            ↓
Use structured AI responses
            ↓
Validate AI output
            ↓
Use retries only when necessary
This keeps the platform simpler, faster, easier to test, and significantly reduces AI/API usage.
Project Status
Current status:
- Frontend: Complete
- Backend: Complete
- Resume parsing: Complete
- Domain selection: Complete
- Personalized question generation: Complete
- 5 MCQs + 5 theoretical questions: Complete
- Voice input/output: Implemented
- Local MCQ scoring: Complete
- AI theoretical evaluation: Complete
- Final scoring: Complete
- Error/retry handling: Implemented
- Automated tests: Passing
- Production build: Passing
- Vercel deployment: Live
- Persistent interview database: Future improvement
License
Add the project's chosen license here if/when the repository is formally licensed.