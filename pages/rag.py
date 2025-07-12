import streamlit as st
import sys
import os
from dotenv import load_dotenv
import PyPDF2
import io
from typing import List, Dict
import hashlib
import pickle

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PDFProcessor:
    def __init__(self):
        self.pdf_cache_dir = "pdf_cache"
        if not os.path.exists(self.pdf_cache_dir):
            os.makedirs(self.pdf_cache_dir)
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from a PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    st.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                    continue
            return text
        except Exception as e:
            st.error(f"Error processing PDF {pdf_file.name}: {str(e)}")
            return ""
    
    def get_file_hash(self, pdf_file) -> str:
        """Generate hash for file caching"""
        pdf_file.seek(0)
        content = pdf_file.read()
        pdf_file.seek(0)
        return hashlib.md5(content).hexdigest()
    
    def cache_pdf_content(self, file_hash: str, content: str, filename: str):
        """Cache extracted PDF content"""
        cache_data = {
            'content': content,
            'filename': filename
        }
        cache_path = os.path.join(self.pdf_cache_dir, f"{file_hash}.pkl")
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
    
    def load_cached_content(self, file_hash: str) -> Dict:
        """Load cached PDF content"""
        cache_path = os.path.join(self.pdf_cache_dir, f"{file_hash}.pkl")
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

def get_pdf_based_response(question: str, pdf_contents: Dict[str, str], chat_history: List = None) -> tuple:
    """Get response based only on PDF content"""
    
    # Combine all PDF contents
    combined_content = ""
    for filename, content in pdf_contents.items():
        combined_content += f"\n\n=== Content from {filename} ===\n{content}\n"
    
    if not combined_content.strip():
        return "I don't have any PDF content to answer your question. Please upload some PDF files first.", chat_history or []
    
    # Create system prompt
    system_prompt = f"""You are a helpful assistant that answers questions ONLY based on the provided PDF content. 

IMPORTANT RULES:
1. Only use information from the provided PDF content below
2. If the answer is not in the PDF content, clearly state "I cannot find this information in the uploaded PDF documents"
3. Always cite which document/page the information comes from when possible
4. Be accurate and don't make up information not present in the PDFs
5. If asked about something not in the PDFs, politely explain that you can only answer based on the uploaded documents

PDF CONTENT:
{combined_content}

Remember: Answer ONLY based on the above PDF content."""

    # Prepare messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add chat history if available
    if chat_history:
        messages.extend(chat_history)
    
    # Add current question
    messages.append({"role": "user", "content": question})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=0.3  # Lower temperature for more factual responses
        )
        
        reply = response.choices[0].message.content
        
        # Update chat history
        updated_history = chat_history if chat_history else []
        updated_history.append({"role": "user", "content": question})
        updated_history.append({"role": "assistant", "content": reply})
        
        return reply, updated_history
        
    except Exception as e:
        error_msg = f"Error getting response: {str(e)}"
        return error_msg, chat_history or []

