# 🏆 AI-Powered Resume Analysis Chatbot

## Overview

A cutting-edge, LLM-driven Resume Analysis Chatbot that enables rapid, recruiter-friendly insights from any PDF resume. Simply upload a file and ask–the bot instantly extracts skills, summarizes experience, lists projects, and answers custom queries via CLI, all powered by deep NLP and AI.

---

## 🚀 Features

- **PDF Resume Upload:** Drag-and-drop or select a PDF resume for instant parsing.
- **AI-Driven Q&A:** Ask in natural language or via quick-action buttons—get skills, experience, projects, certifications, summary, and more.
- **OpenRouter API (LLM) Integration:** Leverages advanced models (Mistral-7B via OpenRouter) for human-like analysis.
- **Custom Python Actions:** Handles file upload, PDF parsing (PyMuPDF), Rasa slot/session management, and AI request/response pipeline.
- **Robust Error Handling:** Timeouts, API failures, and invalid uploads return clear messages.
- **Session Persistence / Slot Resilience:** Custom action logic ensures the resume stays "remembered" for all user queries after upload.

---

## 💼 Sample Use Cases

- **Recruiters/HR:** Instantly extract key qualifications, depth of experience, or highlight unique projects—without reading the whole resume.
- **Job Seekers:** Benchmark your own CV and see what a modern AI will highlight or miss.
- **Developers:** Easily extend for custom company needs (e.g., job fit scoring, gap analysis).

---

## 🛠️ Tech Stack

| Layer             | Tech                                                         |
| ----------------- | ------------------------------------------------------------ |
| **Bot/Core**      | Rasa Open Source 3.x (Python, NLU, Core, Actions)            |
| **PDF Parsing**   | PyMuPDF (fitz)                                               |
| **AI Analysis**   | OpenRouter API (Mistral-7B-Instruct or similar)              |
| **Session/Slots** | Custom slot management + robust recovery logic in actions.py |
| **Prompting**     | Tailored, context-specific LLM prompts per analysis type     |

---

## ⚙️ How It Works

1. **User uploads a PDF resume.**
2. **Bot parses PDF** with PyMuPDF, stores content in a session slot.
3. **User clicks a quick-action or enters a custom question.**
4. **Rasa custom action** validates upload, sends prompt (including resume text) to OpenRouter API.
5. **LLM (OpenRouter)** analyzes, summarizes, and returns a recruiter-formatted answer.
6. **UI displays the latest answer**—no chat clutter, just pure Q&A.

## 👨‍💻 Engineering Highlights

- **Recoverable, Persistent Slots:** Slots and resume data persist reliably—from CLI or web—even across session boundaries, thanks to custom session and event recovery logic in `actions.py`.
- **Resilient Error Handling:** All API calls have timeouts and user-friendly fallback messages.
- **Natural Prompt Engineering:** Each query type (skills, summary, projects, etc.) has a prompt carefully designed for LLM clarity and performance.
- **Secure, Stateless Design:** No resumes are stored long-term; text is held only for duration of analysis.

---

## Future Enhancements

- UI interaction (Gradio or Flask Framework)
- Multiple resumes
- Advanced user friendly chatbot

## 📦 Main Dependencies

- Python 3.9+
- rasa
- rasa-sdk
- pymupdf
- requests
- gradio (optional - still didnt used or implemented)
- openrouter API (get your API key)

## Create requirements.txt (must)
PyMuPDF==1.23.8
requests==2.31.0
python-dotenv

## Step by step
**0. Check python version (must be 3.9.x, if not - change to 3.9.x and do)**
- python --version

**1. Create a Python Virtual Environment**
- python3 -m venv rasa_env

**2. Activate Python Virtual Environment**
- On Linux/Mac: source rasa_env/bin/activate
- On Windows: rasa_env\Scripts\activate

**3. Upgrade pip (recommended) and Install Rasa**
- pip install --upgrade pip
- pip install rasa 

**4. Install Dependencies**
- python3 -m pip install -r requirements.txt

**5. Rasa**
- Terminal - 1 : rasa run actions --port 5055
- Terminal - 2 :-
  - Training : rasa train
  - Shell or CLI : rasa shell

# Note 
- Use python version - **Python 3.9.x** only.
- For uploading file in CLI : Type - /upload <path of file in your system (without quotation marks)>
---

## 🏁 Getting Started