import os
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from arcadepy import Arcade

# Set page configuration
st.set_page_config(
    page_title="Google Doc Reader",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'doc_content' not in st.session_state:
    st.session_state.doc_content = ""
if 'auth_complete' not in st.session_state:
    st.session_state.auth_complete = False
if 'doc_loaded' not in st.session_state:
    st.session_state.doc_loaded = False
if 'document_id' not in st.session_state:
    st.session_state.document_id = ""

def get_google_doc_content():
    """Function to retrieve Google Doc content."""
    try:
        client = Arcade(api_key=os.environ["ARCADE_API_KEY"])
        USER_ID = "terresap2010@gmail.com"
        
        # Handle authorization
        auth_response = client.auth.start(
            user_id=USER_ID,
            provider="google",
            scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"],
        )

        if not st.session_state.auth_complete:
            if auth_response.status != "completed":
                st.link_button("Authorize Google Drive Access", auth_response.url)
                client.auth.wait_for_completion(auth_response)
                st.session_state.auth_complete = True
                st.rerun()
        
        # Get the auth token
        token = auth_response.context.token
        
        if not token:
            st.error("No token found in auth response")
            return

        # Build the credentials and Docs client
        credentials = Credentials(token)
        google_doc = build("docs", "v1", credentials=credentials)
        document_id = st.session_state.document_id
        
        # Get document content
        try:
            with st.spinner("Loading document content..."):
                document = google_doc.documents().get(documentId=document_id).execute()
                
                # Extract text content from the document
                doc_content = ""
                content = document.get("body", {}).get("content", [])
                
                # Process all content elements to extract text
                for element in content:
                    if "paragraph" in element:
                        paragraph = element.get("paragraph", {})
                        for elem in paragraph.get("elements", []):
                            if "textRun" in elem:
                                doc_content += elem.get("textRun", {}).get("content", "")
                
                # Store the content in session state
                st.session_state.doc_content = doc_content
                st.session_state.doc_loaded = True
                st.success("✅ Successfully retrieved Google Doc content!")
            
        except Exception as doc_error:
            st.error(f"Error retrieving document: {str(doc_error)}")
        
    except Exception as e:
        st.error(f"❌ Error accessing Google Doc: {str(e)}")
        import traceback
        st.expander("Error Details").write(traceback.format_exc())

# Main app UI
st.title("📄 Google Doc Reader")
st.markdown("---")

# Document ID input
col1, col2 = st.columns([3, 1])
with col1:
    document_id = st.text_input(
        "Document ID", 
        value="",
        placeholder="Enter Google Doc ID here",
        help="ID from Google Doc URL: docs.google.com/document/d/[THIS-IS-THE-ID]/edit"
    )

with col2:
    if st.button("Load Document", type="primary", use_container_width=True):
        if document_id:
            st.session_state.document_id = document_id
            get_google_doc_content()
        else:
            st.error("Please enter a Document ID first")

# Display document content
if st.session_state.doc_loaded:
    st.markdown("## Document Content")
    
    # Content stats
    word_count = len(st.session_state.doc_content.split())
    char_count = len(st.session_state.doc_content)
    
    stat_col1, stat_col2 = st.columns(2)
    stat_col1.metric("Word Count", f"{word_count:,}")
    stat_col2.metric("Character Count", f"{char_count:,}")
    
    # Full content in an expandable container
    with st.expander("Full Document Content", expanded=True):
        st.text_area(
            "Document Text", 
            value=st.session_state.doc_content, 
            height=400,
            disabled=True
        )
    
    # Optional: Download button for the content
    st.download_button(
        label="Download as Text File",
        data=st.session_state.doc_content,
        file_name="google_doc_content.txt",
        mime="text/plain"
    )
else:
    st.info("Click 'Load Document' to retrieve the Google Doc content")

# Footer
st.markdown("---")
st.caption("Google Doc Reader App | Made with Streamlit")