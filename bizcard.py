import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import mysql.connector

#CONVERTING IMAGE TO BINARY

def img_txt(img):
    upload_image =  Image.open(img)
    img_arr = np.array(upload_image)
    img_reader = easyocr.Reader(['en'])
    imgtext = img_reader.readtext(img_arr, detail=0, paragraph=False)

    return imgtext, upload_image

def ext_text (texts):
    extracted_info = {"NAME":[], "DESIGNATION":[], "COMPANY_NAME":[], "CONTACT":[], "EMAIL":[], "WEBSITE":[], "AREA":[], "CITY":[], "STATE":[], "PINCODE":[]}

    for i,j in enumerate(texts):
        if i==0:
            extracted_info["NAME"].append(j)   #Getting name

        elif i == 1:
            extracted_info["DESIGNATION"].append(j)   #Getting Designation

        elif j.startswith("+") or (j.replace("-","").isdigit() and "-" in j):            
            extracted_info["CONTACT"].append(j)   #Getting Contact details

        elif "@" in j and ".com" in j:
            extracted_info["EMAIL"].append(j)   #Getting Email address
                    
        elif "www" in j.lower() or "www." in j.lower() or "WWW" in j:
            stxt = j.lower()
            extracted_info["WEBSITE"].append(stxt)     #Getting Website name

        elif re.match(r'^[A-Za-z]',j):#i == len(texts)-1:
            extracted_info["COMPANY_NAME"].append(j)        #Getting Company name

        if re.findall('^[0-9].+, [a-zA-Z]+',j):
            extracted_info["AREA"].append(j.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+',j):
            extracted_info["AREA"].append(j)    #Getting area name

        match1 = re.findall('.+St , ([a-zA-Z]+).+', j)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', j)
        match3 = re.findall('^[E].*',j)
        if match1:
            extracted_info["CITY"].append(match1[0])
        elif match2:
            extracted_info["CITY"].append(match2[0])
        elif match3:
            extracted_info["CITY"].append(match3[0])    #Getting City name

        state_match = re.findall('[a-zA-Z]{9} +[0-9]',j)
        if state_match:
            extracted_info["STATE"].append(j[:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);',j):
            extracted_info["STATE"].append(j.split()[-1])
        if len(extracted_info["STATE"])== 2:
            extracted_info["STATE"].pop(0)    #Getting State name
       
        if len(j)>=6 and j.isdigit():
            extracted_info["PINCODE"].append(j)
        elif re.findall('[a-zA-Z]{9} +[0-9]',j):
            extracted_info["PINCODE"].append(j[10:])    #Getting Pincode

    for key, value in extracted_info.items():
        if len(value)>0:
            concadenate = " ".join(value)
            extracted_info[key] = [concadenate]

    return extracted_info


mydb =  mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "NANANANA",
        database = "Bizcard",
        auth_plugin='mysql_native_password'
        )
cursor = mydb.cursor()
cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'NANANANA'")
cursor = mydb.cursor(buffered=True)
    

#UI Page
st.set_page_config(layout="wide")
st.title("BizCardX: Extracting Business Card Data with OCR ")
selected = option_menu(None, ["Home","Upload and Extract","Modify"], 
                       icons=["house","cloud-upload","pencil-square"],
                       menu_icon= "menu-button-wide",
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link-selected": {"background-color": "#5d78a3"}})

if selected == "Home":
    st.write('### Bizcard application is  designed to extract information from business a card, using various technologies such as :blue[Streamlit, Streamlit_lottie, Python, EasyOCR , RegEx function, OpenCV, and MySQL] to achieve this functionality.')
    st.write('### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company name, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR')

elif selected == "Upload and Extract":
    card_img = st.file_uploader("Upload the Image", type=["png", "jpg", "jpeg"])
    if card_img is not None:
        st.image(card_img, width=400)
        text_img, img_uploaded = img_txt(card_img)
        tdic = ext_text(text_img)

        if tdic:
            st.success("TEXT EXTRACTED SUCCESSFULLY")

        df = pd.DataFrame(tdic)
        #st.dataframe(df)

        #Image to Bytes 

        img_byt = io.BytesIO()
        img_uploaded.save(img_byt, format= "PNG")
        imgdata = img_byt.getvalue()

        #Creating Dictionary

        data = {"Image": [imgdata]}
        df1 =pd.DataFrame(data)
        df_concat = pd.concat([df, df1], axis=1)
        st.dataframe(df_concat)

        save_button = st.button("Upload to Database")
        if save_button:
            #SQL Table creation

            table = '''create table if not exists card_detail (name varchar(225),
                                                                designation varchar(225),
                                                                company_name varchar(225),
                                                                contact varchar(225),
                                                                email varchar(225),
                                                                website varchar(225),
                                                                area varchar(225),
                                                                city varchar(225),
                                                                state varchar(225),
                                                                pincode varchar(225),
                                                                image longblob)'''

            cursor.execute(table)
            mydb.commit()

            #Data insertion to SQL
            insert_query = '''insert into card_detail(name, designation, company_name, contact, email, website, area, city, state, pincode, image)
                                                    values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

            df_data = df_concat.values.tolist()[0]
            cursor.execute(insert_query, df_data)
            mydb.commit()

            st.success("Uploaded to database successfully!")

        show_button = st.button("View Data from Database")
        if show_button:
            #MySQL Select query
            selectq = '''select * from card_detail'''
            cursor.execute(selectq)
            dbtable = cursor.fetchall()
            mydb.commit()

            table_df = pd.DataFrame(dbtable, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "AREA", "CITY", "STATE", "PINCODE", "IMAGE"))
            st.dataframe(table_df)

elif selected == "Modify":
    options = st.radio("",("Update Data", "Delete Data"))
    column1,column2 = st.columns(2)
    col1,col2 = st.columns(2)

    if options == "Update Data":
        try:
            with column1:
                cursor.execute("SELECT name FROM card_detail")
                dbtable = cursor.fetchall()
                business_cards = {}
                for row in dbtable:
                    business_cards[row[0]] = row[0]
                selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
                st.markdown("#### Update or modify any data below")
                cursor.execute("select name, company_name, designation, contact, email, website, area, city, state, pincode from card_detail WHERE name=%s",
                                (selected_card,))
                dbtable1 = cursor.fetchone()
                
                Card_holder = st.text_input("Card holder", dbtable1[0])
                Company_name = st.text_input("Company name", dbtable1[1])
                Designation = st.text_input("Designation", dbtable1[2])
                Mobile_number = st.text_input("Mobile number", dbtable1[3])
                Email = st.text_input("Email", dbtable1[4])
                Website = st.text_input("Website", dbtable1[5])
                Area = st.text_input("Area", dbtable1[6])
                City = st.text_input("City", dbtable1[7])
                State = st.text_input("State", dbtable1[8])
                Pin_code = st.text_input("Pincode", dbtable1[9])

                if st.button("Save Changes"):
                    # Update the information for the selected business card in the database
                    cursor.execute("""UPDATE card_detail SET name=%s,company_name=%s,designation=%s,contact=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pincode=%s
                                        WHERE name=%s""", (Card_holder,Company_name,Designation,Mobile_number,Email,Website,Area,City,State,Pin_code,selected_card))
                    mydb.commit()
                    st.success("Information updated into database successfully.")

        except:
            st.warning("There is no data available in the database")

        if st.button("View updated data"):
                cursor.execute("select company_name,name,designation,contact,email,website,area,city,state,pincode from card_detail")
                updated_df = pd.DataFrame(cursor.fetchall(),columns=["Company_Name","Name","Designation","Contact","Email","Website","Area","City","State","PinCode"])
                st.write(updated_df)

    if options == "Delete Data":
        try:
            with column1:
                cursor.execute("SELECT name FROM card_detail")
                dbtable = cursor.fetchall()
                business_cards = {}
                for row in dbtable:
                    business_cards[row[0]] = row[0]
                selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
                st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
                st.write("#### Would you like to delete this card?")

                if st.button("Delete"):
                    cursor.execute(f"DELETE FROM card_detail WHERE name='{selected_card}'")
                    mydb.commit()
                    st.success("Business card information deleted from database.")
        except:
            st.warning("There is no data available in the database")
        
        if st.button("View data"):
            cursor.execute("select company_name,name,designation,contact,email,website,area,city,state,pincode from card_detail")
            updated_df1 = pd.DataFrame(cursor.fetchall(),columns=["Company_Name","Name","Designation","Contact","Email","Website","Area","City","State","PinCode"])
            st.write(updated_df1)