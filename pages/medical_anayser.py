import streamlit as st
import openai
import requests
from PIL import Image
import io
import os
import base64
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Medical Image Analyzer",
    page_icon="🏥",
    layout="wide"
)

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def analyze_medical_image(image, analysis_type, api_key, model="gpt-4o"):
    """Analyze medical image using OpenAI's vision model"""
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image)
        openai.api_key = api_key

        medical_prompts = {
            "general_analysis": """
            As a medical AI assistant, analyze this medical image and provide:
            1. **Visual Observations**: What do you see in the image?
            2. **Potential Conditions**: What medical conditions could this indicate?
            3. **Symptoms to Look For**: What symptoms should be monitored?
            4. **Recommended Actions**: What should the healthcare provider consider?
            5. **Urgency Level**: How urgent is this case?

            IMPORTANT: This is for educational/assistance purposes only. Always consult with qualified medical professionals for diagnosis and treatment.
            """,
            "skin_analysis": """
            Analyze this skin/dermatological image as a medical AI assistant:
            1. **Skin Lesion Assessment**: Describe the appearance, size, color, texture
            2. **Potential Skin Conditions**: List possible dermatological conditions
            3. **ABCDE Analysis**: If applicable, assess Asymmetry, Border, Color, Diameter, Evolution
            4. **Risk Factors**: Identify any concerning features
            5. **Recommendations**: Suggest next steps for evaluation

            DISCLAIMER: This is not a substitute for professional dermatological examination.
            """,
            "xray_analysis": """
            As a medical AI assistant, analyze this X-ray/radiological image:
            1. **Image Quality**: Comment on image clarity and positioning
            2. **Anatomical Structures**: Identify visible structures
            3. **Abnormal Findings**: Note any abnormalities or concerning features
            4. **Possible Conditions**: Suggest potential diagnoses to consider
            5. **Additional Imaging**: Recommend if other imaging might be needed

            IMPORTANT: Radiological interpretation requires specialized training. This is for educational support only.
            """,
            "eye_analysis": """
            Analyze this ophthalmological image as a medical AI assistant:
            1. **Eye Structure Assessment**: Describe visible eye structures
            2. **Abnormalities**: Note any visible abnormalities or lesions
            3. **Potential Eye Conditions**: List possible ocular conditions
            4. **Symptoms to Monitor**: What symptoms should be watched for
            5. **Specialist Referral**: When to refer to ophthalmologist

            DISCLAIMER: Eye conditions require professional ophthalmological evaluation.
            """,
            "wound_analysis": """
            As a medical AI assistant, analyze this wound/injury image:
            1. **Wound Assessment**: Describe type, size, depth, and appearance
            2. **Healing Stage**: Assess current healing phase
            3. **Infection Signs**: Look for signs of infection or complications
            4. **Treatment Considerations**: Suggest wound care approaches
            5. **Monitoring**: What to watch for during healing

            IMPORTANT: Wound care requires proper medical evaluation and treatment.
            """,
            "symptom_analysis": """
            Analyze this medical symptom image as a medical AI assistant:
            1. **Symptom Description**: Describe what you observe
            2. **Possible Causes**: List potential underlying causes
            3. **Associated Symptoms**: What other symptoms might be present
            4. **Severity Assessment**: Evaluate the severity level
            5. **Medical Attention**: When to seek immediate medical care

            DISCLAIMER: Symptoms require proper medical evaluation for accurate diagnosis.
            """
        }

        prompt = medical_prompts.get(analysis_type, medical_prompts["general_analysis"])

        # Use the new OpenAI API for chat completions
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical AI assistant designed to help healthcare professionals analyze medical images. Provide detailed, structured analysis while emphasizing the importance of professional medical consultation. Always include disclaimers about the limitations of AI analysis."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )

        # The new API returns content in response.choices[0].message.content or response.choices[0].content
        result_content = None
        if hasattr(response.choices[0], "message") and hasattr(response.choices[0].message, "content"):
            result_content = response.choices[0].message.content
        elif hasattr(response.choices[0], "content"):
            result_content = response.choices[0].content
        else:
            result_content = str(response)
        return result_content
    except Exception as e:
        raise Exception(f"Error analyzing medical image: {str(e)}")

