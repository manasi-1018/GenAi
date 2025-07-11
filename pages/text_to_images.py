import streamlit as st
import openai
import requests
from PIL import Image
import io 
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(page_title="AI Image Generator Hub",
                   page_icon="+",
                   layout="wide"
                   )

#Title and Description
st.title("AI Image Generator")
st.markdown("Generate Stunning images from text describition using OpenAI's from Dall-E-Model")

st.sidebar.header("Settings")

#API key Input - Check envvironment variable First
default_api_key = os.getenv("OPENAI_API_KEY","")
if default_api_key :
    st.sidebar.success("API key is loaded from the evironmnet")
    api_key = default_api_key
else:
    api_key = st.sidebar.text_input("OpenAI ",type="password",help="Enter your OpenAI API key ")

if api_key:
    openai.api_key = api_key

    #Image generator parameter
    st.sidebar.subheader("Generate Parameter")
    #Model Selection
    model = st.sidebar.selectbox(
        "Model",
        ["dall-e-3","dall-e-2"],
        help = "Choose the DALL-E Model Version"

    )

    #Image size
    if model == "dall-e-3":
        size_option = ["1024x1024","1024x1792","1792x1024"]
    else:
        size_option = ["256x256","512x512","1024x1024"]

    size = st.sidebar.selectbox("Image Size",size_option)

    #Image Quality (only for dall-e-3)
    if model == "dall-e-3":
        quality = st.sidebar.selectbox("Quality",["standard","HD"])
    else:
        quality = "standard"

    #Style(only for dall-e-3)
    if model == "dall-e-3":
        style = st.sidebar.selectbox("Style",["natural","vivid"])
    else:
        style= "natural"

    if model == "dall-e-2":
        n_images = st.sidebar.slider("Number of images",1,4,1)
    else:
        n_images = 1
    
#main content area
col1,col2 = st.columns([1,1])

with col1:
    st.subheader("Text Prompt")