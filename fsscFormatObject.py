"""
FSSC Audit Report Extractor Object Format

Objective: The logical idea of this method is to create multiple of class objects that represent for each of the format
and then using a simple classification model to call the suitable object that can extract the key info out.

Please be aware that this is a temporary method due to the limitation of data and time constrain.

Author: Anh Huy Vo
"""

from abc import ABC, abstractmethod
from PyPDF2 import PdfFileReader

import pdfplumber
import warnings
import camelot
import re

warnings.filterwarnings("ignore")

def get_auditor_name(pdf_file):
    """Get the information of the auditor (CB Name and Location) to call the correct object to 
       retrieve key information out.

       If cannot find, return null and then return to the user that we cannot recognize this format.

    Args:
        pdf_file ([bytes]): The pdf file that want to read

    Returns:
        auditor_name [str]: The auditor name that will be use to call the object
    """
    AUDITOR_PHRASE = ["cb name and office location", "cb name", "auditor name", "cb conducting audit", "certification body"]
    tables = camelot.read_pdf(pdf_file, pages = "0-end")
    for count in range(tables.n):
        dataframe = tables[count].df
        #print(list(dataframe.columns))
        for value in AUDITOR_PHRASE:
            print(dataframe.loc[dataframe[0] == value])


    #return auditor_name

class Baseline_Object(ABC):
    """Format Skeleton for FSSC Extractor"""

    @abstractmethod
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}
        super().__init__()

    @abstractmethod
    def load_and_read_pdf(self):
        pass

    @abstractmethod
    def key_info_extractor(self):
        pass

    def preprocessing(self):
        pass

    def postprocessing(self):
        pass


class Covid_Schema(Baseline_Object):
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}
    
    def load_and_read_pdf(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            self.raw_tables = [
                tables
                for page in pdf.pages
                for tables in page.extract_tables()
            ]
        
        return self.key_info_extractor(self.raw_tables)
    
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

    def key_info_extractor(self, table_information):
        for major_table in table_information:
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
    
class FSSC_Version_5_Schema(Baseline_Object):
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
        with open(self.pdf_path) as file:
            reader = PdfFileReader(self.pdf_path)
            pdf_length = reader.getNumPages()

        for page in range(pdf_length):
                self.tables = camelot.read_pdf(self.pdf_path, pages=str(page))
                self.key_info_extractor()
        return self.result

    def key_info_extractor(self):
        """
        Receive the table information extracted from load_and_read_pdf method and 
        loop through each row or table to find the specific information that need for the outcome

        Returns:
            result [dict]: Return a dictionary that contains key and value of specific information that user want to extract
        """
        for table in range(self.tables.n):
            dataframe = self.tables[table].df
            table_header = dataframe.iloc[0, 0]

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
                self.result["Audit Recommendation"] = dataframe.iloc[1, 0]
        return self.result

class AIBI_Schema(Baseline_Object):
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
                self.key_info_extractor()
            file.close()

        with pdfplumber.open(self.pdf_path) as file:
            text = file.pages[2].extract_text().split("\n")
            self.extract_non_conformities(text)
            file.close()

        with pdfplumber.open(self.pdf_path) as file:
            for i in range(15, 40):
                text = file.pages[i].extract_text().split("\n")
                self.extract_audit_recommendation(text)

        return self.result

    def key_info_extractor(self):
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
                self.result["Audit Recommendation"] = i.split(" ")[1:]


class NutriScience_Schema(Baseline_Object):
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}

    def load_and_read_pdf(self):
        self.tables = camelot.read_pdf(self.pdf_path, pages = "0-end")

        return self.key_info_extractor(self.tables)       

    def key_info_extractor(self, tables):
        for count in range(tables.n):
            dataframe = tables[count].df
            table_header = dataframe.iloc[0,0]

            if table_header == 'Organization profile' and "General description of \naudited organization" in list(dataframe.iloc[:,0]):
                organisation_name = dataframe.iloc[1,1]
                self.result["Organisation Name"] = organisation_name
                self.result["Address"] = dataframe.iloc[3,1]
                self.result["Contact Person"] = dataframe.iloc[4,1]
            
            if table_header == "Audit scope":
                self.result["Audit Scope"] = dataframe.iloc[1,1]
                self.result["Product Scope"] = dataframe.iloc[2,1].replace("\n","")
            
            if table_header == "Audit details":
                self.result["CB Name and Location"] = dataframe.iloc[2,1].replace("\n", "")

            if table_header == "Audit details previous audit":
                self.result["Audit Type"] = dataframe.iloc[1,1]
                self.result["Audit Date"] = dataframe.iloc[2,1]
                self.result["Previous Nonconformities Close"] = dataframe.iloc[4,1]
            
            if table_header == "Summary of audit findings":
                self.result["Critical Nonconformities"] = dataframe.iloc[1,0].split("\n")[0]
                self.result["Major Nonconformities"] = dataframe.iloc[2,0].split("\n")[0]
                self.result["Minor Nonconformities"] = dataframe.iloc[3,0].split("\n")[0]

        return self.result

