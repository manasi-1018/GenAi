import streamlit as st
import openai
import requests
from PIL import Image
import io
import os
from datetime import datetime
from dotenv import load_dotenv

#Load Emnironemnt 
load_dotenv()

#Configure Page
st.set_page_config(page_title="AI Image Generator Hub",
                   page_icon="+^",
                   layout="wide"
                   )

#Title and Description
st.title("AI Image Generator")
st.markdown("Generate Stunning images from text describtion using OpenAI's DALLE-E Model")

st.sidebar.header("Settings")

#API Key Input - Check Environment Variable First 
default_api_key = os.getenv("OPENAI_API_KEY", "")
if default_api_key:
    st.sidebar.success("API Key Loaded from the Environment")
    api_key = default_api_key
else:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter Your OpenAI API Key")

if api_key:
    openai.api_key = api_key

    #Image Generator Paramete
    st.sidebar.subheader("Generate Parameter")
    #Model Selection
    model = st.sidebar.selectbox(
        "Model",
        ["dall-e-3", "dalle-e-2"],
        help="Choose the DALL-E Model Version"
    )

    #Image Size
    if model == "dall-e-3":
        size_option = ["1024x1024", "1024x1792", "1792x1024"]
    else:
        size_option = ["256x256", "512x512", "1024x1024"]

    size = st.sidebar.selectbox("Image Size", size_option)

    #Quality (Only for Dall_E 3)
    if model == "dall-e-3":
        quality = st.sidebar.selectbox("Quality", ["standard","hd"])
    else:
        quality = "standard"

    #Style (Only For DALLE 3)
    if model == "dall-e-3":
        style = st.sidebar.selectbox("Style", ["vivid","natural"])
    else:
        style = "natural"

    if model == "dall-e-2":
        n_images = st.sidebar.slider("Number of Images", 1,4,1)
    else:
        n_images = 1

#Main Content Area

col1, col2 = st.columns([1,1])

with col1:
    st.subheader("Text Prompt")

    #Sample Prompts
    st.markdown("** Quick Start - Sample Prompts:**")
    sample_prompts = {
    "MRI": [
        "A real-world MRI scan showing the detailed structure of a human brain, highlighting the gray and white matter",
        "An MRI image of a knee joint with clear visualization of the ligaments, bones, and cartilage",
        "A high-resolution MRI scan of the spine showing detailed intervertebral discs and spinal cord"
    ],
    "CT Scan": [
        "A real-world CT scan of a human chest showing the lungs, heart, and blood vessels with clear delineation",
        "A CT scan of the abdominal area, displaying the liver, kidneys, and intestines with clear contrast",
        "A 3D reconstruction from a CT scan of the brain, showing the detailed structure of the skull and brain tissue"
    ],
    "X-ray": [
        "A real-world X-ray image of a fractured femur, showing the break clearly and the bone alignment",
        "An X-ray of a human hand showing the bone structure, with a clear view of fractures in the metacarpals",
        "A full-body X-ray revealing the skeletal structure of a person with emphasis on the spine and ribs"
    ]
    }

    selected_category = st.selectbox("Category",list(sample_prompts.keys()))
    selected_prompts = st.selectbox("Sample Prompt",sample_prompts[selected_category])

    if st.button("Use this Prompt"):
        st.session_state.prompt_text = selected_prompts

    # text input
    prompt = st.text_area(
        "Custom Prompt:",
        value= st.session_state.get("prompt_text",""),
        placeholder="A scene landscape with mountain, a lake and a sunset sky",
        height=150
    )

    #Generate Button
    if st.button("Generate Image",type="primary", disabled=not(api_key and prompt)):
        if not api_key:
            st.error("Please enter your OpenAI key in the sidebar")
        elif not prompt:
            st.error("Please enter a text prompt")
        else:
            try:
                with st.spinner("Generating image ... This may take a few seconds"):
                    response = openai.images.generate(
                        prompt=prompt,
                        model=model,
                        n=n_images,
                        size=size,
                        quality=quality if model == "dall-e-3" else None,
                        style=style if model == "dall-e-3" else None,
                        response_format="url"
                    )
                    #store Generated Images in session state
                    st.session_state.generated_images = response.data
                    st.session_state.current_prompt = prompt
                    st.success("Image generated successfully!")
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
with col2:
    st.subheader("Generated Images")

    #displaying generated imnages
    if hasattr(st.session_state,"generated_images") and st.session_state.generated_images:
        for i, image_data in enumerate(st.session_state.generated_images):
            try:
                #download and display image
                image_response = requests.get(image_data.url)
                image = Image.open(io.BytesIO(image_response.content))
                st.image(image, caption=f"Generated Image {i+1}", use_column_width=True)
                #download image
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_image_{timestamp}_{i+1}.png"
                st.download_button(
                    label=f"Download Image",
                    data=img_buffer.getvalue(),
                    file_name=filename,
                    mime="image/png"
                )

                #show prompt used
                if hasattr(st.session_state, "current_prompt"):
                    st.caption(f"Prompt: {st.session_state.current_prompt}")
                

            except Exception as e:
                st.error(f"Error displaying image {i+1}: {str(e)}")

    else:
        st.info("Generated images will appear here")
        