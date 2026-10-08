"use client";

import { ChangeEvent, useEffect, useState } from "react";
import VoiceAnswer from "./voice-answer";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Domain = { name: string };
type CandidateProfile = { name: string; summary: string; skills: string[] };
type Question = {
  id: number;
  type: "mcq" | "theoretical";
  question: string;
  topic: string;
  difficulty: "easy" | "medium" | "hard";
  options: string[];
};
type Answer = { text: string; selected_answer?: string };
type EvaluationResult = {
  overall_score: number;
  mcq_correct: number;
  mcq_incorrect: number;
  mcq_score: number;
  theoretical_score: number;
  category_scores: Record<string, number>;
  evaluations: Array<{ question_id: number; score: number; feedback: string; strengths: string[]; improvements: string[]; completeness: number }>;
  strengths: string[];
  weaknesses: string[];
  recommended_topics: string[];
  overall_assessment: string;
};

const SESSION_ID_KEY = "interview-studio.current-interview";

async function readJson<T>(response: Response): Promise<T> {
  const data = await response.json();
  if (!response.ok) throw new Error(data.message ?? "Something went wrong. Please try again.");
  return data as T;
}

export default function Home() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState<"domain" | "resume" | "preparing" | "interview" | "evaluating" | "results">("domain");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [interviewId, setInterviewId] = useState("");
  const [candidate, setCandidate] = useState<CandidateProfile | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, Answer>>({});
  const [questionIndex, setQuestionIndex] = useState(0);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [unsavedQuestionId, setUnsavedQuestionId] = useState<number | null>(null);
  const activeQuestion = questions[questionIndex];

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/domains`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load interview domains.");
        return response.json() as Promise<Domain[]>;
      })
      .then((data) => {
        if (active) setDomains(data);
      })
      .catch(() => {
        if (active) setError("Domains are unavailable. Check that the API is running and try again.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const savedInterviewId = window.sessionStorage.getItem(SESSION_ID_KEY);
    if (!savedInterviewId) return;
    void (async () => {
      try {
        const state = await readJson<{
          interview_id: string;
          domain: string;
          candidate_profile: CandidateProfile;
          questions: Question[];
          answers: Record<string, Answer>;
          completed: boolean;
          result: EvaluationResult | null;
        }>(await fetch(`${API_URL}/api/interviews/${savedInterviewId}`));
        setInterviewId(state.interview_id);
        setSelectedDomain(state.domain);
        setCandidate(state.candidate_profile);
        setQuestions(state.questions);
        setAnswers(Object.fromEntries(Object.entries(state.answers).map(([id, answer]) => [Number(id), answer])));
        if (state.completed && state.result) {
          setResult(state.result);
          setStep("results");
        } else if (state.questions.length) setStep("interview");
        else {
          const generated = await readJson<{ questions: Question[] }>(
            await fetch(`${API_URL}/api/interviews/${savedInterviewId}/questions`, { method: "POST" }),
          );
          setQuestions(generated.questions);
          setStep("interview");
        }
      } catch {
        window.sessionStorage.removeItem(SESSION_ID_KEY);
      }
    })();
  }, []);

  useEffect(() => {
    if (unsavedQuestionId === null) return;
    const warnBeforeExit = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeExit);
    return () => window.removeEventListener("beforeunload", warnBeforeExit);
  }, [unsavedQuestionId]);

  useEffect(() => () => window.speechSynthesis?.cancel(), [activeQuestion?.id]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    if (resumeFile && nextFile && (resumeFile.name !== nextFile.name || resumeFile.size !== nextFile.size || resumeFile.lastModified !== nextFile.lastModified)) {
      window.sessionStorage.removeItem(SESSION_ID_KEY);
      setInterviewId("");
    }
    setResumeFile(nextFile);
    setError("");
  };

  const startInterview = async () => {
    if (!resumeFile || !selectedDomain) return;
    setStep("preparing");
    setError("");
    const id = window.sessionStorage.getItem(SESSION_ID_KEY) ?? window.crypto.randomUUID();
    window.sessionStorage.setItem(SESSION_ID_KEY, id);
    setInterviewId(id);
    try {
      const formData = new FormData();
      formData.set("file", resumeFile);
      const parsed = await readJson<{ extracted_text: string }>(
        await fetch(`${API_URL}/api/resume/upload`, { method: "POST", body: formData }),
      );
      const analysis = await readJson<{ candidate_profile: CandidateProfile }>(
        await fetch(`${API_URL}/api/interviews`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ interview_id: id, domain: selectedDomain, resume_text: parsed.extracted_text }),
        }),
      );
      setInterviewId(id);
      setCandidate(analysis.candidate_profile);
      const generated = await readJson<{ questions: Question[] }>(
        await fetch(`${API_URL}/api/interviews/${id}/questions`, { method: "POST" }),
      );
      setQuestions(generated.questions);
      setAnswers({});
      setQuestionIndex(0);
      setStep("interview");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Interview setup failed. Your resume was not stored.");
      setStep("resume");
    }
  };

  const saveCurrentAnswer = async (): Promise<boolean> => {
    const question = questions[questionIndex];
    const answer = answers[question.id] ?? { text: "" };
    if (question.type === "mcq" && !answer.selected_answer) {
      setError("Choose an option before continuing.");
      return false;
    }
    if (question.type === "theoretical" && !answer.text.trim()) {
      setError("Add an answer before continuing. You can type or dictate it.");
      return false;
    }
    try {
      await readJson(await fetch(`${API_URL}/api/interviews/${interviewId}/answers/${question.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: question.id, ...answer }),
      }));
      setUnsavedQuestionId((current) => current === question.id ? null : current);
      setError("");
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Your answer could not be saved.");
      return false;
    }
  };

  const moveQuestion = async (direction: -1 | 1) => {
    if (direction === 1 && !(await saveCurrentAnswer())) return;
    setQuestionIndex((current) => current + direction);
    setError("");
  };

  const finishInterview = async () => {
    if (!(await saveCurrentAnswer())) return;
    if (!window.confirm("Submit all 10 answers for evaluation? You cannot edit them after submission.")) return;
    setStep("evaluating");
    try {
      const finalResult = await readJson<EvaluationResult>(
        await fetch(`${API_URL}/api/interviews/${interviewId}/complete`, { method: "POST" }),
      );
      setResult(finalResult);
      setStep("results");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Evaluation could not be completed. Your answers are saved.");
      setStep("interview");
    }
  };

  const updateAnswer = (questionId: number, answer: Answer) => {
    setAnswers((current) => ({ ...current, [questionId]: answer }));
    setUnsavedQuestionId(questionId);
  };

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="wordmark" href="/" aria-label="Interview Studio home">
          <span className="wordmark-mark">I</span>
          <span>INTERVIEW STUDIO</span>
        </a>
        <span className="topbar-note">MOCK INTERVIEW / 01</span>
      </header>

      <section className="welcome" aria-labelledby="welcome-title">
        <div className="intro-copy">
          <p className="eyebrow"><span /> A SPACE TO THINK OUT LOUD</p>
          <h1 id="welcome-title">Make room for<br /><em>your best thinking.</em></h1>
          <p className="welcome-copy">
            Choose your interview track. Bring a resume, then work through a focused set of technical questions.
          </p>
        </div>

        {step === "domain" && <section className="domain-picker" aria-labelledby="domain-title">
          <div className="section-heading">
            <div>
              <p className="section-kicker">01 / YOUR PRACTICE</p>
              <h2 id="domain-title">Choose a domain</h2>
            </div>
            <span className="selection-count">{selectedDomain ? "1 SELECTED" : "SELECT ONE"}</span>
          </div>
          {loading ? (
            <p className="status-message" role="status">Loading domains…</p>
          ) : error ? (
            <p className="status-message error-message" role="alert">{error}</p>
          ) : (
            <div className="domain-grid" role="group" aria-label="Interview domain">
              {domains.map((domain, index) => (
                <button
                  aria-pressed={selectedDomain === domain.name}
                  className={`domain-option${selectedDomain === domain.name ? " is-selected" : ""}`}
                  key={domain.name}
                  onClick={() => setSelectedDomain(domain.name)}
                  type="button"
                >
                  <span className="domain-index">{String(index + 1).padStart(2, "0")}</span>
                  <span className="domain-name">{domain.name}</span>
                  <span className="domain-mark" aria-hidden="true">{selectedDomain === domain.name ? "✓" : "+"}</span>
                </button>
              ))}
            </div>
          )}
          <div className="picker-footer">
            <span>One track per practice session</span>
            <button className="continue-button" disabled={!selectedDomain} onClick={() => setStep("resume")} type="button">
              Continue <span aria-hidden="true">↗</span>
            </button>
          </div>
        </section>}

        {step === "resume" && <section className="flow-panel" aria-labelledby="resume-title">
          <button className="back-link" onClick={() => { window.sessionStorage.removeItem(SESSION_ID_KEY); setInterviewId(""); setStep("domain"); }} type="button">← Change domain</button>
          <p className="section-kicker">02 / YOUR MATERIAL</p>
          <h2 id="resume-title">Bring your resume</h2>
          <p className="panel-copy">Your PDF or DOCX is read locally to prepare a focused interview.</p>
          <label className="upload-field">
            <span className="upload-icon" aria-hidden="true">↑</span>
            <span>{resumeFile ? resumeFile.name : "Choose a PDF or DOCX"}</span>
            <span className="upload-hint">MAX 5 MB</span>
            <input accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleFileChange} type="file" />
          </label>
          {error && <p className="inline-error" role="alert">{error}</p>}
          <div className="picker-footer">
            <span>{selectedDomain}</span>
            <button className="continue-button" disabled={!resumeFile} onClick={startInterview} type="button">Prepare interview <span aria-hidden="true">↗</span></button>
          </div>
        </section>}

        {step === "preparing" && <section className="flow-panel preparing-panel" role="status">
          <p className="section-kicker">PREPARING YOUR SESSION</p>
          <h2>Reading your experience.</h2>
          <p className="panel-copy">Extracting resume text, shaping a candidate profile, and preparing ten questions.</p>
          <div className="loading-track"><span /></div>
        </section>}

        {step === "interview" && activeQuestion && <section className="interview-panel" aria-labelledby="question-title">
          <div className="interview-heading">
            <div>
              <p className="section-kicker">{selectedDomain}</p>
              <h2>{candidate?.name ? `Your session, ${candidate.name}` : "Your interview"}</h2>
            </div>
            <span className="question-count">{String(questionIndex + 1).padStart(2, "0")} <i>/</i> 10</span>
          </div>
          <progress className="question-progress" max={10} value={questionIndex + 1} aria-label="Interview progress" />
          <div className="question-meta">
            <span>{activeQuestion.type === "mcq" ? "MULTIPLE CHOICE" : "THEORETICAL"}</span>
            <span>{activeQuestion.difficulty.toUpperCase()}</span>
            <span>{activeQuestion.topic}</span>
          </div>
          <h3 id="question-title" className="question-title">{activeQuestion.question}</h3>
          <div className="question-tools">
            <button className="tool-button" onClick={() => {
              if (!("speechSynthesis" in window)) { setError("Speech output is not supported in this browser."); return; }
              window.speechSynthesis.cancel();
              window.speechSynthesis.speak(new SpeechSynthesisUtterance(activeQuestion.question));
            }} type="button"><span aria-hidden="true">◖))</span> Read question</button>
          </div>
          {activeQuestion.type === "mcq" ? (
            <div className="answer-options" role="radiogroup" aria-label="Choose your answer">
              {activeQuestion.options.map((option, index) => {
                const selected = answers[activeQuestion.id]?.selected_answer === option;
                return <button aria-checked={selected} className={`answer-option${selected ? " is-selected" : ""}`} key={option} onClick={() => updateAnswer(activeQuestion.id, { text: "", selected_answer: option })} role="radio" type="button">
                  <span className="option-letter">{String.fromCharCode(65 + index)}</span><span>{option}</span><span className="option-check" aria-hidden="true">{selected ? "✓" : ""}</span>
                </button>;
              })}
            </div>
          ) : (
            <div className="theory-answer">
              <VoiceAnswer
                onChange={(text) => updateAnswer(activeQuestion.id, { text })}
                value={answers[activeQuestion.id]?.text ?? ""}
              />
            </div>
          )}
          {error && <p className="inline-error" role="alert">{error}</p>}
          <div className="interview-footer">
            <button className="back-link" disabled={questionIndex === 0} onClick={() => void moveQuestion(-1)} type="button">← Previous</button>
            <button className="continue-button" onClick={() => questionIndex === 9 ? void finishInterview() : void moveQuestion(1)} type="button">
              {questionIndex === 9 ? "Submit interview" : "Save & continue"} <span aria-hidden="true">↗</span>
            </button>
          </div>
        </section>}

        {step === "evaluating" && <section className="flow-panel preparing-panel" role="status"><p className="section-kicker">FINAL STEP</p><h2>Reviewing your answers.</h2><p className="panel-copy">Your answers are saved while the technical review is prepared.</p><div className="loading-track"><span /></div></section>}

        {step === "results" && result && <section className="flow-panel result-panel" aria-labelledby="result-title">
          <p className="section-kicker">SESSION COMPLETE / {selectedDomain}</p>
          <h2 id="result-title">A thoughtful first read.</h2>
          <div className="score-line"><strong>{result.overall_score.toFixed(1)}</strong><span>/ 10</span><i>OVERALL</i></div>
          <p className="panel-copy">{result.overall_assessment}</p>
          <div className="result-stats"><span><b>{result.mcq_correct}/5</b> MCQ correct</span><span><b>{result.theoretical_score.toFixed(1)}/10</b> theory average</span></div>
          <div className="category-scores" aria-label="Interview categories">
            {Object.entries({ technical_knowledge: "Technical knowledge", domain_knowledge: "Domain knowledge", answer_quality: "Answer quality", problem_solving: "Problem solving" }).map(([key, label]) => (
              <div className="category-score" key={key}><span>{label}</span><b>{(result.category_scores[key] ?? 0).toFixed(1)}<i>/10</i></b></div>
            ))}
          </div>
          <div className="feedback-list">{result.evaluations.map((evaluation) => <article key={evaluation.question_id}><span>Q{evaluation.question_id} · {evaluation.score}/10</span><p>{evaluation.feedback}</p></article>)}</div>
          <button className="continue-button" onClick={() => { window.sessionStorage.removeItem(SESSION_ID_KEY); window.location.reload(); }} type="button">Start a new practice <span aria-hidden="true">↗</span></button>
        </section>}
      </section>

      <footer className="page-footer">
        <span>BUILT FOR BETTER ANSWERS</span>
        <span>INTERVIEW STUDIO <span className="footer-year">· 2026</span></span>
      </footer>
    </main>
  );
}