def main():
    st.title("🏥 Medical Image Analyzer")
    st.markdown("AI-powered medical image analysis to assist healthcare professionals in identifying potential conditions and recommendations")
    
    # Medical disclaimer
    st.error("""
    ⚠️ **MEDICAL DISCLAIMER**: This tool is designed to assist healthcare professionals and is for educational purposes only. 
    It should NOT replace professional medical diagnosis, treatment, or consultation. Always consult qualified healthcare providers for medical decisions.
    """)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Medical Analysis Settings")
        
        # API Key input
        default_api_key = os.getenv("OPENAI_API_KEY", "")
        if default_api_key:
            st.success("✅ API key loaded from environment")
            api_key = default_api_key
        else:
            api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
        
        # Model selection
        model = st.selectbox(
            "AI Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview"],
            help="Choose the OpenAI vision model for analysis"
        )
        
        # Medical analysis type
        analysis_type = st.selectbox(
            "Medical Analysis Type",
            [
                "general_analysis",
                "skin_analysis", 
                "xray_analysis",
                "eye_analysis",
                "wound_analysis",
                "symptom_analysis"
            ],
            format_func=lambda x: {
                "general_analysis": "🔍 General Medical Analysis",
                "skin_analysis": "🧴 Dermatological Analysis",
                "xray_analysis": "📷 X-ray/Radiological Analysis", 
                "eye_analysis": "👁️ Ophthalmological Analysis",
                "wound_analysis": "🩹 Wound Assessment",
                "symptom_analysis": "🔬 Symptom Analysis"
            }[x]
        )
        
        # Analysis confidence level
        st.subheader("Analysis Settings")
        detailed_analysis = st.checkbox("Detailed Analysis", value=True, help="Provide comprehensive analysis")
        include_urgency = st.checkbox("Include Urgency Assessment", value=True, help="Assess urgency level")
        
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload Medical Image")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Medical Image",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
            help="Upload medical images: X-rays, skin photos, eye images, wounds, etc."
        )
        
        # Sample medical images (for demo purposes)
        st.markdown("**Demo Images (For Testing Only):**")
        sample_images = {
            "Sample Skin Lesion": "https://images.unsplash.com/photo-1559757175-3dfc3c8e7e88?w=400",
            "Sample X-ray": "https://images.unsplash.com/photo-1559757175-7c8e7e88?w=400",
            "Sample Eye": "https://images.unsplash.com/photo-1574279606130-09958dc756c3?w=400",
            "Sample Wound": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=400"
        }
        
        sample_choice = st.selectbox("Demo Images", list(sample_images.keys()))
        if st.button("Use Demo Image"):
            st.session_state.sample_image_url = sample_images[sample_choice]
            st.warning("⚠️ This is a demo image for testing purposes only")
        
        # Display uploaded or sample image
        image_to_analyze = None
        
        if uploaded_file is not None:
            image_to_analyze = Image.open(uploaded_file)
            st.image(image_to_analyze, caption="Medical Image for Analysis", use_column_width=True)
            
            # Image info
            st.info(f"📊 Image Info: {image_to_analyze.size[0]}x{image_to_analyze.size[1]} pixels, Format: {image_to_analyze.format}")
            
        elif hasattr(st.session_state, 'sample_image_url'):
            try:
                response = requests.get(st.session_state.sample_image_url)
                image_to_analyze = Image.open(io.BytesIO(response.content))
                st.image(image_to_analyze, caption="Demo Medical Image", use_column_width=True)
            except Exception as e:
                st.error(f"Error loading demo image: {str(e)}")
        
        # Analyze button
        if st.button("🔍 Analyze Medical Image", type="primary", disabled=not (api_key and image_to_analyze is not None)):
            if not api_key:
                st.error("Please enter your OpenAI API key")
            elif image_to_analyze is None:
                st.error("Please upload a medical image")
            else:
                st.session_state.analysis_image = image_to_analyze
                st.session_state.analysis_type = analysis_type
                st.session_state.analysis_model = model
    
    with col2:
        st.subheader("📋 Medical Analysis Results")
        
        # Perform analysis if requested
        if hasattr(st.session_state, 'analysis_image'):
            if st.button("🔍 Start Analysis", key="analyze_btn"):
                try:
                    with st.spinner("🔬 Analyzing medical image... This may take up to 30 seconds"):
                        result = analyze_medical_image(
                            st.session_state.analysis_image,
                            st.session_state.analysis_type,
                            api_key,
                            st.session_state.analysis_model
                        )
                        
                        st.session_state.analysis_result = result
                        st.success("✅ Medical analysis complete!")
                        
                except Exception as e:
                    st.error(f"❌ Analysis Error: {str(e)}")
        
        # Display results
        if hasattr(st.session_state, 'analysis_result'):
            st.markdown("### 🏥 Medical Analysis Report:")
            
            # Display analysis in a formatted way
            with st.container():
                st.markdown(st.session_state.analysis_result)
            
            # Action buttons
            col_save, col_copy, col_print = st.columns(3)
            
            with col_save:
                if st.button("💾 Save Report"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"medical_analysis_{timestamp}.txt"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"MEDICAL IMAGE ANALYSIS REPORT\n")
                        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Analysis Type: {st.session_state.analysis_type}\n")
                        f.write(f"AI Model: {st.session_state.analysis_model}\n")
                        f.write(f"{'='*50}\n\n")
                        f.write(st.session_state.analysis_result)
                        f.write(f"\n\n{'='*50}\n")
                        f.write("DISCLAIMER: This analysis is for educational/assistance purposes only. ")
                        f.write("Always consult qualified healthcare professionals for medical decisions.\n")
                    
                    st.success(f"📄 Report saved as {filename}")
            
            with col_copy:
                if st.button("📋 Copy Analysis"):
                    st.code(st.session_state.analysis_result, language="text")
                    st.info("💡 Analysis displayed above - you can select and copy it")
            
            with col_print:
                if st.button("🖨️ Print View"):
                    st.markdown("---")
                    st.markdown("**PRINTABLE MEDICAL ANALYSIS REPORT**")
                    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Analysis Type:** {st.session_state.analysis_type}")
                    st.markdown("---")
                    st.markdown(st.session_state.analysis_result)
                    st.markdown("---")
                    st.markdown("**DISCLAIMER:** This analysis is for educational/assistance purposes only.")
        
        else:
            st.info("🔬 Medical analysis results will appear here after analyzing an image")
    
if __name__ == "__main__":
    main()