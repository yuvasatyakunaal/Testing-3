import os
import fitz  # PyMuPDF
import requests
import magic  # pip install python-magic
import mimetypes
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
PDF_KEYWORDS = ["education", "experience", "skills", "project", "summary", "profile", "certification"]

def is_file_pdf(file_path: str) -> bool:
    try:
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type == "application/pdf":
            return True
        guess, _ = mimetypes.guess_type(file_path)
        return guess == "application/pdf"
    except Exception:
        return False

def extract_text_from_pdf(file_path: str) -> Tuple[str, str]:
    if not os.path.isfile(file_path):
        return "", f"❌ File not found: {file_path}"
    if os.path.getsize(file_path) > 2 * 1024 * 1024:
        return "", "❌ File too large. Please upload a PDF under 2MB."
    if not is_file_pdf(file_path):
        return "", "❌ Uploaded file is not a valid PDF file. Only PDF resumes are supported."
    try:
        doc = fitz.open(file_path)
        if doc.page_count == 0:
            return "", "❌ The uploaded PDF has no pages."
        text = "".join(page.get_text() for page in doc)
        doc.close()
        if not text.strip():
            return "", "❌ The PDF appears empty or could not be read."
        if not any(k in text.lower() for k in PDF_KEYWORDS):
            return "", "❌ This PDF does not appear to be a resume. Please upload a proper resume document."
        return text, ""
    except RuntimeError as e:
        if "encrypted" in str(e).lower():
            return "", "❌ The PDF is encrypted/protected and cannot be processed."
        return "", f"❌ Error extracting PDF text: {e}"
    except Exception as e:
        return "", f"❌ Error extracting PDF: {e}"

def call_openrouter_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=45)
        if response.status_code == 429:
            return "⏱️ Rate limit reached. Please wait a moment and try again."
        elif response.status_code == 503:
            return "🔧 AI service temporarily unavailable. Please try again shortly."
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content.strip()
    except requests.exceptions.Timeout:
        return "⏱️ Analysis is taking longer than expected. Please try a simpler query."
    except requests.exceptions.ConnectionError:
        return "🔌 Connection issue detected. Please check your internet connection."
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return "Sorry, I couldn't analyze the resume right now. Please try again."

def ensure_slots_persist(tracker):
    resume_uploaded = tracker.get_slot("resume_uploaded")
    resume_text = tracker.get_slot("resume_text")
    if resume_uploaded and resume_text:
        return resume_uploaded, resume_text
    # Fallback: Try to recover from events
    events = tracker.events
    recovered_text = None
    for event in reversed(events):
        if hasattr(event, 'name') and hasattr(event, 'value'):
            if event.name == 'resume_text' and event.value:
                recovered_text = event.value
                return True, recovered_text
    return False, None

# ---- ACTION HANDLERS ----

class ActionUploadResume(Action):
    def name(self) -> Text: return "action_upload_resume"
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get('text', '')
        if user_message.startswith('/upload '):
            file_path = user_message.replace('/upload ', '').strip()
            text, error = extract_text_from_pdf(file_path)
            if error:
                dispatcher.utter_message(text=error)
                return [SlotSet("resume_uploaded", False)]
            dispatcher.utter_message(text=f"✅ Resume uploaded successfully from: {file_path}")
            dispatcher.utter_message(text="Now you can ask me questions about the candidate!")
            return [SlotSet("resume_uploaded", True), SlotSet("resume_text", text)]
        else:
            dispatcher.utter_message(text="To upload a resume, use: /upload /path/to/your/resume.pdf")
            return [SlotSet("resume_uploaded", False)]

