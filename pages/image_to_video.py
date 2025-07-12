import streamlit as st
import openai
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Disease Progression Video Generation",
    page_icon="🎬",
    layout="wide"
)

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def generate_disease_progression_frames(disease_info, api_key, num_frames=5):
    """Generate frames showing disease progression using DALL-E"""
    try:
        openai.api_key = api_key
        generated_frames = []
        
        # Define progression stages dynamically based on num_frames
        default_stages = [
            "Early stage - initial symptoms barely visible",
            "Mild progression - early signs becoming apparent", 
            "Moderate progression - clear manifestation of symptoms",
            "Advanced stage - significant disease presentation",
            "Severe stage - advanced disease characteristics",
            "Critical stage - life-threatening complications",
            "End-stage - irreversible damage",
            "Terminal stage - palliative care focus"
        ]
        progression_stages = default_stages[:num_frames]

        # Generate frames for each stage
        for i, stage in enumerate(progression_stages):
            prompt = f"""
            Medical illustration of {disease_info['condition']} - {stage}.
            Location: {disease_info['location']}
            
            Style: Professional medical illustration, clinical photography style,
            educational medical content, anatomically accurate, clear visualization,
            medical textbook quality, diagnostic imaging style, healthcare professional standard
            
            Show: {disease_info['visual_characteristics']} at {stage}
            """
            with st.spinner(f"Generating frame {i+1}/{num_frames} - {stage}..."):
                response = openai.images.generate(
                    prompt=prompt,
                    model="dall-e-3",
                    size="1024x1024",
                    quality="hd",
                    style="natural",
                    n=1
                )
                # Download and store the image
                img_url = response.data[0].url
                img_response = requests.get(img_url)
                frame_image = Image.open(io.BytesIO(img_response.content))
                # Add stage label to frame
                frame_with_label = add_stage_label(frame_image, f"Stage {i+1}: {stage}")
                generated_frames.append({
                    'image': frame_with_label,
                    'stage': stage,
                    'stage_number': i+1
                })
        return generated_frames
        
    except Exception as e:
        raise Exception(f"Error generating progression frames: {str(e)}")

def add_stage_label(image, label_text):
    """Add stage label to the image"""
    try:
        # Create a copy of the image
        labeled_image = image.copy()
        draw = ImageDraw.Draw(labeled_image)
        
        # Try to use a default font, fallback to basic font
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_width = draw.textlength(label_text, font=font)
        text_height = 30
        x = 10
        y = 10
        
        # Draw background rectangle for text
        draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill="black", outline="white")
        
        # Draw text
        draw.text((x, y), label_text, fill="white", font=font)
        
        return labeled_image
        
    except Exception as e:
        st.error(f"Error adding label: {str(e)}")
        return image

def create_progression_analysis(disease_info, api_key, model="gpt-4o"):
    """Generate detailed analysis of disease progression"""
    try:
        openai.api_key = api_key
        
        analysis_prompt = f"""
        As a medical education specialist, provide a comprehensive analysis of {disease_info['condition']} progression:

        **Disease:** {disease_info['condition']}
        **Location:** {disease_info['location']}
        **Patient Demographics:** {disease_info.get('demographics', 'General population')}

        Please provide:
        1. **Disease Overview**: Brief description of the condition
        2. **Progression Timeline**: Typical timeline from onset to advanced stages
        3. **Stage-by-Stage Analysis**: Detailed description of each progression stage
        4. **Visual Changes**: How the appearance changes through each stage
        5. **Symptoms Evolution**: How symptoms develop and worsen over time
        6. **Risk Factors**: Factors that accelerate or influence progression
        7. **Intervention Points**: Key stages where treatment can be most effective
        8. **Prognosis**: Expected outcomes at different stages
        9. **Educational Notes**: Important points for patients and healthcare providers

        **Format**: Use clear medical terminology suitable for healthcare professionals while being educational.
        **Disclaimer**: Include appropriate medical disclaimers about individual variation and professional consultation.
        """
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical education specialist with expertise in disease progression and pathology. Provide comprehensive, educational analysis for healthcare professionals and medical students."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Error generating progression analysis: {str(e)}")

def main():
def create_video_from_frames(frames, frame_duration, output_path):
    """Create a video file from a list of PIL Image frames"""
    try:
        # Convert PIL images to numpy arrays
        frame_arrays = [np.array(frame['image'].convert('RGB')) for frame in frames]
        
        # Create video clip
        clip = mpy.ImageSequenceClip(frame_arrays, fps=1/frame_duration)
        
        # Write video file
        clip.write_videofile(output_path, codec='libx264', audio=False)
        
        return output_path
    except Exception as e:
        st.error(f"Error creating video: {str(e)}")
        return None

