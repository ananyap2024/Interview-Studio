"use client";

import { useEffect, useRef, useState } from "react";

type SpeechRecognitionResult = { transcript: string; isFinal: boolean };
type SpeechRecognitionEvent = Event & {
  resultIndex: number;
  results: ArrayLike<ArrayLike<SpeechRecognitionResult>>;
};
type SpeechRecognitionErrorEvent = Event & { error: string };
type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
};
type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

type VoiceAnswerProps = {
  value: string;
  onChange: (value: string) => void;
};

export default function VoiceAnswer({ value, onChange }: VoiceAnswerProps) {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const speechWindow = window as SpeechWindow;
    setSupported(Boolean(speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition));
    return () => recognitionRef.current?.stop();
  }, []);

  const toggleRecording = () => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setMessage("Speech recognition is not supported in this browser. Type your answer instead.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .slice(event.resultIndex)
        .map((result) => result[0]?.transcript ?? "")
        .filter(Boolean)
        .join(" ");
      if (transcript.trim()) onChange([value.trim(), transcript.trim()].filter(Boolean).join(" "));
      else setMessage("No speech was captured. Try again or type your answer.");
    };
    recognition.onerror = (event) => {
      const messages: Record<string, string> = {
        "not-allowed": "Microphone permission was denied. Allow access or type your answer.",
        "service-not-allowed": "Speech recognition is blocked by the browser. Type your answer instead.",
        "no-speech": "No speech was detected. Try again or type your answer.",
        network: "The browser speech service is unavailable. Type your answer instead.",
      };
      setMessage(messages[event.error] ?? "Speech recognition failed. Type your answer instead.");
      setListening(false);
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    setMessage("");
    try {
      recognition.start();
      setListening(true);
    } catch {
      setMessage("The microphone could not start. Check permissions or type your answer.");
      setListening(false);
    }
  };

  return (
    <div className="voice-answer">
      <div className="voice-answer-heading">
        <label htmlFor="answer-text">Your answer</label>
        <button className={`tool-button${listening ? " is-listening" : ""}`} onClick={toggleRecording} type="button">
          <span aria-hidden="true">{listening ? "■" : "●"}</span>{listening ? "Stop recording" : "Speak answer"}
        </button>
      </div>
      <textarea
        id="answer-text"
        onChange={(event) => onChange(event.target.value)}
        placeholder="Build your answer step by step…"
        value={value}
      />
      {message && <p className="voice-message" role="status">{message}</p>}
      {!supported && <p className="voice-message">Voice input is unavailable here. Text answers work normally.</p>}
      {supported && !value.trim() && <p className="voice-message">Your transcript will appear above and can be edited before submission.</p>}
    </div>
  );
}