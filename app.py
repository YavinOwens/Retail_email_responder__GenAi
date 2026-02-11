import pandas as pd 
import streamlit as st
import os
import ollama
from dotenv import load_dotenv

load_dotenv()

ollama_api_key = os.getenv("ollama_api_key")
ollama_url = os.getenv("ollama_url")


st.set_page_config(
    page_title="email responder", 
    page_icon=":email:", 
    layout="wide")
st.header("Email Responder")
st.markdown(
    """
    This application is designed to help you respond to customer emails efficiently.  
    - Input the customer's name and email address.  
    - The application will generate a suggested response to the customer's email.  
    - You can review and edit the generated response as needed.  
    - Once satisfied, you can send the response directly to the customer.  
    - View a history of all generated responses.  
    - Delete individual responses from your history if needed.  
    - Export your response history to a file for further use.

    _This app leverages the Ollama API to generate email responses._

    **Please note:** This application is currently in development and not yet ready for production use.
    """
)

if "response_history" not in st.session_state:
    st.session_state.response_history = []

if "current_response" not in st.session_state:
    st.session_state.current_response = ""


# Input section
st.subheader("Customer Email Details")
col1, col2 = st.columns(2)

with col1:
    customer_name = st.text_input("Enter the customer's name", key="customer_name")

with col2:
    customer_email = st.text_input("Enter the customer's email address", key="customer_email")

customer_email_body = st.text_area(
    "Enter the customer's email", 
    key="customer_email_body", 
    height=300,
    placeholder="Enter the customer's email here..."
)

def generate_response(customer_email_body):
    response = ollama.generate(
        model="gpt-oss:120B-cloud",
        prompt=f"Youre a friendly customer service agent. Generate a response to the following email: {customer_email_body}",
        temperature=0.5,
        max_tokens=1000,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

if st.button("Generate Response", key="generate_response_button"):
    response = generate_response(customer_email_body)
    st.text_area("Enter the response", key="response", value=response)



st.text_area("Enter the response", key="response")

st.button("Send Response", key="send_response_button")


tabs = st.tabs(["View Response History", "Export Response History"])
with tabs[0]:
    st.write("Response history will be shown here.")
    # st.button("Delete Response History")
with tabs[1]:
    st.write("Export your response history here.")