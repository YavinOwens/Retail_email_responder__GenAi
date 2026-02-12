import pandas as pd
import streamlit as st
import os
from ollama import Client
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


ollama_api_key = os.getenv("ollama_api_key")
ollama_url = os.getenv("ollama_url", "https://ollama.com")


st.set_page_config(
    page_title="School Registrar", 
    page_icon="🎓", 
    layout="wide"
)


st.header("📚 Student Registrar Communication Portal")
st.markdown(
    """
    A comprehensive platform for teachers and parents to communicate about student attendance, progress, and school matters.
    
    **Features:**
    - 📋 **Attendance Overview**: View student attendance records with detailed lesson tracking
    - 💬 **Communication Hub**: Generate professional messages to parents/guardians
    - 📊 **Attendance Reports**: Export attendance data and communication logs
    - 🔍 **Student Records**: Access individual student information and attendance history
    - 📞 **Parent Engagement**: Track communication with families regarding attendance
    
    _This application leverages the Ollama Cloud API to generate contextual messages._
    
    **Note:** Demo mode - uses sample data for development and testing.
    """
)


# Load CSV data
@st.cache_data
def load_data():
    try:
        students = pd.read_csv("data/teachingsassistant_data/students.csv")
        attendance = pd.read_csv("data/teachingsassistant_data/attendance.csv")
        lessons = pd.read_csv("data/teachingsassistant_data/lessons.csv")
        return students, attendance, lessons
    except FileNotFoundError:
        st.error("CSV files not found. Please ensure students.csv, attendance.csv, and lessons.csv are in the 'data' folder.")
        return None, None, None


students_df, attendance_df, lessons_df = load_data()


