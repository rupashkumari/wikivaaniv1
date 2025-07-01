import streamlit as st
import wikipediaapi
import speech_recognition as sr
from gtts import gTTS
import os
import base64
from datetime import datetime
import requests
from PIL import Image
import io
import time
import winsound
# from googletrans import Translator  # For actual translations


# Initialize Wikipedia API with user_agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='english',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent="WikiVaaniApp/1.0 (https://example.com; your@email.com)"
)

# App configuration
st.set_page_config(
    page_title="Wiki Vaani",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for dark theme
st.markdown("""
<style>
.stApp {
    background-color: #000000;
    color: #ffffff;
}
.sidebar .sidebar-content {
    background-color: #1a1a1a;
    color: #ffffff;
}
.article-card {
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(255,255,255,0.1);
    background-color: #1a1a1a;
    margin-bottom: 20px;
    color: #ffffff;
}
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}
p, div, span {
    color: #ffffff !important;
}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    color: #ffffff;
    background-color: #1a1a1a;
}
.st-bd, .st-cb, .st-cg, .st-ch, .st-ci, .st-cj, .st-ck, .st-cl, .st-cm {
    color: #ffffff;
}
.stRadio>div>div>label, .stCheckbox>div>div>label {
    color: #ffffff;
}
.stSelectbox>div>div>select {
    color: #ffffff;
    background-color: #1a1a1a;
}
.stSlider>div>div>div>div>div {
    background-color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# Audio functions
def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)





def text_to_speech(text, lang='en'):
    try:
        # Create temporary in-memory file
        audio_bytes = io.BytesIO()
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Play audio directly without saving to disk
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")




def recognize_speech(language="en"):
    r = sr.Recognizer()
    # Optimized settings for sentence recognition
    r.energy_threshold = 3000  # Adjust for quieter voices
    r.pause_threshold = 1.5    # Wait longer between phrases
    r.dynamic_energy_threshold = True  # Auto-adjust to noise
    r.phrase_time_limit = 10   # Allow longer sentences (10 seconds max)

    # Language mapping (Google's language codes)
    lang_codes = {
        "english": "en-IN",
        "hindi": "hi-IN",
        "telugu": "te-IN",
        "tamil": "ta-IN",
        "marathi": "mr-IN"
    }

    with st.spinner("Preparing microphone..."):
        try:
            with sr.Microphone() as source:
                # Visual feedback
                st.info("Listening... Speak your full sentence now!")
                
                # Play a beep to indicate recording start
                try:
                    winsound.Beep(1000, 200)
                except:
                    pass
                
                # Listen with adjusted settings
                audio = r.listen(
                    source, 
                    timeout=5,  # Wait 5 seconds for speech to start
                    phrase_time_limit=10  # Max 10 seconds of speech
                )
                
                # Process the audio
                with st.spinner("Processing your speech..."):
                    try:
                        text = r.recognize_google(audio, language=lang_codes.get(language.lower(), "en-IN"))
                        st.success(f"Recognized: {text}")
                        return text
                    except sr.UnknownValueError:
                        st.error("Couldn't understand the audio. Please try again.")
                    except sr.RequestError as e:
                        st.error(f"Couldn't request results; check your internet connection. Error: {e}")
                        
        except sr.WaitTimeoutError:
            st.error("No speech detected. Please try again.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    return None
    



def get_wiki_page(title):
    try:
        # Try exact match first
        page = wiki_wiki.page(title)
        
        # If not found, search for alternatives
        if not page.exists():
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={title}&limit=3"
            response = requests.get(search_url)
            if response.status_code == 200:
                search_results = response.json()
                if search_results[1]:  # [1] contains titles
                    page = wiki_wiki.page(search_results[1][0])  # Pick top result
        
        if not page.exists():
            return {"error": f"No results for '{title}'. Try different keywords."}
        
        return {
            "title": page.title,
            "summary": page.summary[:500] + ("..." if len(page.summary) > 500 else ""),
            "url": page.fullurl,
            "content": page.text[:3000] + ("..." if len(page.text) > 3000 else ""),
        }
    except Exception as e:
        return {"error": f"Wikipedia error: {str(e)}"}
    



# AI functions (simplified)
def summarize_text(text, length="medium"):
    lengths = {"short": 100,
                "medium": 250,
                  "long": 400}
    return text[:lengths[length]] + f"... [AI Summary - {length}]"

def translate_text(text, target_lang="en"):
    lang_map = {"French": "fr", "Spanish": "es", "German": "de", "Hindi": "hi"}
    return f"[{target_lang} Translation]: {text[:200]}... (Real translation would appear here)"

def explain_simply(text):
    return f"Simple Explanation: {text[:200]}... [This would be a child-friendly explanation]"

# Main app function
def main():
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Wiki Vaani")
        st.markdown("---")
        
        st.title("Voice Search")

        # Navigation options
        nav_option = st.radio(
            "Menu",
            ["Search", "History", "Settings"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("Recent Searches")
        if not st.session_state.history:
            st.info("No search history")
        else:
            for i, item in enumerate(reversed(st.session_state.history[-3:])):
                if st.button(f"{item['query']} ({item['time']})", key=f"hist_{i}"):
                    st.session_state.last_search = item["query"]
                    nav_option = "Search"
    
    # Main content area
    if nav_option == "Search":
        st.title("Wikipedia Search")
        st.markdown("### 🔍 Wikipedia Search")
        search_query = st.text_input(
            label="",
            value=getattr(st.session_state, "last_search", ""),
            placeholder="e.g. Albert Einstein, India, Water Cycle",
            help="Type a topic, person, event, or concept you'd like to learn about from Wikipedia.",
            key="search"
        )
        
        if not search_query:
            st.info("💡 You can search for people (e.g. Mahatma Gandhi), countries (e.g. India), science topics (e.g. Water Cycle), or any other Wikipedia topic.")
        
        if search_query:
            with st.spinner(f"Searching for '{search_query}'..."):
                article = get_wiki_page(search_query)
                
                if "error" in article:
                    st.error(article["error"])
                else:
                    # Display article
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown("<div class='article-card'>", unsafe_allow_html=True)
                        st.header(article["title"])
                        st.markdown(f"**Summary**: {article['summary']}")
                        
                        with st.expander("Read Full Article"):
                            st.write(article["content"])

                            # Add a button to read the full article aloud
                        if st.button("🔊 Read Full Article Aloud", key=f"read_full_{article['title']}"):
                            with st.spinner(f"Reading '{article['title']}'..."):
                             text_to_speech(article["content"])
                        
                        st.subheader("AI Tools")
                        tab1, tab2, tab3 = st.tabs(["📝 Summarize", "🌍 Translate", "🧒 Explain Simply"])
                        
                        with tab1:
                            length = st.radio("Length", ["short", "medium", "long"], horizontal=True, key="sum_len")
                            if st.button("Generate Summary", key="sum_btn"):
                                summary = summarize_text(article["content"], length)
                                st.write(summary)
                                # if st.checkbox("Read aloud", key="sum_audio"):
                                    # text_to_speech(summary)
                        
                      

                        with tab2:
                            lang = st.selectbox("Language", ["Hindi", "French", "Spanish", "German"], key="trans_lang")
                            if st.button("Translate", key="trans_btn"):
                               with st.spinner("Translating..."):
                               # Translate both summary and content
                                translated_summary = translate_text(article["summary"], lang)
                                translated_content = translate_text(article["content"][:1000], lang)  # First 1000 chars
            
                                st.write(f"**Translated Summary ({lang}):** {translated_summary}")
                                st.write(f"**Translated Content:** {translated_content}...")
            
                                if st.checkbox("Read translated text aloud", key="trans_audio"):
                                 text_to_speech(translated_summary, lang=lang.lower()[:2])
                        
                        with tab3:
                            if st.button("Simplify Explanation", key="simple_btn"):
                                simple = explain_simply(article["summary"])
                                st.write(simple)
                                # if st.checkbox("Read aloud", key="simple_audio"):
                                    # text_to_speech(simple)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("Quick Links")
                        st.markdown(f"[📖 Read on Wikipedia]({article['url']})")
                    
                    # Add to history
                    st.session_state.history.append({
                        "query": search_query,
                        "time": datetime.now().strftime("%H:%M"),
                        "title": article["title"]
                    })

   
    #                     })
    elif nav_option == "Voice Search":
     st.title("🎤 Voice Search")
    language = st.selectbox(
        "Select Language",
        ["english", "hindi", "telugu", "tamil", "marathi"],  # English, Hindi, French, Spanish, German
        key="voice_lang"
    )
    
   
    if st.button("🎤 Start Voice Search"):
        query = recognize_speech()
        if query:
            with st.spinner(f"Searching for '{query}'..."):
                article = get_wiki_page(query)
                
                if "error" in article:
                    # Try to find any relevant page
                    st.warning(f"Couldn't find exact match for '{query}'. Showing closest match:")
                    search_results = wiki_wiki.search(query)
                    if search_results:
                        article = get_wiki_page(search_results[0])
                
                if "error" in article:
                    st.error(f"Couldn't find Wikipedia page related to '{query}'. Try rephrasing.")
                else:
                    # Display results directly
                    st.markdown("<div class='article-card'>", unsafe_allow_html=True)
                    st.header(article["title"])
                    st.markdown(f"**Summary**: {article['summary']}")
                    
                    with st.expander("Read Full Article"):
                        st.write(article["content"])
                        if st.button("🔊 Read Aloud", key=f"read_{article['title']}"):
                            text_to_speech(article["content"])
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Add to history
                    st.session_state.history.append({
                        "query": query,
                        "time": datetime.now().strftime("%H:%M"),
                        "title": article["title"]
                    })


    elif nav_option == "History":
        st.title("Search History")
        if not st.session_state.history:
            st.info("No search history yet")
        else:
            for i, item in enumerate(reversed(st.session_state.history)):
                st.write(f"{i+1}. {item['query']} ({item['time']})")
    
    elif nav_option == "Settings":
        st.title("Settings")
        st.subheader("Audio Settings")
        st.slider("Voice Speed", 0.5, 2.0, 1.0, key="voice_speed")
        st.radio("Voice Gender", ["Male", "Female"], key="voice_gender")
        
        st.subheader("Appearance")
        st.selectbox("Theme", ["Light", "Dark"], key="theme")

if __name__ == "__main__":
    main()