def main():
    st.title("🎬 Disease Progression Video Generation")
    st.title("🎬 Disease Progression Video Generation")
    st.markdown("Generate educational videos showing disease progression over time for medical education and patient understanding")
    
    # Medical disclaimer
    st.error("""
    ⚠️ **MEDICAL DISCLAIMER**: This tool generates educational content for medical professionals and students. 
    It should NOT be used for self-diagnosis or replace professional medical consultation. 
    Generated content is for educational purposes only and may not reflect individual patient variations.
    """)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("🎬 Video Generation Settings")
        
        # API Key
        default_api_key = os.getenv("OPENAI_API_KEY", "")
        if default_api_key:
            st.success("✅ API key loaded from environment")
            api_key = default_api_key
        else:
            api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
        
        # Model selection
        model = st.selectbox(
            "AI Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            help="Choose the AI model for analysis"
        )
        
        # Video settings
        st.subheader("📹 Video Parameters")
        num_frames = st.slider("Number of Stages", 3, 8, 5, help="Number of progression stages to generate")
        frame_duration = st.slider("Stage Duration (seconds)", 1, 10, 3, help="How long each stage is displayed")
        
        # Disease categories
        st.subheader("🦠 Disease Categories")
        disease_category = st.selectbox(
            "Medical Specialty",
            [
                "Dermatology",
                "Oncology", 
                "Cardiology",
                "Neurology",
                "Ophthalmology",
                "Orthopedics",
                "Pulmonology",
                "Gastroenterology",
                "Infectious Disease",
                "Rheumatology"
            ]
        )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔧 Disease Configuration")
        
        # Pre-defined disease examples
        disease_examples = {
            "Dermatology": {
                "Melanoma Progression": {
                    "condition": "Melanoma",
                    "location": "Skin lesion on back",
                    "visual_characteristics": "Changing mole with irregular borders, color variation, and size increase",
                    "demographics": "Adults 30-70 years"
                },
                "Psoriasis Development": {
                    "condition": "Psoriasis",
                    "location": "Elbow and knee areas",
                    "visual_characteristics": "Red, scaly plaques with silvery scales",
                    "demographics": "Adults 20-50 years"
                }
            },
            "Oncology": {
                "Breast Cancer Progression": {
                    "condition": "Breast Cancer",
                    "location": "Breast tissue",
                    "visual_characteristics": "Tumor growth, tissue changes, lymph node involvement",
                    "demographics": "Women 40-70 years"
                },
                "Lung Cancer Development": {
                    "condition": "Lung Cancer",
                    "location": "Lung tissue - chest X-ray view",
                    "visual_characteristics": "Nodule growth, opacity changes, pleural involvement",
                    "demographics": "Adults 50-80 years"
                }
            },
            "Cardiology": {
                "Atherosclerosis Progression": {
                    "condition": "Atherosclerosis",
                    "location": "Coronary artery",
                    "visual_characteristics": "Plaque buildup, arterial narrowing, calcification",
                    "demographics": "Adults 40-80 years"
                }
            },
            "Ophthalmology": {
                "Diabetic Retinopathy": {
                    "condition": "Diabetic Retinopathy",
                    "location": "Retina - fundus view",
                    "visual_characteristics": "Microaneurysms, hemorrhages, neovascularization",
                    "demographics": "Diabetic patients"
                },
                "Glaucoma Progression": {
                    "condition": "Glaucoma",
                    "location": "Optic nerve head",
                    "visual_characteristics": "Optic disc cupping, nerve fiber layer thinning",
                    "demographics": "Adults over 40"
                }
            }
        }
        
        # Select disease example
        if disease_category in disease_examples:
            disease_options = list(disease_examples[disease_category].keys())
            selected_disease = st.selectbox("Select Disease Example", disease_options)
            disease_info = disease_examples[disease_category][selected_disease]
            
            # Display selected disease info
            st.json(disease_info)
        else:
            disease_info = {
                "condition": "Custom Disease",
                "location": "Specify location",
                "visual_characteristics": "Describe visual changes",
                "demographics": "Target population"
            }
        
        # Custom disease input
        st.subheader("🎯 Custom Disease Configuration")
        
        condition = st.text_input("Disease/Condition", value=disease_info["condition"])
        location = st.text_input("Anatomical Location", value=disease_info["location"])
        visual_characteristics = st.text_area("Visual Characteristics", value=disease_info["visual_characteristics"])
        demographics = st.text_input("Patient Demographics", value=disease_info["demographics"])
        
        # Update disease info
        disease_info = {
            "condition": condition,
            "location": location,
            "visual_characteristics": visual_characteristics,
            "demographics": demographics
        }
        
        # Generate buttons
        st.subheader("🎬 Generation Controls")
        
        col_analysis, col_video = st.columns(2)
        
        with col_analysis:
            if st.button("📊 Generate Analysis", disabled=not api_key):
                if api_key and condition:
                    st.session_state.disease_info = disease_info
                    st.session_state.generate_analysis = True
                else:
                    st.error("Please enter API key and disease information")
        
        with col_video:
            if st.button("🎬 Generate Video Frames", disabled=not api_key):
                if api_key and condition:
                    st.session_state.disease_info = disease_info
                    st.session_state.generate_frames = True
                    st.session_state.num_frames = num_frames
                else:
                    st.error("Please enter API key and disease information")
    
    with col2:
        st.subheader("📹 Disease Progression Results")
        
        # Generate analysis
        if hasattr(st.session_state, 'generate_analysis') and st.session_state.generate_analysis:
            if st.button("📊 Start Analysis Generation"):
                try:
                    with st.spinner("🔬 Generating disease progression analysis..."):
                        analysis = create_progression_analysis(st.session_state.disease_info, api_key, model)
                        st.session_state.progression_analysis = analysis
                        st.session_state.generate_analysis = False
                        st.success("✅ Analysis generated successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Generate video frames
        if hasattr(st.session_state, 'generate_frames') and st.session_state.generate_frames:
            if st.button("🎬 Start Frame Generation"):
                try:
                    frames = generate_disease_progression_frames(
                        st.session_state.disease_info, 
                        api_key, 
                        st.session_state.num_frames
                    )
                    st.session_state.progression_frames = frames
                    st.session_state.generate_frames = False
                    st.success("✅ Video frames generated successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Display analysis
        if hasattr(st.session_state, 'progression_analysis'):
            st.markdown("### 📊 Disease Progression Analysis:")
            with st.expander("View Full Analysis", expanded=True):
                st.markdown(st.session_state.progression_analysis)
            
            # Save analysis
            if st.button("💾 Save Analysis Report"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"disease_progression_analysis_{timestamp}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"DISEASE PROGRESSION ANALYSIS REPORT\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Disease: {st.session_state.disease_info['condition']}\n")
                    f.write(f"Location: {st.session_state.disease_info['location']}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(st.session_state.progression_analysis)
                    f.write(f"\n\n{'='*60}\n")
                    f.write("DISCLAIMER: This is educational content for medical professionals.\n")
                
                st.success(f"📄 Analysis saved as {filename}")
        
        # Display video frames
        if hasattr(st.session_state, 'progression_frames'):
            st.markdown("### 🎬 Disease Progression Frames:")
            
            # Display frames in sequence
            for i, frame_data in enumerate(st.session_state.progression_frames):
                st.markdown(f"**Stage {frame_data['stage_number']}:** {frame_data['stage']}")
                st.image(frame_data['image'], caption=f"Stage {frame_data['stage_number']}", use_column_width=True)
                
                # Download individual frame
                img_buffer = io.BytesIO()
                frame_data['image'].save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"progression_stage_{frame_data['stage_number']}_{timestamp}.png"
                
                st.download_button(
                    label=f"📥 Download Stage {frame_data['stage_number']}",
                    data=img_buffer.getvalue(),
                    file_name=filename,
                    mime="image/png",
                    key=f"download_{i}"
                )
                
                st.markdown("---")
            
            # Video creation instructions
            st.markdown("### 🎬 Create Video:")
            st.info("""
            **To create a video from these frames:**
            1. Download all frames using the buttons above
            2. Use video editing software (e.g., Adobe Premiere, DaVinci Resolve, or free tools like OpenShot)
            3. Import frames in sequence
            4. Set frame duration to your preferred timing
            5. Add transitions between stages
            6. Export as MP4 for sharing
            
            **Suggested video settings:**
            - Frame rate: 1-2 FPS for educational viewing
            - Add fade transitions between stages
            - Include stage labels and timestamps
            - Add narration or background music if desired
            """)
        
        else:
            st.info("🎬 Disease progression frames will appear here")
    
    # Footer with educational information
    st.markdown("---")
    with st.expander("📚 Disease Progression Education Guide"):
        st.markdown("""
        ### 🎓 Educational Applications:
        
        **For Medical Students:**
        - Visual learning of disease progression
        - Understanding pathophysiology timeline
        - Recognizing early vs. late stage presentations
        - Exam preparation with visual aids
        
        **For Healthcare Professionals:**
        - Patient education materials
        - Clinical decision-making support
        - Training and continuing education
        - Research and presentation materials
        
        **For Patients:**
        - Understanding their condition
        - Recognizing progression signs
        - Treatment compliance motivation
        - Informed consent discussions
        
        ### 🏥 Clinical Applications:
        
        **Diagnostic Training:**
        - Pattern recognition across stages
        - Differential diagnosis considerations
        - Imaging interpretation skills
        - Clinical correlation exercises
        
        **Treatment Planning:**
        - Intervention timing decisions
        - Prognosis discussions
        - Monitoring requirements
        - Outcome expectations
        
        ### 🔬 Research Applications:
        - Disease modeling visualization
        - Progression timeline studies
        - Treatment efficacy demonstration
        - Educational material development
        
        ### ⚠️ Important Notes:
        - Individual progression may vary significantly
        - Multiple factors influence disease course
        - Professional medical evaluation essential
        - Not all diseases follow predictable patterns
        """)

if __name__ == "__main__":
    main()