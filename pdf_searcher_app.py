import streamlit as st
import dropbox
import pymupdf  # PyMuPDF
import os
import tempfile
from urllib.parse import urlparse


def get_dropbox_files(dbx, folder_path):
    try:
        files = dbx.files_list_folder(folder_path).entries
        return [f for f in files if isinstance(f, dropbox.files.FileMetadata) and f.name.endswith(".pdf")]
    except Exception as e:
        st.error(f"Error accessing Dropbox folder: {e}")
        return []


def search_keyword_in_pdf(dbx, file_path, keyword):
    try:
        metadata, res = dbx.files_download(file_path)
        with open("temp.pdf", "wb") as f:
            f.write(res.content)

        doc = pymupdf.open("temp.pdf")
        for page in doc:
            if keyword.lower() in page.get_text("text").lower():
                return True
        return False
    except Exception as e:
        st.error(f"Error searching PDF {file_path}: {e}")
        return False


def create_merged_pdf(dbx, file_paths):
    temp_dir = tempfile.mkdtemp()
    merged_pdf_path = os.path.join(temp_dir, "merged_pdfs.pdf")

    merger = pymupdf.open()
    for file_path in file_paths:
        metadata, res = dbx.files_download(file_path)
        local_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        with open(local_file_path, "wb") as f:
            f.write(res.content)

        doc = pymupdf.open(local_file_path)
        merger.insert_pdf(doc)

    merger.save(merged_pdf_path)
    merger.close()

    return merged_pdf_path


# Streamlit UI
st.title("Dropbox PDF Keyword Finder")

# User inputs Dropbox URL and keyword
dropbox_url = st.text_input("Enter Dropbox Folder URL")
access_token = st.text_input("Enter Dropbox Access Token", type="password")
keyword = st.text_input("Enter Keyword")
merge_pdfs = st.checkbox("Merge matching PDFs into one file")

if st.button("Find PDFs"):
    if not dropbox_url or not keyword or not access_token:
        st.warning("Please provide Dropbox folder URL, access token, and keyword.")
    else:
        # Extract folder path from URL
        parsed_url = urlparse(dropbox_url)
        path = parsed_url.path.replace("/sh/", "").split("?")[0]

        # Authenticate Dropbox
        dbx = dropbox.Dropbox(access_token)

        # Get PDF files in the folder
        pdf_files = get_dropbox_files(dbx, path)

        matching_pdfs = []
        for pdf in pdf_files:
            if search_keyword_in_pdf(dbx, pdf.path_lower, keyword):
                matching_pdfs.append(pdf.path_lower)
                st.markdown(f"[📄 {pdf.name}](https://www.dropbox.com/home{pdf.path_lower})")

        if merge_pdfs and matching_pdfs:
            merged_pdf_path = create_merged_pdf(dbx, matching_pdfs)
            with open(merged_pdf_path, "rb") as f:
                st.download_button("Download Merged PDF", f, file_name="merged_pdfs.pdf", mime="application/pdf")
        elif merge_pdfs:
            st.info("No matching PDFs found to merge.")
