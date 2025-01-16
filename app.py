import streamlit as st
import requests
import time
import pandas as pd
import json

# SnapLogic API details
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Aleksandra%20Kulawska/syncron/draft%20Task"
BEARER_TOKEN = "2S4USaBtuMLDAY6IazTKy5HYcDseni4H"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

# Title and description
st.title("Syncron Data Validation Assistant")
st.markdown(
    """
    Welcome to the Syncron Data Validation Assistant. This application validates your CSV files against
    Syncron's specified requirements. Upload your files to get started.
    """
)

# File uploader
customer_file = st.file_uploader("Upload Customer Data File (CSV or TXT)", type=["csv", "txt"])

# Add file preview section
if customer_file is not None:
    with st.spinner('Previewing file...'):
        try:
            # Read the file as a pandas DataFrame with error handling
            df = pd.read_csv(
                customer_file,
                on_bad_lines='warn',  # Warn about bad lines instead of raising an error
                engine='python',      # More flexible but slower engine
                quoting=3            # QUOTE_NONE: Don't use quotes to enclose fields
            )
            
            # Reset the file pointer for later use
            customer_file.seek(0)
            
            st.write("### File Preview:")
            st.write(f"Total rows: {len(df)}")
            st.dataframe(df.head(5), use_container_width=True)
        except Exception as e:
            st.error(f"Error previewing file: {str(e)}")
            st.info("Note: Your file may contain inconsistent formatting. The validation process will still continue.")

if st.button("Run Validation"):
    if not customer_file:
        st.error("Please upload the customer data file before running the validation.")
    else:
        with st.spinner('Processing validation request...'):
            st.write("### File Uploaded:")
            st.write(f"- Customer File: {customer_file.name}")

            # Send file to SnapLogic API using the new approach
            try:
                response = requests.post(
                    url=URL,
                    data=customer_file.getvalue(),
                    headers={
                        "Authorization": f"Bearer {BEARER_TOKEN}",
                        "Content-Type": "text/csv"
                    },
                    timeout=timeout
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # Extract content from the nested structure
                        if result and isinstance(result, list) and len(result) > 0:
                            content = result[0].get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
                            
                            if content:
                                # Split content into sections
                                sections = content.split('\n\n')
                                
                                # First, find and display the validation status
                                status_line = next((s for s in sections if "Validation status:" in s), "")
                                if status_line:
                                    status = status_line.split("Validation status:")[1].strip()
                                    status_color = {
                                        "GREEN": "🟢 #0f5132",
                                        "YELLOW": "🟡 #997404",
                                        "RED": "🔴 #842029"
                                    }.get(status.upper(), "#1e1e1e")
                                    
                                    st.markdown(
                                        f"""
                                        <div style="
                                            padding: 20px;
                                            border-radius: 10px;
                                            margin: 25px 0;
                                            background-color: {status_color.split()[1]};
                                            color: white;
                                            font-weight: bold;
                                            display: flex;
                                            align-items: center;
                                        ">
                                            <span style="font-size: 24px; margin-right: 10px;">{status_color.split()[0]}</span>
                                            <span>Validation Status: {status}</span>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                # Display the rest of the content in styled sections
                                for section in sections:
                                    if "Validation status:" not in section:
                                        # Check if it's a section header
                                        if any(header in section for header in [
                                            "Errors and warnings:", 
                                            "Recommendations:", 
                                            "Conclusion:"
                                        ]):
                                            # Display section header
                                            header = section.split(':')[0] + ':'
                                            st.markdown(
                                                f"""
                                                <div style="
                                                    margin-top: 30px;
                                                    margin-bottom: 15px;
                                                    padding: 12px 15px;
                                                    background-color: #f8f9fa;
                                                    border-left: 5px solid #0d6efd;
                                                    font-weight: bold;
                                                    border-radius: 0 4px 4px 0;
                                                ">
                                                    {header}
                                                </div>
                                                """, 
                                                unsafe_allow_html=True
                                            )
                                            
                                            # Display section content if any
                                            if ':' in section:
                                                content = section.split(':', 1)[1].strip()
                                                if content:
                                                    lines = content.split('\n')
                                                    formatted_lines = []
                                                    for line in lines:
                                                        line = line.strip()
                                                        if line:
                                                            formatted_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{line}")
                                                    
                                                    formatted_content = "<br>".join(formatted_lines)
                                                    st.markdown(
                                                        f"""
                                                        <div style="
                                                            margin: 15px 0 20px 20px;
                                                            line-height: 1.6;
                                                        ">
                                                            {formatted_content}
                                                        </div>
                                                        """,
                                                        unsafe_allow_html=True
                                                    )
                                        else:
                                            # Regular content
                                            st.markdown(section)
                        else:
                            st.error("Invalid response format")
                            
                    except json.JSONDecodeError:
                        st.error("Failed to parse API response")
                else:
                    st.error(f"API request failed with status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: {str(e)}")
