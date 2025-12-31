import os
import fitz  # PyMuPDF
import requests
import tempfile
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def call_openrouter_api(prompt: str) -> str:
    """Call OpenRouter API to analyze resume content"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
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
def call_openrouter_api_with_retry(prompt: str, max_retries=3) -> str:
    for attempt in range(max_retries):
        try:
            response = call_openrouter_api(prompt)
            if response and not response.startswith("Sorry, I couldn't"):
                return response
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return "Analysis temporarily unavailable. Please try again."

def ensure_slots_persist(tracker):
    """Helper function to check and maintain slot persistence"""
    resume_uploaded = tracker.get_slot("resume_uploaded")
    resume_text = tracker.get_slot("resume_text")
    
    print(f"SLOT CHECK: resume_uploaded={resume_uploaded}, text_length={len(resume_text) if resume_text else 0}")
    
    # If slots exist and are valid, return them
    if resume_uploaded and resume_text:
        return resume_uploaded, resume_text
    
    # Try to recover from recent conversation events
    print("ATTEMPTING SLOT RECOVERY from conversation history...")
    events = tracker.events
    recovered_text = None
    
    for event in reversed(events):
        if hasattr(event, 'name') and hasattr(event, 'value'):
            if event.name == 'resume_text' and event.value:
                recovered_text = event.value
                print(f"RECOVERED resume_text from event: length={len(recovered_text)}")
                return True, recovered_text
    
    print("SLOT RECOVERY FAILED - no resume data found")
    return False, None

class ActionUploadResume(Action):
    """Handle resume upload and text extraction"""
    
    def name(self) -> Text:
        return "action_upload_resume"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            user_message = tracker.latest_message.get('text', '')
            
            if user_message.startswith('/upload '):
                file_path = user_message.replace('/upload ', '').strip()
                
                if not os.path.exists(file_path):
                    dispatcher.utter_message(text=f"File not found: {file_path}")
                    return [SlotSet("resume_uploaded", False)]
                
                if not file_path.lower().endswith('.pdf'):
                    dispatcher.utter_message(text="Please provide a PDF file.")
                    return [SlotSet("resume_uploaded", False)]
                
                resume_text = extract_text_from_pdf(file_path)
                
                if resume_text:
                    dispatcher.utter_message(text=f"✅ Resume uploaded successfully from: {file_path}")
                    dispatcher.utter_message(text="Now you can ask me questions about the candidate!")
                    
                    print(f"DEBUG: Setting slots - resume_uploaded: True, text_length: {len(resume_text)}")
                    
                    return [
                        SlotSet("resume_uploaded", True),
                        SlotSet("resume_text", resume_text)
                    ]
                else:
                    dispatcher.utter_message(text="Failed to extract text from PDF.")
                    return [SlotSet("resume_uploaded", False)]
            
            else:
                dispatcher.utter_message(text="To upload a resume, use: /upload /path/to/your/resume.pdf")
                return [SlotSet("resume_uploaded", False)]
            
        except Exception as e:
            dispatcher.utter_message(text=f"Error uploading resume: {str(e)}")
            return [SlotSet("resume_uploaded", False)]

class ActionAskSkills(Action):
    """Extract and list candidate skills"""
    
    def name(self) -> Text:
        return "action_ask_skills"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskSkills ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"===============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        From the given resume, extract all skills exactly as written.

        ✅ If the resume already categorizes skills (e.g., Technical Skills, Soft Skills, Tools, etc.), retain the same categories and formatting.

        ✅ If no categorization is present, then organize the extracted skills into two groups:
        Technical Skills
        Soft Skills

        ❌ Do not assume, interpret, or add any skills not explicitly mentioned.
        ❌ Only include content from the Skills section(s) of the resume. Ignore skills implied elsewhere (e.g., in projects or experience).
        
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskSummary(Action):
    """Generate candidate summary"""
    
    def name(self) -> Text:
        return "action_ask_summary"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskSummary ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"===============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        Extract the Professional Summary of the candidate from the given resume.

        ✅ If a summary/profile/objective section is explicitly written in the resume, extract that exact content only.
        ✅ If not available, generate a concise and professional summary based solely on the actual content of the resume, including:
        Key strengths
        Experience level
        Notable achievements
        Overall profile and areas of expertise

        ❌ Do not assume or add anything not present in the resume.
        ❌ No filler or generalizations — strictly base it on resume content.
        
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskExperience(Action):
    """Extract work experience information"""
    
    def name(self) -> Text:
        return "action_ask_experience"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskExperience ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"=================================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        Analyze the following resume and extract only the Work Experience details.

        ✅ For each experience, provide:
        Job Title
        Company Name
        Duration (Start – End)
        Key Responsibilities (as bullet points, if available) or summary or description given in resume

        ✅ Present the experiences in reverse chronological order (most recent first).
        ❌ Do not include internship/project/volunteer experience unless it's under the Work Experience heading.
        ❌ No summaries, no assumptions. Only extract what’s written in the resume.
        
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskTechstack(Action):
    """Extract technology stack and programming languages"""
    
    def name(self) -> Text:
        return "action_ask_techstack"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskTechstack ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"=================================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        From the given resume, extract only the technologies listed under the "Skills" section.

        ✅ Categorize them clearly into, for example like (not as it is, give whats there in resume):
        Programming Languages
        Frameworks/Libraries
        Databases
        Tools
        Platforms/Cloud

        ✅ Include proficiency levels if mentioned.
        ❌ Do not include any technologies outside the "Skills" section.
        ❌ No assumptions or additions. Just what's explicitly listed.
        ❌ No extra explanation or formatting outside the categories.
        
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskEducation(Action):
    """Extract education information"""
    
    def name(self) -> Text:
        return "action_ask_education"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskEducation ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"===============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        Extract the following educational details from the given resume:
        Degree name
        Institution name
        Graduation year
        CGPA (if mentioned)
        ⚠️ Only return these four fields.
        ⚠️ No explanations, no additional data, no extra formatting.
        ⚠️ Output should be concise and structured as:-
        Degree: [Your answer]  
        Institution: [Your answer]  
        Graduation Year: [Your answer]  
        CGPA: [Your answer]
        --
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskContact(Action):
    """Extract contact information"""
    
    def name(self) -> Text:
        return "action_ask_contact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskContact ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"=============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        Extract contact information from this resume.
        Include name, email, phone number, location, LinkedIn profile, and any other contact details.
        Present in a clean, organized format.
        
        Resume text:
        {resume_text}
        
        Please provide contact information.
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskGeneral(Action):
    """Handle general questions about the resume"""
    
    def name(self) -> Text:
        return "action_ask_general"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskGeneral ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"==============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        user_message = tracker.latest_message.get('text', '')
        
        prompt = f"""
        Based on the following resume, answer the question below using only the information mentioned in the resume.

        Question:{user_message}?
        ✅ Refer strictly to resume content — do not infer or generate anything not clearly stated.
        ✅ If the answer is not found in the resume, respond with: "Not mentioned in the resume."
        ❌ No assumptions, summaries, or external knowledge.
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskProjects(Action):
    """Extract project information"""
    
    def name(self) -> Text:
        return "action_ask_projects"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskProjects ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"===============================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        Extract detailed Project information from the given resume.

        ✅ For each project, include:
        Project Name
        Description (as written)
        Technologies Used
        Duration (if mentioned)
        Outcomes or Results (if mentioned)

        ✅ Maintain the exact structure, wording, and formatting from the resume where available.

        ❌ Do not summarize or infer anything that isn’t explicitly stated.
        ❌ Only pull information from the Projects section (not from Experience or elsewhere).
        ❌ No extra interpretation, and do not generate descriptions/tech unless clearly mentioned.
        
        Resume text:
        {resume_text}
        
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionAskCertifications(Action):
    """Extract certifications and achievements"""
    
    def name(self) -> Text:
        return "action_ask_certifications"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionAskCertifications ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"=====================================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        prompt = f"""
        From the given resume, extract the following sections exactly as they appear:
        Certifications
        Awards
        Achievements

        ✅ For each item, include (if mentioned):
        Certification/Award/Achievement Name (thats it)
        

        ✅ Preserve the original wording and formatting from the resume.

        ❌ Do not rephrase, infer, or generate any content.
        ❌ No personal responses
        ❌ Only extract from given labeled sections like "Certifications", "Achievements", "Awards", or similar.
        
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionCompareSkills(Action):
    """Compare candidate skills with job requirements"""
    
    def name(self) -> Text:
        return "action_compare_skills"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionCompareSkills ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"=================================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        user_message = tracker.latest_message.get('text', '')
        
        prompt = f"""
        Based on this resume and job requirements mentioned in the question: "{user_message}"
        
        Resume text:
        {resume_text}
        
        Please compare the candidate's skills with the job requirements and provide:
        1. Matching skills
        2. Missing skills
        3. Overall fit assessment
        4. Recommendations
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=response)
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionGetResumeStats(Action):
    """Get resume statistics and overview"""
    
    def name(self) -> Text:
        return "action_get_resume_stats"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        
        print(f"=== DEBUG ActionGetResumeStats ===")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"==================================")
        
        if not resume_uploaded or not resume_text:
            dispatcher.utter_message(text="Please upload a resume first using: /upload /path/to/resume.pdf")
            return []
        
        word_count = len(resume_text.split())
        char_count = len(resume_text)
        
        prompt = f"""
        Analyze the following resume and provide a detailed overview report containing only the following items:
        Total Years of Experience (based on the Work Experience section)
        Number of Jobs/Positions Held
        Total Number of Unique Skills Mentioned (only from explicitly listed skills sections)
        Highest Education Level (Degree name, Institution, Graduation Year)
        Key Highlights (Notable projects, certifications, achievements—based only on actual content)
        
        Resume Quality Assessment:
        Clarity & structure
        Professional tone
        Relevance of content
        Visual formatting (if applicable)
        Suggestions for improvement (if any)

        ✅ Base everything strictly on the content present in the resume.
        ❌ Do not make assumptions or generate content not mentioned.
        ❌ No hallucinations, fluff, or generic advice.
                
        Resume text:
        {resume_text}
        """
        
        response = call_openrouter_api(prompt)
        dispatcher.utter_message(text=f"📊 Resume Statistics:\n{response}")
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", True),
            SlotSet("resume_text", resume_text)
        ]

class ActionDebugSlots(Action):
    """Debug action to check current slot values"""
    
    def name(self) -> Text:
        return "action_debug_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        resume_uploaded, resume_text = ensure_slots_persist(tracker)
        all_slots = tracker.current_slot_values()
        
        print(f"=== DEBUG SLOTS INSPECTION ===")
        print(f"All slots: {all_slots}")
        print(f"resume_uploaded: {resume_uploaded}")
        print(f"resume_text length: {len(resume_text) if resume_text else 0}")
        print(f"==============================")
        
        dispatcher.utter_message(text="🔍 **Debug Information:**")
        dispatcher.utter_message(text=f"📊 resume_uploaded: {resume_uploaded}")
        dispatcher.utter_message(text=f"📝 resume_text exists: {'Yes' if resume_text else 'No'}")
        dispatcher.utter_message(text=f"📏 resume_text length: {len(resume_text) if resume_text else 0} characters")
        
        if resume_text:
            preview = resume_text[:100] + "--->...." if len(resume_text) > 200 else resume_text
            dispatcher.utter_message(text=f"👀 Text preview: {preview}")
        
        # Force slots to persist
        return [
            SlotSet("resume_uploaded", resume_uploaded if resume_uploaded else False),
            SlotSet("resume_text", resume_text if resume_text else "")
        ]
