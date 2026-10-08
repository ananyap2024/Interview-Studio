# Technical Stack

- **Frontend:** Next.js App Router, TypeScript, and Tailwind CSS.
- **Backend:** FastAPI with Pydantic and Pydantic Settings.
- **Database:** Supabase PostgreSQL, configured through `SUPABASE_DB_URL`; database integration is not implemented yet.
- **AI:** Gemini API, configured with `GEMINI_API_KEY` and `LLM_MODEL`.
- **Resume parsing:** PyMuPDF for PDF and `python-docx` for DOCX; deferred to its implementation phase.
- **Voice:** Browser SpeechSynthesis and SpeechRecognition APIs; deferred to its implementation phase.

The frontend communicates with one FastAPI backend. The backend owns configuration, persistence, and any future Gemini requests. No additional services or orchestration layers are included.

The target interview flow uses three LLM calls: resume analysis, generation of all ten questions, and evaluation of the five theoretical answers with qualitative feedback. MCQ scoring, final score calculation, resume text extraction, voice, navigation, and progress are local operations and use no LLM calls.