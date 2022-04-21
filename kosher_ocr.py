import streamlit as st
import spacy
import pdfplumber as plumber
import itertools
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# open it, go to a website, and get results
driver = webdriver.Chrome(options=options)
nlp = spacy.load("ner-model-best")


def ocr_text(path):
    """
    OCR Model
    """
    pdf = plumber.open(path)
    text = []
    sent_full = []
    for page in pdf.pages:
        text.append(page.extract_text())

    for sent in text:
        sent_full.append(sent.split("\n"))

    sent_tokenize = list(itertools.chain.from_iterable(sent_full))
    return sent_tokenize

def ner(list_of_line_to_ner, nlp):
    label_list = []
    text_list = []

    for line in list_of_line_to_ner:
        clean_text = preprocess_text(line)
        text = nlp(clean_text)
        for ent in text.ents:
            label_list.append(ent.label_)
            text_list.append(ent.text)
    
    dataframe = pd.DataFrame({"text": text_list, "label": label_list})
        
    return dataframe

def group_1_scraper(product_id):
    driver.delete_all_cookies()
    driver.get("https://digitalkosher.com/oskm/home.jsp")

    username = driver.find_element_by_xpath("//table/tbody/tr[4]/td/table/tbody/tr/td[2]/table/tbody/tr/td/form/input[3]")
    password = driver.find_element_by_xpath("//table/tbody/tr[4]/td/table/tbody/tr/td[2]/table/tbody/tr/td/form/input[4]")
    username.clear()
    password.clear()
    username.send_keys("huyvo6812")
    password.send_keys("Poohuynh183")
    driver.find_element(By.NAME, 'Submit').click()

    element = driver.find_element_by_id("kidSearchText")
    element.clear()
    element.send_keys(product_id)
    element.send_keys(Keys.ENTER)

    ingredient_name = driver.find_element_by_xpath("//table/tbody/tr[4]/td[1]/table[1]/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[2]/td[2]").text
    supplier_name = driver.find_element_by_xpath("//table/tbody/tr[4]/td[1]/table[1]/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[3]/td[2]").text
    certifier = driver.find_element_by_xpath("//table/tbody/tr[4]/td[1]/table[1]/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[4]/td[2]").text
    expiry_date = driver.find_element_by_xpath("//table/tbody/tr[4]/td[1]/table[1]/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[5]/td[2]").text
    
    result = {"product_name": ingredient_name, 
              "supplier_name": supplier_name,
              "certifier": certifier,
              "expiry_date": expiry_date,
              "id": product_id}
    return result

def preprocess_text(text):
    clean_text = text.lower()
    clean_text = clean_text.replace(",", "")
    
    if "until" in clean_text:
        clean_text = "".join(clean_text.split("until"))
    
    return clean_text

def group_2_scraper(product_id):
    driver.delete_cookie
    driver.get("https://www.koshercertificate.com/login.aspx")
    driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_txtLogin']").send_keys('huy@otrafy.com')
    driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_txtPassword']").send_keys('otrafydata')
    driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_btnLogin']").click()
    
    ukd_search_button = driver.find_element_by_xpath("//div[3]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[2]/td[4]/a").click()
    input_search = driver.find_element_by_xpath("//div[3]/table/tbody/tr[3]/td/div/table/tbody/tr[4]/td/input")
    input_search.clear()
    input_search.send_keys(product_id)
    input_search.send_keys(Keys.ENTER)

    ingredient_name = driver.find_element_by_xpath("//div[3]/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr[3]/td[2]/span")
    supplier_name = driver.find_element_by_xpath("//div[3]/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr[4]/td[2]/span")
    certifier = driver.find_element_by_xpath("//div[3]/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr[5]/td[2]/span")
    expiry_date = driver.find_element_by_xpath("//div[3]/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr[6]/td[2]/span")

    result = {"product_name": ingredient_name, 
              "supplier_name": supplier_name,
              "certifier": certifier,
              "expiry_date": expiry_date,
              "id": product_id}
    return result

def pipeline():
    try:
        pdf_file = st.file_uploader("Upload a Kosher Certificate to scan", type=["pdf"])
        text_list = ocr_text(pdf_file)
        dataframe = ner(text_list, nlp)
        product_id_list = list(dataframe["text"][dataframe["label"].str.contains("ID")])
        product_name = []
        supplier_name = []
        certifier = []
        expiry_date = []
        product_id = []
        for id in product_id_list:
            try:
                crawl_result = group_1_scraper(id)
                product_name.append(crawl_result["product_name"])
                supplier_name.append(crawl_result["supplier_name"])
                certifier.append(crawl_result["certifier"])
                expiry_date.append(crawl_result["expiry_date"])
                product_id.append(crawl_result["id"])
            except:
                crawl_result = group_2_scraper(id)
                product_name.append(crawl_result["product_name"])
                supplier_name.append(crawl_result["supplier_name"])
                certifier.append(crawl_result["certifier"])
                expiry_date.append(crawl_result["expiry_date"])
                product_id.append(crawl_result["id"])
            else:
                pass
                    
        
        result_dataframe = pd.DataFrame({
            "Product Name":product_name,
            "Supplier Name": supplier_name,
            "Certifier": certifier,
            "Expiry Date": expiry_date,
            "Product ID": product_id})
    except:
        pass
    
    try:
        st.write(result_dataframe)
    except:
        pass