class ActionAskSkills(Action):
    def name(self) -> Text: return "action_ask_skills"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "From the given resume, extract all skills exactly as written.\n\n"
            "✅ If the resume already categorizes skills (e.g., Technical Skills, Soft Skills, Tools, etc.), retain the same categories and formatting.\n"
            "✅ If no categorization is present, then organize the extracted skills into two groups: Technical Skills and Soft Skills.\n"
            "❌ Do not assume, interpret, or add any skills not explicitly mentioned.\n"
            "❌ Only include content from the Skills section(s) of the resume. Ignore skills implied elsewhere (e.g., in projects or experience).\n\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskSummary(Action):
    def name(self) -> Text: return "action_ask_summary"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Extract the Professional Summary of the candidate from the given resume.\n"
            "✅ If a summary/profile/objective section is explicitly written in the resume, extract that exact content only.\n"
            "✅ If not available, generate a concise and professional summary based solely on the actual content of the resume, including:\n"
            "- Key strengths\n- Experience level\n- Notable achievements\n- Overall profile and areas of expertise\n"
            "❌ Do not assume or add anything not present in the resume.\n"
            "❌ No filler or generalizations — strictly base it on resume content.\n\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskExperience(Action):
    def name(self) -> Text: return "action_ask_experience"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Analyze the following resume and extract only the Work Experience details.\n"
            "✅ For each experience, provide:\n"
            "- Job Title\n- Company Name\n- Duration (Start – End)\n- Key Responsibilities (as bullet points, if available) or summary or description given in resume\n"
            "✅ Present the experiences in reverse chronological order (most recent first).\n"
            "❌ Do not include internship/project/volunteer experience unless it's under the Work Experience heading.\n"
            "❌ No summaries, no assumptions. Only extract what’s written in the resume.\n\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskTechstack(Action):
    def name(self) -> Text: return "action_ask_techstack"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "From the given resume, extract only the technologies listed under the 'Skills' section.\n"
            "✅ Categorize them clearly into,\n"
            "- Programming Languages\n- Frameworks/Libraries\n- Databases\n- Tools\n- Platforms/Cloud\n"
            "✅ Include proficiency levels if mentioned.\n"
            "❌ Do not include any technologies outside the 'Skills' section.\n"
            "❌ No assumptions or additions. Just what's explicitly listed.\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskEducation(Action):
    def name(self) -> Text: return "action_ask_education"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Extract the following educational details from the given resume:\n"
            "- Degree name\n- Institution name\n- Graduation year\n- CGPA (if mentioned)\n"
            "⚠️ Only return these four fields.\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskContact(Action):
    def name(self) -> Text: return "action_ask_contact"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Extract contact information from this resume.\n"
            "Include name, email, phone number, location, LinkedIn profile, and any other contact details.\n"
            "Present in a clean, organized format.\n"
            f"Resume text:\n{resume_text}\nPlease provide contact information."
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskProjects(Action):
    def name(self) -> Text: return "action_ask_projects"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Extract detailed Project information from the given resume.\n"
            "✅ For each project, include:\n"
            "- Project Name\n- Description (as written)\n- Technologies Used\n- Duration (if mentioned)\n- Outcomes or Results (if mentioned)\n"
            "✅ Maintain the exact structure, wording, and formatting from the resume where available.\n"
            "❌ Do not summarize or infer anything that isn’t explicitly stated.\n"
            "❌ Only pull information from the Projects section (not from Experience or elsewhere).\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionAskCertifications(Action):
    def name(self) -> Text: return "action_ask_certifications"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "From the given resume, extract the following sections exactly as they appear:\n"
            "- Certifications\n- Awards\n- Achievements\n"
            "✅ For each item, include (if mentioned):\n"
            "Certification/Award/Achievement Name (that's it)\n"
            "✅ Preserve the original wording and formatting from the resume.\n"
            "❌ Do not rephrase, infer, or generate any content.\n"
            "❌ No personal responses\n"
            "❌ Only extract from given labeled sections like 'Certifications', 'Achievements', 'Awards', or similar.\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionCompareSkills(Action):
    def name(self) -> Text: return "action_compare_skills"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        user_message = tracker.latest_message.get('text', '')
        prompt = (
            f"Based on this resume and job requirements mentioned in the question: '{user_message}'\n"
            "Please compare the candidate's skills with the job requirements and provide:\n"
            "1. Matching skills\n2. Missing skills\n3. Overall fit assessment\n4. Recommendations\n\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionGetResumeStats(Action):
    def name(self) -> Text: return "action_get_resume_stats"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        prompt = (
            "Analyze the following resume and provide a detailed overview report containing only the following items:\n"
            "Total Years of Experience (based on the Work Experience section)\n"
            "Number of Jobs/Positions Held\n"
            "Total Number of Unique Skills Mentioned (only from explicitly listed skills sections)\n"
            "Highest Education Level (Degree name, Institution, Graduation Year)\n"
            "Key Highlights (Notable projects, certifications, achievements—based only on actual content)\n"
            "Resume Quality Assessment:\n"
            "- Clarity & structure\n- Professional tone\n- Relevance of content\n- Visual formatting (if applicable)\n"
            "- Suggestions for improvement (if any)\n"
            "✅ Base everything strictly on the content present in the resume.\n"
            "❌ Do not make assumptions or generate content not mentioned.\n"
            "❌ No hallucinations, fluff, or generic advice.\n\n"
            f"Resume text:\n{resume_text}"
        )
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=f"📊 Resume Statistics:\n{response}")
        return [SlotSet("resume_uploaded", True), SlotSet("resume_text", resume_text)]

class ActionDebugSlots(Action):
    def name(self) -> Text: return "action_debug_slots"
    def run(self, dispatcher, tracker, domain):
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        all_slots = tracker.current_slot_values()
        dispatcher.utter_message(text="🔍 **Debug Information:**")
        dispatcher.utter_message(text=f"📊 resume_uploaded: {resume_uploaded}")
        dispatcher.utter_message(text=f"📝 resume_text exists: {'Yes' if resume_text else 'No'}")
        dispatcher.utter_message(text=f"📏 resume_text length: {len(resume_text) if resume_text else 0} characters")
        if resume_text:
            preview = resume_text[:100] + "--->...." if len(resume_text) > 200 else resume_text
            dispatcher.utter_message(text=f"👀 Text preview: {preview}")
        return [
            SlotSet("resume_uploaded", resume_uploaded if resume_uploaded else False),
            SlotSet("resume_text", resume_text if resume_text else "")
        ]
