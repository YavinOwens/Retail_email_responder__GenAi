import pandas as pd 
import streamlit as st
import os
from ollama import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ollama_api_key = os.getenv("ollama_api_key")
ollama_url = os.getenv("ollama_url", "https://ollama.com")  # base URL for cloud

st.set_page_config(
    page_title="email responder", 
    page_icon="envelope", 
    layout="wide"
)

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

    _This app leverages the Ollama Cloud API to generate email responses._

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

def generate_response(customer_email_body: str) -> str:
    """Generate a response using Ollama Cloud API via Python client."""
    try:
        if not ollama_api_key:
            return "Error: OLLAMA_API_KEY not configured. Please set it in your .env file."

        # Configure client for cloud: host + Authorization header
        client = Client(
            host=ollama_url,
            headers={"Authorization": f"Bearer {ollama_api_key}"}
        )

        response = client.chat(
            model="gpt-oss:120b-cloud",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly and professional customer service agent. "
                        "Generate a concise, helpful response to the customer's email."
                    ),
                },
                {
                    "role": "user",
                    "content": customer_email_body,
                },
            ],
            stream=True,
        )

        # Newer client returns dict parts; access message content
        # GitHub docs show `part['message']['content']` for streamed, `response['message']['content']` for non-stream.[web:39][web:17]
        return response["message"]["content"].strip()

    except Exception as e:
        msg = str(e)
        if "Connection refused" in msg or "ECONNREFUSED" in msg:
            return "Error: Connection refused. Check internet connectivity and ollama_url."
        if "401" in msg or "Unauthorized" in msg:
            return "Error: Authentication failed. Check OLLAMA_API_KEY."
        if "404" in msg or "not found" in msg:
            return "Error: Model 'gpt-oss:120b-cloud' not found."
        return f"Error generating response: {msg}"


def send_email_simulation(to_email: str, subject: str, body: str):
    """Simulate sending email (smoke test only - no actual email sent)."""
    try:
        if not to_email or not subject or not body:
            return False, "Missing required email fields."

        import time
        time.sleep(0.5)  # simulate network delay

        return True, f"[SIMULATION] Email sent successfully to {to_email}!"

    except Exception as e:
        return False, f"Simulation error: {str(e)}"


def save_to_history(customer_name, customer_email, customer_body, generated_response):
    """Save email interaction to history."""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_body": customer_body,
        "generated_response": generated_response,
    }
    st.session_state.response_history.append(entry)


# Response generation section
if st.button("Generate Response", key="generate_response_button"):
    if not customer_email_body.strip():
        st.error("Please enter the customer's email first.")
    else:
        with st.spinner("Generating response..."):
            response = generate_response(customer_email_body)
            st.session_state.current_response = response

# Display and edit response
if st.session_state.current_response:
    st.subheader("Generated Response")
    edited_response = st.text_area(
        "Review and edit the response below",
        key="response",
        value=st.session_state.current_response,
        height=200,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Save to History", use_container_width=True):
            if customer_name and customer_email:
                save_to_history(
                    customer_name, customer_email, customer_email_body, edited_response
                )
                st.success("Response saved to history!")
            else:
                st.error("Please enter customer name and email.")

    with col2:
        if st.button("Send Response", key="send_response_button", use_container_width=True, type="primary"):
            if not customer_email:
                st.error("Please enter customer email address.")
            else:
                with st.spinner("Sending email..."):
                    success, message = send_email_simulation(
                        to_email=customer_email,
                        subject=f"Re: Your Email - {customer_name}",
                        body=edited_response,
                    )
                    if success:
                        st.success(message)
                        save_to_history(
                            customer_name, customer_email, customer_email_body, edited_response
                        )
                        st.session_state.current_response = ""
                        st.rerun()
                    else:
                        st.error(message)

    with col3:
        if st.button("Clear", use_container_width=True):
            st.session_state.current_response = ""
            st.rerun()

# History and Export tabs
st.divider()
tabs = st.tabs(["View Response History", "Export Response History"])

with tabs[0]:
    st.subheader("Response History")

    if st.session_state.response_history:
        for idx, entry in enumerate(st.session_state.response_history):
            with st.expander(f"{entry['customer_name']} - {entry['timestamp']}", expanded=False):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.write(f"**Customer Email:** {entry['customer_email']}")
                    st.write("**Customer Message:**")
                    st.text(entry["customer_body"])
                    st.write("**Your Response:**")
                    st.text(entry["generated_response"])

                with col2:
                    if st.button("Delete", key=f"delete_{idx}", use_container_width=True):
                        st.session_state.response_history.pop(idx)
                        st.rerun()

        st.info(f"Total responses: {len(st.session_state.response_history)}")
    else:
        st.info("No responses in history yet. Generate and save some responses to see them here.")

with tabs[1]:
    st.subheader("Export Response History")

    if st.session_state.response_history:
        df = pd.DataFrame(st.session_state.response_history)

        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"email_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            import io

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Responses")
            buffer.seek(0)

            st.download_button(
                label="Download as Excel",
                data=buffer,
                file_name=f"email_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.write("**Preview:**")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No responses to export yet. Generate and save some responses first.")

st.divider()
st.caption("Email Responder v1.0 | Built with Streamlit and Ollama Cloud [SIMULATION MODE]")
