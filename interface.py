import streamlit as st
import base64

from pathlib import Path
from kosher_ocr import pipeline
from extraction import Covid_Schema

#Setup page configuration and connect with css file
st.set_page_config(
     page_title='Otrafy OCR 3PA Service',
     layout= "wide",
     initial_sidebar_state= "auto",
     page_icon = ":eyeglasses:"
)

with open("style.css") as css_file:
    st.markdown(f'<style>{css_file.read()}</style>', unsafe_allow_html=True)

#Convert image to bytes
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

#CSS for the sidebar nav
def css_sidebar():
    st.sidebar.markdown('''[<img src='data:image/png;base64,{}' class='center' width=60 height=130>](https://www.otrafy.com)'''.format(img_to_bytes("otrafy_icon.jpg")), unsafe_allow_html=True)
    st.sidebar.markdown("<h1 style='text-align: center; color: white;'>Otrafy 3PA OCR Service</h1>", unsafe_allow_html=True)
    selected_event = st.sidebar.selectbox('', ["Please choose a service","Third Party Audit Report OCR", "Third Party Certificate OCR", "Kosher Certificate OCR"])

    return selected_event

#Link to the extractor to extract the information
def extract_info():
    pdf_file = st.file_uploader('Upload Audit Report to scan', type=["pdf"])
    if pdf_file is not None:
        schema = Covid_Schema(pdf_file)
        result = schema.load_and_read_pdf()
        print(result)
    return result, pdf_file

#Post Processing the address after extract
def post_process_address(result_extractions, format_type):
    if "Covid Schema" in format_type:
        address = result_extractions['Address'] + " " + result_extractions['City'] + " " + result_extractions['Postcode'] + " " + result_extractions['Country']
    elif format_type == "FSSC Version 5 Schema":
        address = result_extractions["City"] + " " + result_extractions["Region"] + " " + result_extractions["Postal Code"] + " " + result_extractions['Country']
    
    return address

#Display the result that extract from the document
def display_result(result, pdf_file):
    with st.container():
        address = post_process_address(result, result["Format"])
        st.markdown("<h4 style='color: black;'>Attachment Analysis Result</h4>", unsafe_allow_html=True)
        st.markdown("<div class=line></div>", unsafe_allow_html=True)

        st.markdown(f"<h7 style='color: black;'><b>File Name:</b> {pdf_file.name}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Audit Report Type:</b> {result['Audit Document Class']}</h7>", unsafe_allow_html=True)
        #st.markdown(f"<h7 style='color: black;'><b>Expiration Date:</b> NA</h7>", unsafe_allow_html=True)
        st.markdown("<div class=line></div>", unsafe_allow_html=True)

        st.markdown(f"<h7 style='color: black;'><b>Organisation Name:</b> {result['Organisation Name']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Address:</b> {address}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Client Representative:</b> {result['Client Representative']}</h7>", unsafe_allow_html=True)
        st.markdown("<div class=line></div>", unsafe_allow_html=True)

        st.markdown(f"<h7 style='color: black;'><b>Number of Minor Nonconformities:</b> {result['Minor Nonconformities']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Number of Major Nonconformities:</b> {result['Major Nonconformities']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Number of Critical Nonconformities:</b> {result['Critical Nonconformities']}</h7>", unsafe_allow_html=True)
        st.markdown("<div class=line></div>", unsafe_allow_html=True)

        st.markdown(f"<h7 style='color: black;'><b>Auditor Company Name:</b> {result['CB Name and Location']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Audit Type:</b> {result['Audit Type']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Audit Recommendation:</b> {result['Audit Recommendation']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Have all NCs been closed ?:</b> Yes</h7>", unsafe_allow_html=True)
        st.markdown("<div class=line></div>", unsafe_allow_html=True)

        st.markdown(f"<h7 style='color: black;'><b>Previous Audit Type:</b> {result['Previous Audit Type']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Previous Start Date:</b> {result['Previous Start Date']}</h7>", unsafe_allow_html=True)
        st.markdown(f"<h7 style='color: black;'><b>Previous End Date:</b> {result['Previous End Date']}</h7>", unsafe_allow_html=True)
        
#Main Function
def main():
    """
        Logical process of the Key Information Extraction part
    """
    event = css_sidebar()

    with st.container():
        if event == "Third Party Audit Report OCR":
            try:
                result, pdf_file = extract_info()
                display_result(result, pdf_file)
            except:
                #raise
                pass
        elif event == "Please choose a service":
            st.empty()
        elif event == "Kosher Certificate OCR":
            pipeline()
        else:
            st.markdown("<h1 style='text-align: center; color: black;'>Service Unvailable</h1>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()