class SAI_Schema(Baseline_Object):
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}
    
    def load_and_read_pdf(self):
        self.tables = camelot.read_pdf(self.pdf_path, pages = "0-end")

        return self.key_info_extractor(self.tables)

    def key_info_extractor(self, tables):

        for count in range(tables.n):
            dataframe = tables[count].df
            table_header = dataframe.iloc[0,0]

            if table_header == "Registered Legal Name:":
                self.result["Organisation Name"] = dataframe.iloc[1,2]
                self.result["Address"] = dataframe.iloc[3,2]
                self.result["Client Representative"] = dataframe.iloc[4,2]
            
            if table_header == "Certificate No.:":
                self.result["Audit Report Company"] = dataframe.iloc[1,2].split("\n")[0]
                self.result["Audit Type"] = dataframe.iloc[7,2].replace("\n", "")
                self.result["Audit Complexity"] = dataframe.iloc[8,2]
            
            if table_header == "Previous Audit Type:":
                self.result["Previous Audit Type"] = dataframe.iloc[0,1]
                self.result["Previous Audit Date"] = dataframe.iloc[1,1]
            
            if table_header == "Findings \n(refer to non-conformance \nreports)":
                try:
                    critical_nc_text = dataframe.iloc[1,1].split("\n")[6]
                    self.result["Critical Nonconformities"] = re.findall(r'\d+', critical_nc_text)[0]
                except:
                    self.result["Critical Nonconformities"] = 0
                
                try:
                    major_nc_text = dataframe.iloc[2,1].split("\n")[6]
                    self.result["Major Nonconformities"] = re.findall(r'\d+', major_nc_text)[0]
                except:
                    self.result["Major Nonconformities"] = 0
                
                try:
                    minor_nc_text = dataframe.iloc[3,1].split("\n")[6]
                    self.result["Minor Nonconformities"] = re.findall(r'\d+', minor_nc_text)[0]
                except:
                    self.result["Minor Nonconformities"] = 0

            if table_header == "The recommendation \nfrom this audit":
                self.result["Audit Recommendation"] = dataframe.iloc[0,1]

        return self.result


class SGS_Surveilance_Schema():
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}
    
    def load_and_read_pdf(self):
        self.tables = camelot.read_pdf(self.pdf_path, pages = "0-end")

        return self.key_info_extractor(self.tables)
    
    def key_info_extractor(self, tables):
        for count in range(tables.n):
            dataframe = tables[count].df
            table_header = dataframe.iloc[0,0]

            if table_header == "Organisation":
                self.result["Organisation Name"] = dataframe.iloc[0,1]
                self.result["Location"] = dataframe.iloc[3,1]
                self.result["Postcode"] = dataframe.iloc[5,1]
                self.result["Country"] = dataframe.iloc[6,1]
                self.result["Client Representative"] = dataframe.iloc[7,1]
            
            if "Additional \nStandard(s)" in table_header:
                self.result["Start and End Date"] = dataframe.iloc[3,1].split("\n")
                self.result["Last Date Previous Audit"] = dataframe.iloc[3,3]
                self.result["Cert Expiry Date"] = dataframe.iloc[4,3]
                self.result["Previous Audit Type"] = dataframe.iloc[5,3]
                self.result["Product Scope"] = dataframe.iloc[14,1]
            
            if table_header == "NUMBER OF NON-CONFORMITIES":
                self.result["Minor Nonconformities"] = dataframe.iloc[1,0].split("\n")[1]
                self.result["Major Nonconformities"] = dataframe.iloc[2,0].split("\n")[1]
                self.result["Critical Nonconformities"] = dataframe.iloc[3,0].split("\n")[1]

        return self.result

class DNV_Schema(Baseline_Object):
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result = {}
    
    def load_and_read_pdf(self):
        self.tables = camelot.read_pdf(self.pdf_path, pages = "0-end")

        return self.key_info_extractor(self.tables)
    
    def key_info_extractor(self, tables):
        for count in range(tables.n):
            dataframe = tables[count].df
            table_header = dataframe.iloc[0,0]

            if table_header == "Registered legal name":
                self.result["Organisation Name"] = dataframe.iloc[0,1]
                self.result["Location"] = dataframe.iloc[1,1]
                self.result["Client Representative"] = dataframe.iloc[3,1].split(";")[0]
            
            if "Certificate Number" in table_header:
                self.result["Expiry Date"] = dataframe.iloc[1,1]
                self.result["Product Scope"] = dataframe.iloc[2,1]
            
            if ("Audit type" in table_header) and ("Audit onsite start date" in list(dataframe.iloc[:,0])):
                self.result["Audit Type"] = dataframe.iloc[0,3] + " " + dataframe.iloc[1,3]
                self.result["Audit Start Date"] = dataframe.iloc[5,3]
                self.result["Audit End Date"] = dataframe.iloc[6,3]
            
            if ("Audit type" in table_header) and ("Audit dates" in list(dataframe.iloc[:,0])):
                self.result["Previous Audit Type"] = dataframe.iloc[0,1] + " " + dataframe.iloc[1,1]
                self.result["Audit dates"] = dataframe.iloc[2,1]
                self.result["Audit Company Name"] = dataframe.iloc[3,1]
                self.result["Nonconformities Close"] = dataframe.iloc[4,1]
            
            if "Number of critical non-conformities" in table_header:
                self.result["Critical Nonconformities"] = dataframe.iloc[0,1]
                self.result["Major Nonconformities"] = dataframe.iloc[1,1]
                self.result["Minor Nonconformities"] = dataframe.iloc[2,1]
                self.result["Nonconformities Close Number"] = dataframe.iloc[3,1]

        return self.result

pdf_path = input("Please input the PDF Path: ")
get_auditor_name(pdf_path)
#schema = DNV_Schema(pdf_path)
#result = schema.load_and_read_pdf()
#print(result)