if students_df is not None:
    
    if "message_history" not in st.session_state:
        st.session_state.message_history = []
    
    
    if "current_message" not in st.session_state:
        st.session_state.current_message = ""
    
    
    # ==================== MESSAGE GENERATION SECTION ====================
    st.divider()
    st.subheader("💬 Generate Communication Message")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Select student
        student_names = [f"{row['FirstName']} {row['LastName']} (ID: {row['StudentID']})" 
                         for _, row in students_df.iterrows()]
        selected_student_name = st.selectbox("Select Student", options=student_names, key="student_select")
        
        # Extract student ID from selection
        student_id = int(selected_student_name.split("ID: ")[1].rstrip(")"))
        student_info = students_df[students_df['StudentID'] == student_id].iloc[0]
    
    with col2:
        # Select recipient
        recipient_type = st.radio("Message Recipient", options=["Parent/Guardian", "Student", "Internal Note"], 
                                  horizontal=True, key="recipient_type")
    
    
    # Get student's recent attendance
    student_attendance = attendance_df[attendance_df['StudentID'] == student_id].tail(20)
    attendance_rate = (student_attendance['Attended'].sum() / len(student_attendance) * 100) if len(student_attendance) > 0 else 0
    
    st.info(f"📊 **{student_info['FirstName']} {student_info['LastName']}** | Class: {student_info['Class']} | Recent Attendance Rate: {attendance_rate:.1f}%")
    
    
    # Message context
    message_type = st.selectbox(
        "Message Type",
        options=[
            "Attendance Concern",
            "Positive Attendance Recognition",
            "Follow-up on Absence",
            "Attendance Improvement Notice",
            "General Communication",
            "Punctuality Notice"
        ],
        key="message_type"
    )
    
    
    # Additional context
    additional_context = st.text_area(
        "Additional Context (Optional)",
        key="additional_context",
        height=150,
        placeholder="Add any specific details, concerns, or observations about the student's attendance or behavior..."
    )
    
    
    def generate_message(student_name: str, student_class: str, attendance_rate: float, 
                        message_type: str, recipient_type: str, context: str) -> str:
        """Generate a message using Ollama Cloud API."""
        try:
            if not ollama_api_key:
                return "Error: OLLAMA_API_KEY not configured. Please set it in your .env file."
            
            
            client = Client(
                host=ollama_url,
                headers={"Authorization": f"Bearer {ollama_api_key}"}
            )
            
            
            prompt = f"""
            You are a professional school administrator and teacher. Generate an appropriate {message_type.lower()} message.
            
            **Student Information:**
            - Name: {student_name}
            - Class: {student_class}
            - Recent Attendance Rate: {attendance_rate:.1f}%
            
            **Message Type:** {message_type}
            **Recipient:** {recipient_type}
            
            **Additional Context:** {context if context else "None provided"}
            
            Generate a professional, empathetic, and constructive message suitable for a school setting.
            Keep it concise (2-3 paragraphs) and appropriate for the recipient type.
            """
            
            response = client.chat(
                model="gpt-oss:120b-cloud",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful school communication assistant. Generate professional, empathetic messages for teachers and parents regarding student attendance and progress.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=True,
            )
            
            
            # Accumulate streamed response
            full_response = ""
            for chunk in response:
                if isinstance(chunk, dict) and "message" in chunk:
                    full_response += chunk["message"].get("content", "")
            
            return full_response.strip()
        
        except Exception as e:
            msg = str(e)
            if "Connection refused" in msg or "ECONNREFUSED" in msg:
                return "Error: Connection refused. Check internet connectivity and ollama_url."
            if "401" in msg or "Unauthorized" in msg:
                return "Error: Authentication failed. Check OLLAMA_API_KEY."
            if "404" in msg or "not found" in msg:
                return "Error: Model 'gpt-oss:120b-cloud' not found."
            return f"Error generating message: {msg}"
    
    
    # Generate message button
    if st.button("🔄 Generate Message", key="generate_message_button", use_container_width=True):
        if not student_id:
            st.error("Please select a student.")
        else:
            with st.spinner("Generating message..."):
                message = generate_message(
                    student_name=f"{student_info['FirstName']} {student_info['LastName']}",
                    student_class=student_info['Class'],
                    attendance_rate=attendance_rate,
                    message_type=message_type,
                    recipient_type=recipient_type,
                    context=additional_context
                )
                st.session_state.current_message = message
    
    
    # ==================== MESSAGE REVIEW & ACTIONS ====================
    if st.session_state.current_message:
        st.divider()
        st.subheader("✏️ Review & Edit Message")
        
        edited_message = st.text_area(
            "Edit message if needed:",
            key="message_edit",
            value=st.session_state.current_message,
            height=250,
        )
        
        
        def save_to_message_history(student_id, student_name, student_class, message_type, 
                                   recipient_type, generated_message, attendance_rate):
            """Save communication to history."""
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "student_id": student_id,
                "student_name": student_name,
                "student_class": student_class,
                "message_type": message_type,
                "recipient": recipient_type,
                "attendance_rate": f"{attendance_rate:.1f}%",
                "message": generated_message,
            }
            st.session_state.message_history.append(entry)
        
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save to History", use_container_width=True):
                save_to_message_history(
                    student_id=student_id,
                    student_name=f"{student_info['FirstName']} {student_info['LastName']}",
                    student_class=student_info['Class'],
                    message_type=message_type,
                    recipient_type=recipient_type,
                    generated_message=edited_message,
                    attendance_rate=attendance_rate
                )
                st.success("✅ Message saved to history!")
        
        
        with col2:
            if st.button("📤 Save & Mark Sent", use_container_width=True, type="primary"):
                save_to_message_history(
                    student_id=student_id,
                    student_name=f"{student_info['FirstName']} {student_info['LastName']}",
                    student_class=student_info['Class'],
                    message_type=message_type,
                    recipient_type=recipient_type,
                    generated_message=edited_message,
                    attendance_rate=attendance_rate
                )
                st.success("✅ Message marked as sent and saved to history!")
                st.session_state.current_message = ""
                st.rerun()
        
        
        with col3:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.toast("Message copied to clipboard! (Demo mode)", icon="📋")
        
        
        with col4:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.current_message = ""
                st.rerun()
    
    
    # ==================== ATTENDANCE OVERVIEW SECTION ====================
    st.divider()
    st.subheader("📊 Attendance Overview")
    
    tabs = st.tabs(["Student Attendance", "Communication History", "Export Data"])
    
    
    with tabs[0]:
        st.subheader("Individual Student Attendance")
        
        overview_student = st.selectbox(
            "Select Student to View Attendance",
            options=student_names,
            key="overview_student"
        )
        
        overview_student_id = int(overview_student.split("ID: ")[1].rstrip(")"))
        overview_student_info = students_df[students_df['StudentID'] == overview_student_id].iloc[0]
        
        
        student_attendance_full = attendance_df[attendance_df['StudentID'] == overview_student_id]
        
        # Attendance statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_lessons = len(student_attendance_full)
        lessons_attended = (student_attendance_full['Attended'] == True).sum()
        lessons_missed = (student_attendance_full['Attended'] == False).sum()
        attendance_percentage = (lessons_attended / total_lessons * 100) if total_lessons > 0 else 0
        
        with col1:
            st.metric("Total Lessons", total_lessons)
        
        with col2:
            st.metric("Lessons Attended", lessons_attended)
        
        with col3:
            st.metric("Lessons Missed", lessons_missed)
        
        with col4:
            st.metric("Attendance Rate", f"{attendance_percentage:.1f}%")
        
        
        # Attendance breakdown
        st.write("**Attendance Breakdown by Status:**")
        status_counts = student_attendance_full['Status'].value_counts()
        col1, col2 = st.columns(2)
        
        with col1:
            st.bar_chart(status_counts)
        
        with col2:
            st.write(status_counts)
        
        
        # Recent attendance details
        st.write("**Recent Attendance Records (Last 10 Lessons):**")
        recent_attendance = student_attendance_full.tail(10)[
            ['Date', 'LessonName', 'StartTime', 'Status', 'Attended', 'ArrivalTime', 'Notes']
        ]
        st.dataframe(recent_attendance, use_container_width=True)
    
    
    with tabs[1]:
        st.subheader("Communication History")
        
        if st.session_state.message_history:
            for idx, entry in enumerate(st.session_state.message_history):
                with st.expander(
                    f"📧 {entry['student_name']} - {entry['message_type']} - {entry['timestamp']}",
                    expanded=False
                ):
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.write(f"**Student:** {entry['student_name']} (Class: {entry['student_class']})")
                        st.write(f"**Message Type:** {entry['message_type']} | **Recipient:** {entry['recipient']}")
                        st.write(f"**Attendance Rate at Time:** {entry['attendance_rate']}")
                        st.write(f"**Timestamp:** {entry['timestamp']}")
                        st.divider()
                        st.write("**Message Content:**")
                        st.text(entry["message"])
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_msg_{idx}", use_container_width=True):
                            st.session_state.message_history.pop(idx)
                            st.rerun()
            
            st.info(f"📈 Total communications: {len(st.session_state.message_history)}")
        else:
            st.info("No messages in history yet. Generate and save some messages to see them here.")
    
    
    with tabs[2]:
        st.subheader("📥 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Export Attendance Data", use_container_width=True):
                attendance_export = attendance_df[[
                    'StudentID', 'Date', 'LessonName', 'Status', 'Attended', 'StartTime'
                ]].copy()
                
                csv = attendance_export.to_csv(index=False)
                st.download_button(
                    label="Download Attendance CSV",
                    data=csv,
                    file_name=f"attendance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        
        with col2:
            if st.button("💬 Export Communication Log", use_container_width=True):
                if st.session_state.message_history:
                    df_messages = pd.DataFrame(st.session_state.message_history)
                    csv = df_messages.to_csv(index=False)
                    st.download_button(
                        label="Download Communication Log CSV",
                        data=csv,
                        file_name=f"communication_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.warning("No communication history to export.")
        
        with col3:
            if st.button("👥 Export Student List", use_container_width=True):
                csv = students_df.to_csv(index=False)
                st.download_button(
                    label="Download Student List CSV",
                    data=csv,
                    file_name=f"student_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        
        
        st.divider()
        st.write("**Data Preview:**")
        
        preview_tab1, preview_tab2, preview_tab3 = st.tabs(["Students", "Attendance", "Communication"])
        
        with preview_tab1:
            st.dataframe(students_df, use_container_width=True)
        
        with preview_tab2:
            st.dataframe(attendance_df.head(50), use_container_width=True)
        
        with preview_tab3:
            if st.session_state.message_history:
                st.dataframe(pd.DataFrame(st.session_state.message_history), use_container_width=True)
            else:
                st.info("No communication history yet.")
    
    
    st.divider()
    st.caption("🎓 Student Registrar v1.0 | Built with Streamlit and Ollama Cloud | DEMO MODE")