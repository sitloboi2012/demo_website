import io
from typing import Dict

import camelot
import streamlit as st
import pdfplumber
from PyPDF2 import PdfFileReader


class Covid_Schema():
    """
    Covid Schema OCR Key Information Extraction Object
    """

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}

    def load_and_read_pdf(self):
        """
        Load the PDF file, read it and return a dict result

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            self.raw_tables = [
                tables
                for page in pdf.pages
                for tables in page.extract_tables()
            ]

        return self.key_information_extraction(self.raw_tables)

    def preprocessing(self, text):
        """
        Get a text that included both string and number and convert to get int only

        Args:
            text (str): a text that extract from the pdf

        Returns:
            numb [int]: a number that appear in that text
        """
        result = [int(s) for s in text.split() if s.isdigit()]
        return result[0]

    def key_information_extraction(self, table_info):
        """
        Receive the table information extracted from load_and_read_pdf method and 
        loop through each row or table to find the specific information that need for the outcome

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        for major_table in table_info:
            for minor_table in major_table:

                if "Organisation Details" in minor_table:
                    for rows in major_table[1:]:
                        if "Organisation" in rows:
                            self.result["Organisation Name"] = rows[1]
                        elif "Address" in rows:
                            self.result["Address"] = rows[1]
                        elif "City" in rows:
                            self.result["City"] = rows[1]
                        elif "Postcode" in rows:
                            self.result["Postcode"] = rows[1]
                        elif "Country" in rows:
                            self.result["Country"] = rows[1]
                        elif "Client Representative" in rows:
                            self.result["Client Representative"] = rows[1]

                if "Critical Nonconformities" in minor_table:
                    self.result["Critical Nonconformities"] = minor_table[1]
                elif "Major Nonconformities" in minor_table:
                    self.result["Major Nonconformities"] = minor_table[1]
                elif "Minor Nonconformities" in minor_table:
                    self.result["Minor Nonconformities"] = self.preprocessing(
                        minor_table[1])
                elif "Audit Recommendation" in minor_table:
                    self.result["Audit Recommendation"] = minor_table[1]
                    self.result["Nonconformities Close"] = "Yes"
                elif "CB Name and Location" in minor_table:
                    self.result["CB Name and Location"] = minor_table[1]
                    self.result["Audit Document Class"] = "FSSC"
                    self.result["Format"] = "Covid Schema"
                

                for rows in major_table:
                    if "Audit Type" in rows:
                        if len(rows) == 2:
                            self.result["Audit Type"] = rows[1]
                        else:
                            self.result["Previous Audit Type"] = rows[2]
                    if "Start Date" in rows:
                        self.result["Previous Start Date"] = rows[1]
                        self.result["Previous End Date"] = rows[3]

        return self.result


class FSSC_Version_5_Schema():
    """
    FSSC Version 5 Schema OCR Key Information Extraction Object
    """

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}

    def load_and_read_pdf(self):
        """
        Load, read the pdf and return the key information that need to be extract
        Due to the ability of each of the package, we have to use both PDFPlumber and Camelot in this case

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        file_contents = self.pdf_path.read()
        print(camelot.__version__)
        # stream = io.BytesIO(file_contents)
        # reader = PdfFileReader(stream)
        # pdf_length = reader.getNumPages()
        filepath = 'downloaded_file.pdf'
        with open(filepath, 'wb+') as file:
            file.write(file_contents)
        
        self.tables = camelot.read_pdf(filepath, pages='all')
        self.key_information_extraction()
        # for page in range(pdf_length):
        return self.result

    def key_information_extraction(self):
        """
        Receive the table information extracted from load_and_read_pdf method and 
        loop through each row or table to find the specific information that need for the outcome

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        for table in range(self.tables.n):
            dataframe = self.tables[table].df
            table_header = dataframe.iloc[0, 0]
            print(table_header)

            if table_header == "Organization profile":
                self.result["Organisation Name"] = dataframe.iloc[2, 1]
                self.result["City"] = dataframe.iloc[6, 1]
                self.result["Region"] = dataframe.iloc[7, 1]
                self.result["Postal Code"] = dataframe.iloc[8, 1]
                self.result["Country"] = dataframe.iloc[9, 1]
                self.result["Client Representative"] = dataframe.iloc[10, 1]

            elif table_header == "Audit details":
                self.result["CB Name and Location"] = dataframe.iloc[1, 1]
                self.result["Audit Type"] = dataframe.iloc[6, 1]
                self.result["Audit Document Class"] = "FSSC"
                self.result["Format"] = "FSSC Version 5 Schema"

            elif table_header == "Audit details previous audit":
                self.result["Prev Audit Type"] = dataframe.iloc[1, 1]

            elif table_header == "Summary of audit findings":
                self.result["Critical Nonconformities"] = dataframe.iloc[1, 1]
                self.result["Major Nonconformities"] = dataframe.iloc[2, 1]
                self.result["Minor Nonconformities"] = dataframe.iloc[3, 1]

            elif table_header == "Audit recommendation":
                self.result["Audit Recommendation"] = "(Re-)Certification Granted"
                self.result["Nonconformities Close"] = "Yes"
        return self.result


class AIBI_Schema():
    """
    AIBI Schema OCR Key Information Extraction Object
    """

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}

    def load_and_read_pdf(self):
        """
        Load, read the pdf and return the key information that need to be extract
        Due to the ability of each of the package, we have to use both PDFPlumber and Camelot in this case

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        with open(self.pdf_path, "rb") as file:
            for page in range(0, 6):
                self.tables = camelot.read_pdf(self.pdf_path, pages=str(page))
                self.key_information_extraction()
            file.close()

        with pdfplumber.open(self.pdf_path) as file:
            text = file.pages[2].extract_text().split("\n")
            self.extract_non_conformities(text)
            file.close()

        with pdfplumber.open(self.pdf_path) as file:
            for i in range(20, 36):
                text = file.pages[i].extract_text().split("\n")
                self.extract_audit_recommendation(text)

        return self.result

    def key_information_extraction(self):
        """
        Receive the table information extracted from load_and_read_pdf method and 
        loop through each row or table to find the specific information that need for the outcome

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        for table in range(self.tables.n):
            dataframe = self.tables[table].df
            table_header = dataframe.iloc[0, 0]

            if table_header == "Registered legal name" and "General description of organization" in list(dataframe.iloc[:, 0]):
                organisation_name = dataframe.iloc[0, 1].split("-")
                self.result["City"] = organisation_name[1]
                self.result["Organization name"] = organisation_name[0]
                self.result["Location"] = dataframe.iloc[3, 1]
                self.result["Contact Person"] = dataframe.iloc[4, 1]

            elif table_header == "Audit type":
                self.result["Prev Audit type"] = dataframe.iloc[0, 1]
                self.result["Prev Audit date"] = dataframe.iloc[1, 1]
                self.result["CB name"] = "AIBI-CS"
                self.result["Format"] = "AIBI Schema"

        return self.result

    def extract_non_conformities(self, text):
        for i in text:
            if "Critical nonconformities" in i:
                i = i.split(" ")
                i = i[-1]
                self.result["Critical nonconformities"] = i
            elif "Major nonconformities" in i:
                i = i.split(" ")
                i = i[-1]
                self.result["Major nonconformities"] = i
            elif "Minor nonconformities" in i:
                i = i.split(" ")
                i = i[-1]
                self.result["Minor nonconformities"] = i

    def extract_audit_recommendation(self, text):
        for i in text:
            if "Conclusion" in i:
                self.result["Audit Type"] = "Certification Maintained"
                self.result["Audit Recommendation"] = i.split(" ")[1:]