# Streamlit App Configuration
st.set_page_config(
    page_title="PDF-Based AI Assistant", 
    page_icon="📚", 
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .pdf-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .stats-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "pdf_contents" not in st.session_state:
    st.session_state.pdf_contents = {}
if "pdf_chat_history" not in st.session_state:
    st.session_state.pdf_chat_history = []
if "pdf_input_key" not in st.session_state:
    st.session_state.pdf_input_key = 0

# Initialize PDF processor
pdf_processor = PDFProcessor()

# Header
st.title("📚 PDF-Based AI Assistant")
st.markdown("Upload multiple PDFs and ask questions based on their content!")

# Sidebar
with st.sidebar:
    st.header("📁 PDF Management")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="Upload one or more PDF files to analyze"
    )
    
    # Process uploaded files
    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Check if file is already processed
            file_hash = pdf_processor.get_file_hash(uploaded_file)
            cached_data = pdf_processor.load_cached_content(file_hash)
            
            if cached_data:
                st.session_state.pdf_contents[uploaded_file.name] = cached_data['content']
                status_text.text(f"✅ Loaded from cache: {uploaded_file.name}")
            else:
                # Extract text
                extracted_text = pdf_processor.extract_text_from_pdf(uploaded_file)
                if extracted_text:
                    st.session_state.pdf_contents[uploaded_file.name] = extracted_text
                    # Cache the content
                    pdf_processor.cache_pdf_content(file_hash, extracted_text, uploaded_file.name)
                    status_text.text(f"✅ Processed: {uploaded_file.name}")
                else:
                    status_text.text(f"❌ Failed to process: {uploaded_file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("✅ All files processed!")
        st.success(f"Successfully processed {len(st.session_state.pdf_contents)} PDF files!")
    
    # Display loaded PDFs
    if st.session_state.pdf_contents:
        st.markdown("### 📋 Loaded Documents")
        for filename, content in st.session_state.pdf_contents.items():
            word_count = len(content.split())
            st.markdown(f"""
            <div class="pdf-card">
                <strong>📄 {filename}</strong><br>
                <small>{word_count:,} words extracted</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear all PDFs button
        if st.button("🗑️ Clear All PDFs", type="secondary"):
            st.session_state.pdf_contents = {}
            st.session_state.pdf_chat_history = []
            st.session_state.pdf_input_key += 1
            st.rerun()
    
    # Statistics
    if st.session_state.pdf_contents:
        st.markdown("### 📊 Document Statistics")
        total_words = sum(len(content.split()) for content in st.session_state.pdf_contents.values())
        total_chars = sum(len(content) for content in st.session_state.pdf_contents.values())
        
        st.markdown(f"""
        <div class="stats-card">
            <h4>{len(st.session_state.pdf_contents)} Documents</h4>
            <p>{total_words:,} Total Words</p>
            <p>{total_chars:,} Total Characters</p>
        </div>
        """, unsafe_allow_html=True)

# Main content area
if not st.session_state.pdf_contents:
    # Welcome screen
    st.markdown("""
    <div class="upload-section">
        <h2 style="color: white; text-align: center;">📚 Welcome to PDF-Based AI Assistant</h2>
        <p style="color: white; text-align: center; font-size: 1.2em;">
            Upload your PDF documents and start asking questions based on their content!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 How to Get Started:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 1️⃣ Upload PDFs
        - Use the sidebar to upload one or more PDF files
        - Supported formats: PDF only
        - Multiple files can be processed at once
        """)
    
    with col2:
        st.markdown("""
        #### 2️⃣ Ask Questions
        - Ask specific questions about the content
        - The AI will answer based only on uploaded PDFs
        - Get precise, document-based responses
        """)
    
    with col3:
        st.markdown("""
        #### 3️⃣ Explore Content
        - View document statistics
        - See which files are loaded
        - Clear and reload documents anytime
        """)
    
    st.markdown("### 💡 Example Questions:")
    examples = [
        "What is the main topic discussed in the documents?",
        "Can you summarize the key points from the PDFs?",
        "What conclusions are drawn in the documents?",
        "Are there any specific recommendations mentioned?",
        "What data or statistics are provided?"
    ]
    
    for example in examples:
        st.markdown(f"• {example}")

else:
    # Chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 💬 Ask Questions About Your PDFs")
        
        # Warning about PDF-only responses
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Important:</strong> This AI assistant will only answer questions based on the content of your uploaded PDF documents. 
            If information is not available in the PDFs, the assistant will clearly state so.
        </div>
        """, unsafe_allow_html=True)
        
        # Display chat history
        if st.session_state.pdf_chat_history:
            for message in st.session_state.pdf_chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(message['content'])
        
        # Chat input
        with st.form(key="pdf_chat_form", clear_on_submit=True):
            user_question = st.text_area(
                "Ask a question about your PDFs:",
                placeholder="e.g., What are the main findings in the documents?",
                key=f"pdf_input_{st.session_state.pdf_input_key}",
                height=100
            )
            
            col_send, col_examples = st.columns([1, 3])
            
            with col_send:
                submit_button = st.form_submit_button("Ask Question 🚀", type="primary")
            
            with col_examples:
                example_questions = [
                    "Summarize the main points",
                    "What conclusions are drawn?",
                    "Any recommendations mentioned?"
                ]
                
                selected_example = st.selectbox(
                    "Or try an example:",
                    [""] + example_questions
                )
                
                if selected_example and st.form_submit_button("Use Example", type="secondary"):
                    user_question = selected_example
                    submit_button = True
        
        # Process question
        if submit_button and user_question and user_question.strip():
            with st.spinner("🔍 Searching through your PDFs..."):
                try:
                    response, updated_history = get_pdf_based_response(
                        user_question,
                        st.session_state.pdf_contents,
                        st.session_state.pdf_chat_history
                    )
                    st.session_state.pdf_chat_history = updated_history
                    st.session_state.pdf_input_key += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        # Quick actions and info
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Clear Chat History", type="secondary"):
            st.session_state.pdf_chat_history = []
            st.session_state.pdf_input_key += 1
            st.rerun()
        
        # Chat statistics
        st.markdown("### 📈 Chat Stats")
        total_messages = len(st.session_state.pdf_chat_history)
        user_messages = len([m for m in st.session_state.pdf_chat_history if m["role"] == "user"])
        
        st.metric("Total Messages", total_messages)
        st.metric("Questions Asked", user_messages)
        
        # Tips
        st.markdown("### 💡 Tips")
        st.info("""
        **Best Practices:**
        - Ask specific questions about the content
        - Reference specific topics or sections
        - Ask for summaries or key points
        - Request comparisons between documents
        """)
        
        st.markdown("### 🎯 Example Queries")
        st.markdown("""
        - "What is the methodology described?"
        - "List the main recommendations"
        - "Compare findings across documents"
        - "What evidence supports the conclusions?"
        """)

# Footer
st.markdown("---")
st.markdown("""
**Note:** This assistant only provides information based on the uploaded PDF documents. 
For questions outside the scope of your documents, please consult other sources.
""")