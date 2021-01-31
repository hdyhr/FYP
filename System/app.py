import pandas as pd
import numpy as np
import pdfkit
import time
import datetime
from jinja2 import Environment, FileSystemLoader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

#secret key
app.secret_key = 'system'

# database connection (done)
mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="fyp"
)

mysql = MySQL(app)
mycursor = mydb.cursor()

# create file_name table in database (done)
mycursor.execute("CREATE TABLE IF NOT EXISTS reports (admin_report VARCHAR(255), customer_report VARCHAR(255))")

FILE_PATH_FOLDER = 'D:\FYP\FYP\System'
path = "D:\FYP\Drivers\chromedriver.exe"

# run in background with no pop-up (done)
#options = Options()
#options.headless = True

# default page shown when running system
@app.route("/", methods=["GET", "POST"])
def default():
    return render_template("default.html")

# route to login page if user is admin
@app.route("/admin", methods=["GET", "POST"])
def admin():
    #IM HERE
    msg = ""
    if request.method == "POST":
        req = request.form
        username = req.get("usrname")
        password = req.get("psw")
        
        #check if account exists in db
        mycursor.execute('SELECT * FROM admin_accounts WHERE username = %s AND password = %s', (username, password))
        #fetch the result
        account = mycursor.fetchone()
        print(account)

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]

            return redirect(url_for('home'))
        
        else:
            msg = 'Incorrect Username/Password'

    return render_template("login.html", msg=msg)

# route to forgetpw page when admin forgetpw
@app.route("/forgetpw", methods=["GET", "POST"])
def forgetpw():
    msg=""
    if request.method == "POST" and 'email' in request.form:

        email = request.form['email']
        mycursor.execute('SELECT * FROM admin_accounts WHERE email = %s', (email,))
        account = mycursor.fetchone()

        if account:
            session['verified'] = True
            session['email'] = account[3]
            session['id'] = account[0]

            return redirect(url_for('newpw'))

        else:
            msg = "invalid user"

    return render_template('forgetpw.html', msg=msg)

# route to newpw page to change pw
@app.route("/newpw", methods=["GET", "POST"])
def newpw():
    msg = ""
    if 'verified' in session:
        if request.method == "POST":
            req = request.form

            pw1 = req.get("psw1")
            pw2 = req.get("psw2")
            id = session['id']

            if pw1 == pw2:
                mycursor.execute('UPDATE admin_accounts SET password = %s WHERE id = %s', (pw2, id))

                return redirect(url_for('changedpw'))
            else:
                msg = "Password does not match"
            

    return render_template("newpw.html", msg=msg)

# route to confirmation of pw change
@app.route("/changedpw", methods=["GET", "POST"])
def changedpw():
    return render_template("changedpw.html")

# route to customer report page when user is customer
@app.route("/customer", methods=["GET", "POST"])
def customer():
    customer_reportList = []
    df = pd.read_sql_query("SELECT customer_report FROM reports", mydb)
    
    for x in df.index:
        customer_reports = df['customer_report'][x]
        customer_reportList.append(customer_reports)            
    
    env = Environment(loader=FileSystemLoader('./'))
    view_report = env.get_template('System//templates//customerreport.html')

    custtemp_vars = {"customer_reportList" : customer_reportList}
    view_cust_out = view_report.render(custtemp_vars)
    return view_cust_out    

# route  to home page when admin login
@app.route("/admin/home", methods=["GET", "POST"])
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    
    return redirect(url_for('admin'))

# route to view reports page
@app.route("/admin/viewreport", methods=["GET", "POST"])
def viewreport():
    if 'loggedin' in session:
        admin_reportList = []
        df = pd.read_sql_query("SELECT admin_report FROM reports", mydb)
        
        for x in df.index:
            admin_reports = df['admin_report'][x]
            admin_reportList.append(admin_reports)
            
        
        env = Environment(loader=FileSystemLoader('./'))
        view_report = env.get_template('System//templates//viewreport.html')

        admintemp_vars = {"admin_reportList" : admin_reportList}
        view_out = view_report.render(admintemp_vars)
        return view_out
    else:
        return redirect(url_for('admin'))    

# route to view customer reports page
@app.route("/admin/viewcustomerreport", methods=["GET", "POST"])
def viewcustomerreport():
    if 'loggedin' in session:
        customer_reportList = []
        df = pd.read_sql_query("SELECT customer_report FROM reports", mydb)
        
        for x in df.index:
            customer_reports = df['customer_report'][x]
            customer_reportList.append(customer_reports)            
        
        env = Environment(loader=FileSystemLoader('./'))
        view_report = env.get_template('System//templates//viewcustomerreport.html')

        custtemp_vars = {"customer_reportList" : customer_reportList}
        view_cust_out = view_report.render(custtemp_vars)
        return view_cust_out
    else:
        return redirect(url_for('admin'))

# route to logout page
@app.route("/admin/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    print(session)

    return redirect(url_for('admin'))

# generate function (done)
@app.route("/admin/generate", methods=["GET", "POST"])
def generate():
    # Check if user is loggedin
    if 'loggedin' in session:
        # create agoda_data table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS agoda_data")
        mycursor.execute("CREATE TABLE agoda_data (hotel_name VARCHAR(255), hotel_location VARCHAR(255), rating VARCHAR(255), country VARCHAR(255), group_name VARCHAR(255), room_type VARCHAR(255), stay VARCHAR(1000), year VARCHAR(4))")

        # create agoda_ratings table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS agoda_ratings")
        mycursor.execute("CREATE TABLE agoda_ratings (hotel_id INT NOT NULL AUTO_INCREMENT, hotel_name VARCHAR(255), cleanliness DECIMAL(3,1), facilities DECIMAL(3,1), location DECIMAL(3,1), room_comfort DECIMAL(3,1), service DECIMAL(3,1), value DECIMAL(3,1), average_rating DECIMAL(3,1), PRIMARY KEY(hotel_id))")

        # create google ads table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS google_ads")
        mycursor.execute("CREATE TABLE google_ads (google_clicks INT(10), google_impression INT(10), google_cost DECIMAL(7,2), click_through_rate DECIMAL(5,2), cost_per_click DECIMAL(5,2))")

        # create facebook campaign table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS facebook_campaign")
        mycursor.execute("CREATE TABLE facebook_campaign (fb_clicks INT(10), fb_linkclick INT(10), fb_amt DECIMAL(7,2), fb_impression INT(10), CPM DECIMAL(10,2), CTR DECIMAL(5,2), CPC DECIMAL(5,2), LCTR DECIMAL(5,2), CPLC DECIMAL(5,2))")

        # create booking_data table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS booking_data")
        mycursor.execute("CREATE TABLE booking_data (hotel_name VARCHAR(255), hotel_location VARCHAR(255), rating VARCHAR(255), country VARCHAR(255), group_name VARCHAR(255), room_type VARCHAR(255), stay VARCHAR(1000), year VARCHAR(4))")

        # create booking_ratings table in database (done)
        mycursor.execute("DROP TABLE IF EXISTS booking_ratings")
        mycursor.execute("CREATE TABLE booking_ratings (hotel_id INT NOT NULL AUTO_INCREMENT, hotel_name VARCHAR(255), cleanliness DECIMAL(3,1), facilities DECIMAL(3,1), location DECIMAL(3,1), room_comfort DECIMAL(3,1), service DECIMAL(3,1), value DECIMAL(3,1), average_rating DECIMAL(3,1),  PRIMARY KEY(hotel_id))")

        if request.method == "POST":
            req = request.form

            # hotel_name
            search = req.get("search")

            # GoogleAd
            googleAdClick = req.get("googleAdClick")
            googleImp = req.get("googleImp")
            googleAdCost = req.get("googleAdCost")

            google = []
            if(googleAdClick and googleImp and googleAdCost != ""):            
                click_through_rate = (int(googleAdClick) / int(googleImp)) * 100 #%
                cost_per_click = float(googleAdCost) / int(googleAdClick) #$
                gooAd = [googleAdClick, googleImp, googleAdCost, click_through_rate, cost_per_click]
                google.append(gooAd)            
            else:
                googleAdClick = 0
                googleImp = 0
                googleAdCost = 0
                click_through_rate = 0
                cost_per_click = 0 
                gooAd = [googleAdClick, googleImp, googleAdCost, click_through_rate, cost_per_click]
                google.append(gooAd)        
            # save into database google_ads table (done)
            try:
                sql = "INSERT INTO google_ads (google_clicks, google_impression, google_cost, click_through_rate, cost_per_click) VALUES (%s, %s, %s, %s, %s)"
                mycursor.executemany(sql, google)
                mydb.commit()
                print("Google Ads data inserted successfully")
            except:
                print("Unable to insert Google Ads Data as no full data was given")

            
            # FacebookCampaign
            FbClick = req.get("FbClick")
            FbClickLink = req.get("FbClickLink")
            FbAmtSpent = req.get("FbAmtSpent")
            FbImp = req.get("FbImp")

            facebook = []
            if(FbClick and FbClickLink and FbAmtSpent and FbImp != ""):
                CPM = (float(FbAmtSpent) / int(FbImp)) * 1000 #$
                CTR = (int(FbClick) / int(FbImp)) * 100 #%
                CPC = float(FbAmtSpent) / int(FbClick) #$
                LCTR = (int(FbClickLink) / int(FbImp)) * 100 #%
                CPLC = float(FbAmtSpent) / int(FbClickLink) #$
                fbcam = [FbClick, FbClickLink, FbAmtSpent, FbImp, CPM, CTR, CPC, LCTR, CPLC]
                facebook.append(fbcam)            
            else:
                FbClick = 0
                FbClickLink = 0
                FbAmtSpent = 0
                FbImp = 0
                CPM = 0
                CTR = 0
                CPC = 0
                LCTR = 0
                CPLC = 0
                fbcam = [FbClick, FbClickLink, FbAmtSpent, FbImp, CPM, CTR, CPC, LCTR, CPLC]
                facebook.append(fbcam)
            # save into database google_ads table (done)
            try:
                sql = "INSERT INTO facebook_campaign (fb_clicks, fb_linkclick, fb_amt, fb_impression, CPM, CTR, CPC, LCTR, CPLC) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.executemany(sql, facebook)
                mydb.commit()
                print("Facebook Campaign data inserted successfully")
            except:
                print("Unable to insert Facebook Campaign Data as no full data was given")


            # start of AGODA.COM
            driver = webdriver.Chrome(path)
            driver.get("https://www.agoda.com/en-sg/")

            elem = driver.find_element_by_xpath('//input[@class="SearchBoxTextEditor SearchBoxTextEditor--autocomplete"]')
            elem.clear()
            elem.send_keys(search)
            elem.send_keys(Keys.ARROW_DOWN)

            # wait for the first dropdown option to appear and click it (done)
            try:
                first_option = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "Suggestion__text")))
            finally:
                first_option.click()
                driver.implicitly_wait(10)

            # click search button (done)
            element = driver.find_element_by_xpath('//*[@id="SearchBoxContainer"]/div[2]/button')
            driver.execute_script("arguments[0].click();", element)

            # click the hotel  (done)
            driver.implicitly_wait(10)
            element = driver.find_element_by_xpath('//h3[@class="PropertyCard__HotelName"]')
            driver.execute_script("arguments[0].click();", element)

            # switch to the new tab (done)
            driver.switch_to.window(driver.window_handles[1])
            search_qeury = driver.current_url
            driver.get(search_qeury)

            print("scroll down to reviews section ")
            # add a method to click the most recent (done)
            select_recent = Select(driver.find_element_by_id("review-sort-id"))
            select_recent.select_by_value('1')
            print("clicked most recent")

            # need to loop the first few pages to scrape data ? (done)
            page_num = driver.find_elements_by_class_name('Review-paginator-numbers')

            hotel_name = driver.find_element_by_class_name('HeaderCerebrum__Name').text

            hotel_location = driver.find_element_by_class_name('HeaderCerebrum__Location').text

            # array to store data from agoda (done)
            data_details = []

            for x in range(0, 10):

                data = driver.find_elements_by_class_name('Review-comment')

                for each_review in data:
                    try:
                        rating = each_review.find_elements_by_class_name('Review-comment-leftHeader')[0].text
                        country = each_review.find_elements_by_class_name('Review-comment-reviewer')[0].text
                        group_name = each_review.find_elements_by_class_name('Review-comment-reviewer')[1].text
                        room_type = each_review.find_elements_by_class_name('Review-comment-reviewer')[2].text
                        stay = each_review.find_elements_by_class_name('Review-comment-reviewer')[3].text

                    except:
                        rating = ""
                        country = ""
                        group_name = ""
                        room_type = ""
                        stay = ""

                    year = stay[-4:]

                    # Saving review info (done)
                    review_info = [hotel_name, hotel_location, rating, country, group_name, room_type, stay, year]

                    # append into data_details (done)
                    data_details.append(review_info)

                # insert into database table (done)
                try:
                    sql = "INSERT INTO agoda_data (hotel_name, hotel_location, rating, country, group_name, room_type, stay, year) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    mycursor.executemany(sql, data_details)
                    mydb.commit()
                except:
                    print("cant be inserted")

                print(mycursor.rowcount, "was inserted.")

                data_details.clear()

                # click next page (done)
                element = driver.find_element_by_xpath('//i[@class="ficon ficon-24 ficon-carrouselarrow-right"]')
                driver.execute_script("arguments[0].click();", element)
            
            # add method to get ratings of the main hotel (done)
            rating_details = []

            try:
                hotel_name = driver.find_element_by_class_name('HeaderCerebrum__Name').text

                clean_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[1]/span[2]')[0]
                cleanliness = clean_element.text

                facilities_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[2]/span[2]')[0]
                facilities = facilities_element.text

                location_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[3]/span[2]')[0]
                location = location_element.text

                room_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[4]/span[2]')[0]
                room_comfort = room_element.text

                service_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[5]/span[2]')[0]
                service = service_element.text

                value_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[6]/span[2]')[0]
                value = value_element.text

                print("scraped main hotel rating")

            except:
                backup = driver.find_element_by_xpath('//*[@id="reviewSection"]/div[2]/span[2]')
                driver.execute_script("arguments[0].click();", backup)

                hotel_name = driver.find_element_by_class_name('HeaderCerebrum__Name').text

                clean_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[1]/span[2]')[0]
                cleanliness = clean_element.text

                facilities_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[2]/span[2]')[0]
                facilities = facilities_element.text

                location_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[3]/span[2]')[0]
                location = location_element.text

                room_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[4]/span[2]')[0]
                room_comfort = room_element.text

                service_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[5]/span[2]')[0]
                service = service_element.text

                value_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[6]/span[2]')[0]
                value = value_element.text

                print("scraped main hotel backup rating")

            average_rating = (float(cleanliness) + float(facilities) + float(location) + float(room_comfort) + float(service) + float(value)) / 6

            # Saving ratings info (done)
            ratings = [hotel_name, cleanliness, facilities, location, room_comfort, service, value, average_rating]

            # append into ratings (done)
            rating_details.append(ratings)

            # save into database hotel_ratings table (done)
            try:
                sql = "INSERT INTO agoda_ratings (hotel_name, cleanliness, facilities, location, room_comfort, service, value, average_rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.executemany(sql, rating_details)
                mydb.commit()
                print("successfully save main hotel rating")

            except:
                print("unsuccessfully save main hotel rating")

            # click recommended hotel (done)
            driver.implicitly_wait(10)
            recommended_element = driver.find_element_by_xpath('//*[@id="recommended-properties-body"]/table/tbody/tr[6]/td[3]/button')
            driver.execute_script("arguments[0].click();", recommended_element)

            # switch to the new tab (done)
            driver.switch_to.window(driver.window_handles[2])
            search_qeury = driver.current_url
            driver.get(search_qeury)

            # clear list (done)
            rating_details.clear()

            # add method to get ratings of recommended hotel (done)
            try:
                hotel_name = driver.find_element_by_class_name('HeaderCerebrum__Name').text

                clean_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[1]/span[2]')[0]
                cleanliness = clean_element.text

                facilities_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[2]/span[2]')[0]
                facilities = facilities_element.text

                location_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[3]/span[2]')[0]
                location = location_element.text

                room_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[4]/span[2]')[0]
                room_comfort = room_element.text

                service_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[5]/span[2]')[0]
                service = service_element.text

                value_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[6]/span[2]')[0]
                value = value_element.text

                print("scraped recommended hotel rating")

            except:
                backup = driver.find_element_by_xpath('//*[@id="reviewSection"]/div[2]/span[2]')
                driver.execute_script("arguments[0].click();", backup)

                hotel_name = driver.find_element_by_class_name('HeaderCerebrum__Name').text

                clean_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[1]/span[2]')[0]
                cleanliness = clean_element.text

                facilities_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[2]/span[2]')[0]
                facilities = facilities_element.text

                location_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[3]/span[2]')[0]
                location = location_element.text

                room_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[4]/span[2]')[0]
                room_comfort = room_element.text

                service_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[5]/span[2]')[0]
                service = service_element.text

                value_element = driver.find_elements_by_xpath('//*[@id="reviewSection"]/div[3]/div[1]/div/div[2]/div[1]/div/div[6]/span[2]')[0]
                value = value_element.text

                print("scraped recommended hotel backup rating")

            average_rating = (float(cleanliness) + float(facilities) + float(location) + float(room_comfort) + float(service) + float(value)) / 6

            # Saving ratings info (done)
            ratings = [hotel_name, cleanliness, facilities, location, room_comfort, service, value, average_rating]

            # append into ratings (done)
            rating_details.append(ratings)

            # save into database hotel_ratings table (done)
            try:
                sql = "INSERT INTO agoda_ratings (hotel_name, cleanliness, facilities, location, room_comfort, service, value, average_rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.executemany(sql, rating_details)
                mydb.commit()
                print("successfully saved recommended hotel rating")

            except:
                print("unsuccessfully save recommended hotel rating")

            print("AGODA done")

            #Booking.com STARTS
            driver = webdriver.Chrome(path)
            driver.get("https://www.booking.com/")

            elem2 = driver.find_element_by_id('ss')
            elem2.clear()
            elem2.send_keys(search)
            elem2.send_keys(Keys.ARROW_DOWN)

            # wait for the first dropdown option to appear and click it (done)
            try:
                first_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "search_hl_name")))
            finally:
                first_option.click()
                driver.implicitly_wait(10)

            # click search button (done)
            element = driver.find_element_by_xpath('//button[@class="sb-searchbox__button "]')
            driver.execute_script("arguments[0].click();", element)

            # click the hotel  (done)
            driver.implicitly_wait(10)
            element = driver.find_element_by_class_name('sr-hotel__name')
            driver.execute_script("arguments[0].click();", element)

            # switch to the new tab (done)
            driver.switch_to.window(driver.window_handles[1])
            search_qeury = driver.current_url
            driver.get(search_qeury)

            hotel_name_element = driver.find_element_by_xpath('//*[@id="hp_hotel_name"]')   
            hotel_name = hotel_name_element.text

            hotel_location_element = driver.find_element_by_xpath('//*[@id="showMap2"]/span[1]')
            hotel_location = hotel_location_element.text

            element1 = driver.find_element_by_xpath('//*[@id="show_reviews_tab"]')
            driver.execute_script("arguments[0].click();", element1)
            time.sleep(10)

            rating_details2= []

            try:
                clean_element = driver.find_elements_by_xpath('//*[@id="review_list_score"]/div[4]/div/ul/li[3]/div/span[2]')[0]
                cleanliness = clean_element.text

                facilities_element = driver.find_elements_by_xpath('//*[@id="review_list_score"]/div[4]/div/ul/li[2]/div/span[2]')[0]
                facilities = facilities_element.text

                location_element = driver.find_elements_by_xpath('//*[@id="review_list_score"]/div[4]/div/ul/li[6]/div/span[2]')[0]
                location = location_element.text

                room_element = driver.find_elements_by_xpath('//*[@id="review_list_score"]/div[4]/div/ul/li[4]/div/span[2]')[0]
                room_comfort = room_element.text

                service_element = driver.find_elements_by_xpath(' //*[@id="review_list_score"]/div[4]/div/ul/li[1]/div/span[2]')[0]
                service = service_element.text

                value_element = driver.find_elements_by_xpath('//*[@id="review_list_score"]/div[4]/div/ul/li[5]/div/span[2]')[0]
                value = value_element.text     
                
                print("scraped booking rating")
            
            except:
                print("Ratings not found")

            booking_average = ""

            avg = [cleanliness, facilities, location, room_comfort, service, value]
            print(avg)

            booking_average = (float(cleanliness) + float(facilities) + float(location) + float(room_comfort) + float(service) + float(value)) / 6 
        
            # Saving ratings info (done)
            ratings2 = [hotel_name, cleanliness, facilities, location, room_comfort, service, value, booking_average] 

            # append into ratings (done)
            rating_details2.append(ratings2)
            print(rating_details2)

            try:          
                sql = "INSERT INTO booking_ratings (hotel_name, cleanliness, facilities, location, room_comfort, service, value, average_rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.executemany(sql, rating_details2)
                mydb.commit()
                print("successfully saved booking rating")

            except:
                print("unsuccessfully save booking rating")        

            #click date newest to oldest
            select_newest = Select(driver.find_element_by_id("review_sort"))
            select_newest.select_by_value("f_recent_desc")

            search_qeury = driver.current_url
            driver.get(search_qeury)

            booking_datas = []
            for x in range(0,10):
                try:
                    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "review_list_new_item_block")))
                    print("found it")

                    #click date newest to oldest
                    select_newest = Select(driver.find_element_by_id("review_sort"))
                    select_newest.select_by_value("f_recent_desc")

                except:
                    print("cant find review section")
                
                data1 = driver.find_elements_by_class_name('review_list_new_item_block')
                time.sleep(10)

                for each_data in data1:
                    try:
                        rating = each_data.find_elements_by_class_name('bui-review-score__badge')[0].text
                        country = each_data.find_elements_by_class_name('bui-avatar-block__subtitle')[0].text
                        room_type = each_data.find_elements_by_class_name('bui-list__body')[0].text
                        group_name = each_data.find_elements_by_class_name('bui-list__body')[2].text
                        stay = each_data.find_elements_by_class_name('bui-list__body')[1].text
                        year = stay[-4:]

                        booking = [hotel_name,hotel_location,rating,country,group_name,room_type,stay,year]
                        booking_datas.append(booking)

                    except:
                        rating = ""
                        country = ""
                        room_type = ""
                        group_name = ""
                        stay = ""
                        year = ""
                                        
                try:
                    sql = "INSERT INTO booking_data (hotel_name, hotel_location, rating, country, group_name, room_type, stay, year) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    mycursor.executemany(sql, booking_datas)
                    mydb.commit()
                except:
                    print("cant be inserted")

                booking_datas.clear()
            
                #click next page (done)
                element = driver.find_element_by_class_name('pagenext')
                driver.execute_script("arguments[0].click();", element)
                time.sleep(10)

            print("Booking DONE")

            return redirect(url_for('downloadreport'))
        return render_template("generate.html", username=session['username'])

    else:
        return redirect(url_for('logout'))

#download reports
@app.route("/admin/download", methods=["GET", "POST"])
def downloadreport():
    if 'loggedin' in session:
        #Generating Report
        env = Environment(loader=FileSystemLoader('./'))
        template = env.get_template('System//templates//adminReport.html')
        template1 = env.get_template('System//templates//custReport.html')

        #hotel_name
        h_name = pd.read_sql_query('SELECT hotel_name FROM agoda_data', mydb)
        hname = pd.DataFrame(h_name, columns=['hotel_name'])
        hotel_name = hname['hotel_name'][0]

        #recommended hotel_name
        reco_h_name = pd.read_sql_query('SELECT hotel_name FROM agoda_ratings', mydb)
        reco_hotel_name = pd.DataFrame(reco_h_name, columns=['hotel_name'])
        recommended_hotel_name = reco_hotel_name['hotel_name'][1]
        print(recommended_hotel_name)

        #hotel_location
        h_location = pd.read_sql_query('SELECT hotel_location FROM agoda_data', mydb)
        hloc = pd.DataFrame(h_location, columns=['hotel_location'])
        hotel_location = hloc['hotel_location'][0]

        #reviews_count
        agoda_review = pd.read_sql_query('SELECT COUNT(rating) FROM agoda_data WHERE rating IS NOT NULL AND year=(YEAR(CURDATE())-1)', mydb)
        rcount = pd.DataFrame(agoda_review, columns=['COUNT(rating)'])
        reviews_count = rcount['COUNT(rating)'][0]

        #bookings_by_month
        #Jan_Bookings
        jan = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%january%' AND year=(YEAR(CURDATE())-1)", mydb)
        jan_count = pd.DataFrame(jan, columns=['COUNT(stay)'])
        jan_bookings = jan_count['COUNT(stay)'][0]

        #Feb_Bookings
        feb = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%february%' AND year=(YEAR(CURDATE())-1)", mydb)
        feb_count = pd.DataFrame(feb, columns=['COUNT(stay)'])
        feb_bookings = feb_count['COUNT(stay)'][0]

        #Mar_Bookings
        mar = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%march%' AND year=(YEAR(CURDATE())-1)", mydb)
        mar_count = pd.DataFrame(mar, columns=['COUNT(stay)'])
        mar_bookings = mar_count['COUNT(stay)'][0]

        #Apr_Bookings
        apr = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%april%' AND year=(YEAR(CURDATE())-1)", mydb)
        apr_count = pd.DataFrame(apr, columns=['COUNT(stay)'])
        apr_bookings = apr_count['COUNT(stay)'][0]

        #May_Bookings
        may = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%may%' AND year=(YEAR(CURDATE())-1)", mydb)
        may_count = pd.DataFrame(may, columns=['COUNT(stay)'])
        may_bookings = may_count['COUNT(stay)'][0]

        #Jun_Bookings
        jun = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%june%' AND year=(YEAR(CURDATE())-1)", mydb)
        jun_count = pd.DataFrame(jun, columns=['COUNT(stay)'])
        jun_bookings = jun_count['COUNT(stay)'][0]

        #July_Bookings
        july = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%july%' AND year=(YEAR(CURDATE())-1)", mydb)
        july_count = pd.DataFrame(july, columns=['COUNT(stay)'])
        july_bookings = july_count['COUNT(stay)'][0]

        #Aug_Bookings
        aug = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%august%' AND year=(YEAR(CURDATE())-1)", mydb)
        aug_count = pd.DataFrame(aug, columns=['COUNT(stay)'])
        aug_bookings = aug_count['COUNT(stay)'][0]

        #Sept_Bookings
        sept = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%september%' AND year=(YEAR(CURDATE())-1)", mydb)
        sept_count = pd.DataFrame(sept, columns=['COUNT(stay)'])
        sept_bookings = sept_count['COUNT(stay)'][0]

        #Oct_Bookings
        oct = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%october%' AND year=(YEAR(CURDATE())-1)", mydb)
        oct_count = pd.DataFrame(oct, columns=['COUNT(stay)'])
        oct_bookings = oct_count['COUNT(stay)'][0]

        #Nov_Bookings
        nov = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%november%' AND year=(YEAR(CURDATE())-1)", mydb)
        nov_count = pd.DataFrame(nov, columns=['COUNT(stay)'])
        nov_bookings = nov_count['COUNT(stay)'][0]

        #DEC_Bookings
        dec = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%december%' AND year=(YEAR(CURDATE())-1)", mydb)
        dec_count = pd.DataFrame(dec, columns=['COUNT(stay)'])
        dec_bookings = dec_count['COUNT(stay)'][0]

        #Agoda_Room_Types
        agoda_room = pd.read_sql_query("SELECT room_type AS 'Room Type', COUNT(hotel_name) AS 'Total Number Of Bookings' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY room_type ORDER BY COUNT(hotel_name) DESC LIMIT 3", mydb)

        # best room type from agoda
        a_b_r = pd.read_sql_query("SELECT room_type FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY room_type ORDER BY COUNT(hotel_name) DESC LIMIT 1" , mydb)
        a_best_room = pd.DataFrame(a_b_r, columns=['room_type'])
        agoda_best_room = a_best_room['room_type'][0]


        #1_night
        one = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%1 night%' AND year=(YEAR(CURDATE())-1)", mydb)
        one_night_count = pd.DataFrame(one, columns=['COUNT(stay)'])
        one_night = one_night_count['COUNT(stay)'][0]

        #2_nights
        two = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%2 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        two_night_count = pd.DataFrame(two, columns=['COUNT(stay)'])
        two_night = two_night_count['COUNT(stay)'][0]

        #3_nights
        three = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%3 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        three_night_count = pd.DataFrame(three, columns=['COUNT(stay)'])
        three_night = three_night_count['COUNT(stay)'][0]

        #4_nights
        four = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%4 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        four_night_count = pd.DataFrame(four, columns=['COUNT(stay)'])
        four_night = four_night_count['COUNT(stay)'][0]

        #5_nights
        five = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%5 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        five_night_count = pd.DataFrame(five, columns=['COUNT(stay)'])
        five_night = five_night_count['COUNT(stay)'][0]

        #6_nights
        six = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%6 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        six_night_count = pd.DataFrame(six, columns=['COUNT(stay)'])
        six_night = six_night_count['COUNT(stay)'][0]

        #7_nights
        seven = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%7 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        seven_night_count = pd.DataFrame(seven, columns=['COUNT(stay)'])
        seven_night = seven_night_count['COUNT(stay)'][0]

        #8_nights
        eight = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '%8 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        eight_night_count = pd.DataFrame(eight, columns=['COUNT(stay)'])
        eight_night = eight_night_count['COUNT(stay)'][0]

        #9_nights
        nine = pd.read_sql_query("SELECT COUNT(stay) FROM agoda_data WHERE stay LIKE '9 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        nine_night_count = pd.DataFrame(nine, columns=['COUNT(stay)'])
        nine_night = nine_night_count['COUNT(stay)'][0]

        # agoda best night 
        a_b_n = pd.read_sql_query("SELECT SUBSTRING(stay, 7, 9) AS 'nights' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY 'nights' ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        a_best_night = pd.DataFrame(a_b_n, columns=['nights'])
        agoda_best_night = a_best_night['nights'][0]

        #Agoda_Group_Types
        group_type = pd.read_sql_query("SELECT group_name AS 'Group Type', COUNT(hotel_name) AS 'Frequency' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY group_name ORDER BY COUNT(hotel_name) DESC", mydb)

        # agoda best group
        a_b_g = pd.read_sql_query("SELECT group_name AS 'Group Type' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY group_name ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        a_best_grp = pd.DataFrame(a_b_g, columns=['Group Type'])
        agoda_best_group = a_best_grp['Group Type'][0]

        #exceptional
        a_exceptional = pd.read_sql_query("SELECT COUNT(rating) FROM agoda_data WHERE rating LIKE '%exceptional%' AND year=(YEAR(CURDATE())-1)", mydb)
        exceptional_count = pd.DataFrame(a_exceptional, columns=['COUNT(rating)'])
        exceptional = exceptional_count['COUNT(rating)'][0]

        #excellent
        a_excellent = pd.read_sql_query("SELECT COUNT(rating) FROM agoda_data WHERE rating LIKE '%excellent%' AND year=(YEAR(CURDATE())-1)", mydb)
        excellent_count = pd.DataFrame(a_excellent, columns=['COUNT(rating)'])
        excellent = excellent_count['COUNT(rating)'][0]

        #very good 
        a_very_good = pd.read_sql_query("SELECT COUNT(rating) FROM agoda_data WHERE rating LIKE '%very good%' AND year=(YEAR(CURDATE())-1)", mydb)
        very_good__count = pd.DataFrame(a_very_good, columns=['COUNT(rating)'])
        very_good =very_good__count['COUNT(rating)'][0]

        #good 
        a_good = pd.read_sql_query("SELECT COUNT(rating) FROM agoda_data WHERE rating LIKE '%good%' AND year=(YEAR(CURDATE())-1)", mydb)
        good_count = pd.DataFrame(a_good, columns=['COUNT(rating)'])
        good = good_count['COUNT(rating)'][0]

        #below expectation
        a_below_expectation = (int(reviews_count) - int(exceptional)- int(excellent)- int(very_good)- int(good))

        # agoda country
        a_country = pd.read_sql_query("SELECT SUBSTRING_INDEX(country, ' ', -1) AS 'Countries', COUNT(hotel_name) AS 'Frequency' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY Countries ORDER BY COUNT(hotel_name) DESC LIMIT 3", mydb)

        #BOOKING REPORT STARTS HEREEEEEEEEEEEEEE
        #b_reviews
        book_reviews = pd.read_sql_query('SELECT COUNT(rating) FROM booking_data WHERE rating IS NOT NULL AND year=(YEAR(CURDATE())-1)', mydb)
        b_reviews_count = pd.DataFrame(book_reviews, columns=['COUNT(rating)'])
        b_reviews = b_reviews_count['COUNT(rating)'][0]

        #Booking.com Bookings by Month
        #b_jan
        b_jan = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%January%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_jan_count = pd.DataFrame(b_jan, columns=['COUNT(stay)'])
        b_jan_bookings = b_jan_count['COUNT(stay)'][0]

        #b_feb
        b_feb = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%February%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_feb_count = pd.DataFrame(b_feb, columns=['COUNT(stay)'])
        b_feb_bookings = b_feb_count['COUNT(stay)'][0]

        #b_mar
        b_mar = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%March%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_mar_count = pd.DataFrame(b_mar, columns=['COUNT(stay)'])
        b_mar_bookings = b_mar_count['COUNT(stay)'][0]

        #b_apr
        b_apr = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%April%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_apr_count = pd.DataFrame(b_apr, columns=['COUNT(stay)'])
        b_apr_bookings = b_apr_count['COUNT(stay)'][0]

        #b_may
        b_may = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%May%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_may_count = pd.DataFrame(b_may, columns=['COUNT(stay)'])
        b_may_bookings = b_may_count['COUNT(stay)'][0]

        #b_jun
        b_jun = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%June%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_jun_count = pd.DataFrame(b_jun, columns=['COUNT(stay)'])
        b_jun_bookings = b_jun_count['COUNT(stay)'][0]

        #b_jul
        b_jul = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%July%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_jul_count = pd.DataFrame(b_jul, columns=['COUNT(stay)'])
        b_jul_bookings = b_jul_count['COUNT(stay)'][0]

        #b_aug
        b_aug = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%August%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_aug_count = pd.DataFrame(b_aug, columns=['COUNT(stay)'])
        b_aug_bookings = b_aug_count['COUNT(stay)'][0]

        #b_sep
        b_sep = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%September%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_sep_count = pd.DataFrame(b_sep, columns=['COUNT(stay)'])
        b_sep_bookings = b_sep_count['COUNT(stay)'][0]

        #b_oct
        b_oct = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%October%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_oct_count = pd.DataFrame(b_oct, columns=['COUNT(stay)'])
        b_oct_bookings = b_oct_count['COUNT(stay)'][0]

        #b_nov
        b_nov = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%november%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_nov_count = pd.DataFrame(b_nov, columns=['COUNT(stay)'])
        b_nov_bookings = b_nov_count['COUNT(stay)'][0]

        #b_dec
        b_dec = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%december%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_dec_count = pd.DataFrame(b_dec, columns=['COUNT(stay)'])
        b_dec_bookings = b_dec_count['COUNT(stay)'][0]

        #b_room_types
        b_room_types = pd.read_sql_query("SELECT room_type as 'Room Type', COUNT(hotel_name) AS 'Total Number of Bookings' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY room_type ORDER BY COUNT(hotel_name) DESC LIMIT 3", mydb)

        # booking best room type
        b_b_r = pd.read_sql_query("SELECT room_type FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY room_type ORDER BY COUNT(hotel_name) DESC LIMIT 1" , mydb)
        b_best_room = pd.DataFrame(b_b_r, columns=['room_type'])
        booking_best_room = b_best_room['room_type'][0]

        #NIGHTS
        #b_one
        b_one = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%1 night%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_one_count = pd.DataFrame(b_one, columns=['COUNT(stay)'])
        b_one_night = b_one_count['COUNT(stay)'][0]

        #b_two
        b_two = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%2 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_two_count = pd.DataFrame(b_two, columns=['COUNT(stay)'])
        b_two_night = b_two_count['COUNT(stay)'][0]

        #b_three
        b_three = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%3 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_three_count = pd.DataFrame(b_three, columns=['COUNT(stay)'])
        b_three_night = b_three_count['COUNT(stay)'][0]

        #b_four
        b_four = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%4 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_four_count = pd.DataFrame(b_four, columns=['COUNT(stay)'])
        b_four_night = b_four_count['COUNT(stay)'][0]

        #b_five
        b_five = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%5 night%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_five_count = pd.DataFrame(b_five, columns=['COUNT(stay)'])
        b_five_night = b_five_count['COUNT(stay)'][0]

        #b_six
        b_six = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%6 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_six_count = pd.DataFrame(b_six, columns=['COUNT(stay)'])
        b_six_night = b_six_count['COUNT(stay)'][0]

        #b_seven
        b_seven = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%7 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_seven_count = pd.DataFrame(b_seven, columns=['COUNT(stay)'])
        b_seven_night = b_seven_count['COUNT(stay)'][0]

        #b_eight
        b_eight = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%8 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_eight_count = pd.DataFrame(b_eight, columns=['COUNT(stay)'])
        b_eight_night = b_eight_count['COUNT(stay)'][0]

        #b_nine
        b_nine = pd.read_sql_query("SELECT COUNT(stay) FROM booking_data WHERE stay LIKE '%9 nights%' AND year=(YEAR(CURDATE())-1)", mydb)
        b_nine_count = pd.DataFrame(b_nine, columns=['COUNT(stay)'])
        b_nine_night = b_nine_count['COUNT(stay)'][0]

        # booking best night 
        b_b_n = pd.read_sql_query("SELECT SUBSTRING_INDEX(stay,' ', 2) AS 'nights' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY 'nights' ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        b_best_night = pd.DataFrame(b_b_n, columns=['nights'])
        booking_best_night = b_best_night['nights'][0]

        #b_group
        b_group = pd.read_sql_query("SELECT group_name, COUNT(hotel_name) AS 'Total Number of Bookings' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY group_name ORDER BY COUNT(hotel_name) DESC", mydb)

        # booking best group
        b_b_g = pd.read_sql_query("SELECT group_name AS 'Group Type' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY group_name ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        b_best_grp = pd.DataFrame(b_b_g, columns=['Group Type'])
        booking_best_group = b_best_grp['Group Type'][0]


        #b_exceptional
        b_excep = pd.read_sql_query("SELECT COUNT(rating) FROM booking_data WHERE rating IS NOT NULL AND rating > 9 AND year=(YEAR(CURDATE())-1)", mydb)
        b_excep_count = pd.DataFrame(b_excep, columns=['COUNT(rating)'])
        b_exceptional = b_excep_count['COUNT(rating)'][0]

        #b_excellent
        b_excel = pd.read_sql_query("SELECT COUNT(rating), rating FROM booking_data WHERE rating IS NOT NULL AND rating BETWEEN 8.1 AND 9.0 AND year=(YEAR(CURDATE())-1)", mydb)
        b_excel_count = pd.DataFrame(b_excel, columns=['COUNT(rating)'])
        b_excellent = b_excel_count['COUNT(rating)'][0]

        #b_very_good
        b_very = pd.read_sql_query("SELECT COUNT(rating) FROM booking_data WHERE rating IS NOT NULL AND rating BETWEEN 7.1 AND 8.0 AND year=(YEAR(CURDATE())-1)", mydb)
        b_very_count = pd.DataFrame(b_very, columns=['COUNT(rating)'])
        b_very_good =b_very_count['COUNT(rating)'][0]

        #b_good 
        b_gd = pd.read_sql_query("SELECT COUNT(rating) FROM booking_data WHERE rating IS NOT NULL AND rating BETWEEN 6.0 AND 7.0 AND year=(YEAR(CURDATE())-1)", mydb)
        b_gd_count = pd.DataFrame(b_gd, columns=['COUNT(rating)'])
        b_good = b_gd_count['COUNT(rating)'][0]

        #b_below
        b_below = (int(b_reviews) - int(b_exceptional)- int(b_excellent)- int(b_very_good)- int(b_good))

        # booking country
        b_country = pd.read_sql_query("SELECT country AS 'Country', COUNT(hotel_name) AS 'Frequency' from booking_data where year=(YEAR(CURDATE())-1) GROUP BY Country ORDER BY COUNT(hotel_name) DESC LIMIT 3", mydb)

        #Google_CLicks
        g_clicks = pd.read_sql_query('SELECT google_clicks FROM google_ads', mydb)
        clicks = pd.DataFrame(g_clicks, columns=['google_clicks'])
        google_clicks = clicks['google_clicks'][0]

        #Google Impression
        g_impression = pd.read_sql_query('SELECT google_impression FROM google_ads', mydb)
        imp = pd.DataFrame(g_impression, columns=['google_impression'])
        google_impression = imp['google_impression'][0]

        #Google Cost
        g_cost = pd.read_sql_query('SELECT google_cost FROM google_ads', mydb)
        cost = pd.DataFrame(g_cost, columns=['google_cost'])
        google_cost = cost['google_cost'][0]

        #Google CTR
        g_ctr = pd.read_sql_query('SELECT click_through_rate FROM google_ads', mydb)
        ctr = pd.DataFrame(g_ctr, columns=['click_through_rate'])
        click_through_rate = ctr['click_through_rate'][0]

        #Google Cost Per Click
        g_cpc = pd.read_sql_query('SELECT cost_per_click FROM google_ads', mydb)
        cpc = pd.DataFrame(g_cpc, columns=['cost_per_click'])
        cost_per_click = cpc['cost_per_click'][0]

        #fb clicks
        f_clicks = pd.read_sql_query('SELECT fb_clicks FROM facebook_campaign', mydb)
        fclicks = pd.DataFrame(f_clicks, columns=['fb_clicks'])
        fb_clicks = fclicks['fb_clicks'][0]

        #fb link clicks
        f_l_click = pd.read_sql_query('SELECT fb_linkclick FROM facebook_campaign', mydb)
        flink_clicks = pd.DataFrame(f_l_click, columns=['fb_linkclick'])
        fb_link_clicks = flink_clicks['fb_linkclick'][0]

        #fb amount
        f_amt = pd.read_sql_query('SELECT fb_amt FROM facebook_campaign', mydb)
        fb_amt = pd.DataFrame(f_amt, columns=['fb_amt'])
        fb_amount = fb_amt['fb_amt'][0]

        #fb impression
        f_impression = pd.read_sql_query('SELECT fb_impression FROM facebook_campaign', mydb)
        fimpression = pd.DataFrame(f_impression, columns=['fb_impression'])
        fb_impression = fimpression['fb_impression'][0]

        #fb CPM
        fb_cpm = pd.read_sql_query('SELECT CPM FROM facebook_campaign', mydb)
        fcpm = pd.DataFrame(fb_cpm, columns=['CPM'])
        CPM = fcpm['CPM'][0]

        #fb CTR
        fb_ctr = pd.read_sql_query('SELECT CTR FROM facebook_campaign', mydb)
        fctr = pd.DataFrame(fb_ctr, columns=['CTR'])
        CTR = fctr['CTR'][0]

        #fb CPC
        fb_cpc = pd.read_sql_query('SELECT CPC FROM facebook_campaign', mydb)
        fcpc = pd.DataFrame(fb_cpc, columns=['CPC'])
        CPC = fcpc['CPC'][0]

        #fb LCTR
        fb_lctr = pd.read_sql_query('SELECT LCTR FROM facebook_campaign', mydb)
        flctr = pd.DataFrame(fb_lctr, columns=['LCTR'])
        LCTR = flctr['LCTR'][0]

        #fb CPLC
        fb_lcpc = pd.read_sql_query('SELECT CPLC FROM facebook_campaign', mydb)
        fcplc = pd.DataFrame(fb_lcpc, columns=['CPLC'])
        CPLC = fcplc['CPLC'][0]

        #agoda cleanliness 1
        a_clean1 = pd.read_sql_query('SELECT cleanliness FROM agoda_ratings where hotel_id = 1', mydb)
        a_cleanliness1 = pd.DataFrame(a_clean1, columns=['cleanliness'])
        agoda_cleanliness1 = a_cleanliness1['cleanliness'][0]

        #agoda cleanliness 2
        a_clean2 = pd.read_sql_query('SELECT cleanliness FROM agoda_ratings where hotel_id = 2', mydb)
        a_cleanliness2 = pd.DataFrame(a_clean2, columns=['cleanliness'])
        agoda_cleanliness2 = a_cleanliness2['cleanliness'][0]

        #agoda facilities 1
        a_fac1 = pd.read_sql_query('SELECT facilities FROM agoda_ratings where hotel_id = 1', mydb)
        a_facilities1 = pd.DataFrame(a_fac1, columns=['facilities'])
        agoda_facilities1 = a_facilities1['facilities'][0]

        #agoda facilities 2
        a_fac2 = pd.read_sql_query('SELECT facilities FROM agoda_ratings where hotel_id = 2', mydb)
        a_facilities2 = pd.DataFrame(a_fac2, columns=['facilities'])
        agoda_facilities2 = a_facilities2['facilities'][0]

        #agoda location 1
        a_loc1 = pd.read_sql_query('SELECT location FROM agoda_ratings where hotel_id = 1', mydb)
        a_location1 = pd.DataFrame(a_loc1, columns=['location'])
        agoda_location1 = a_location1['location'][0]

        #agoda location 2
        a_loc2 = pd.read_sql_query('SELECT location FROM agoda_ratings where hotel_id = 2', mydb)
        a_location2 = pd.DataFrame(a_loc2, columns=['location'])
        agoda_location2 = a_location2['location'][0]

        #agoda room_comfort 1
        a_r_c1 = pd.read_sql_query('SELECT room_comfort FROM agoda_ratings where hotel_id = 1', mydb)
        a_room_comfort1 = pd.DataFrame(a_r_c1, columns=['room_comfort'])
        agoda_room_comfort1 = a_room_comfort1['room_comfort'][0]

        #agoda room_comfort 2
        a_r_c2 = pd.read_sql_query('SELECT room_comfort FROM agoda_ratings where hotel_id = 2', mydb)
        a_room_comfort2 = pd.DataFrame(a_r_c2, columns=['room_comfort'])
        agoda_room_comfort2 = a_room_comfort2['room_comfort'][0]

        #agoda service 1
        a_serv1 = pd.read_sql_query('SELECT service FROM agoda_ratings where hotel_id = 1', mydb)
        a_service1 = pd.DataFrame(a_serv1, columns=['service'])
        agoda_service1 = a_service1['service'][0]

        #agoda service 2
        a_serv2 = pd.read_sql_query('SELECT service FROM agoda_ratings where hotel_id = 2', mydb)
        a_service2 = pd.DataFrame(a_serv2, columns=['service'])
        agoda_service2 = a_service2['service'][0]

        #agoda value 1
        a_v1 = pd.read_sql_query('SELECT value FROM agoda_ratings where hotel_id = 1', mydb)
        a_value1 = pd.DataFrame(a_v1, columns=['value'])
        agoda_value1 = a_value1['value'][0]

        #agoda value 2
        a_v2 = pd.read_sql_query('SELECT value FROM agoda_ratings where hotel_id = 2', mydb)
        a_value2 = pd.DataFrame(a_v2, columns=['value'])
        agoda_value2 = a_value2['value'][0]

        #agoda average_rating 1
        a_a_r1 = pd.read_sql_query('SELECT average_rating FROM agoda_ratings where hotel_id = 1', mydb)
        a_average_rating1 = pd.DataFrame(a_a_r1, columns=['average_rating'])
        agoda_average_rating1 = a_average_rating1['average_rating'][0]

        #agoda average_rating 2
        a_a_r2 = pd.read_sql_query('SELECT average_rating FROM agoda_ratings where hotel_id = 2', mydb)
        a_average_rating2 = pd.DataFrame(a_a_r2, columns=['average_rating'])
        agoda_average_rating2 = a_average_rating2['average_rating'][0]

        #PROS AND CONS 
        p1 = ""
        if agoda_cleanliness1 > agoda_cleanliness2:
            p1 = "better"
        elif agoda_cleanliness1 == agoda_cleanliness2:
            p1 = "the same"
        else:
            p1 = "deficient"

        p2 = ""
        if agoda_facilities1 > agoda_facilities2:
            p2 = "better"
        elif agoda_facilities1 == agoda_facilities2:
            p2 = "the same"
        else:
            p2 = "deficient"

        p3 = ""
        if agoda_location1 > agoda_location2:
            p3 = "better"
        elif agoda_location1 == agoda_location2:
            p3 = "the same"
        else:
            p3 = "deficient"

        p4 = ""
        if agoda_room_comfort1 > agoda_room_comfort2:
            p4 = "better"
        elif agoda_room_comfort1 == agoda_room_comfort2:
            p4 = "the same"
        else:
            p4 = "deficient"

        p5 = ""
        if agoda_service1 > agoda_service2:
            p5 = "better"
        elif agoda_service1 == agoda_service2:
            p5 = "the same"
        else:
            p5 = "deficient"

        p6 = ""
        if agoda_value1 > agoda_value2:
            p6 = "higher"
        elif agoda_value1 > agoda_value2:
            p6 = "the same"
        else:
            p6 = "lower"

        #booking cleanliness 1
        b_clean1 = pd.read_sql_query('SELECT cleanliness FROM booking_ratings where hotel_id = 1', mydb)
        b_cleanliness1 = pd.DataFrame(b_clean1, columns=['cleanliness'])
        booking_cleanliness1 = b_cleanliness1['cleanliness'][0]

        #booking facilities 1
        b_fac1 = pd.read_sql_query('SELECT facilities FROM booking_ratings where hotel_id = 1', mydb)
        b_facilities1 = pd.DataFrame(b_fac1, columns=['facilities'])
        booking_facilities1 = b_facilities1['facilities'][0]

        #booking location 1
        b_loc1 = pd.read_sql_query('SELECT location FROM booking_ratings where hotel_id = 1', mydb)
        b_location1 = pd.DataFrame(b_loc1, columns=['location'])
        booking_location1 = b_location1['location'][0]

        #booking room_comfort 1
        b_r_c1 = pd.read_sql_query('SELECT room_comfort FROM booking_ratings where hotel_id = 1', mydb)
        b_room_comfort1 = pd.DataFrame(b_r_c1, columns=['room_comfort'])
        booking_room_comfort1 = b_room_comfort1['room_comfort'][0]

        #booking service 1
        b_serv1 = pd.read_sql_query('SELECT service FROM booking_ratings where hotel_id = 1', mydb)
        b_service1 = pd.DataFrame(b_serv1, columns=['service'])
        booking_service1 = b_service1['service'][0]

        #booking value 1
        b_v1 = pd.read_sql_query('SELECT value FROM booking_ratings where hotel_id = 1', mydb)
        b_value1 = pd.DataFrame(b_v1, columns=['value'])
        booking_value1 = b_value1['value'][0]

        #booking average_rating 1
        b_a_r1 = pd.read_sql_query('SELECT average_rating FROM booking_ratings where hotel_id = 1', mydb)
        b_average_rating1 = pd.DataFrame(b_a_r1, columns=['average_rating'])
        booking_average_rating1 = b_average_rating1['average_rating'][0]

        #best website
        msg1 = ""
        if reviews_count > b_reviews:
            msg1 = "www.agoda.com/en-sg/"
        else:
            msg1 = "www.booking.com"

        #agoda best month
        a_b_m = pd.read_sql_query("SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(stay, ' ', -2),' ', 1) AS 'Month' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY SUBSTRING_INDEX(SUBSTRING_INDEX(stay, ' ', -2),' ', 1) ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        a_best_month = pd.DataFrame(a_b_m, columns=['Month'])
        agoda_best_month = a_best_month['Month'][0]

        #booking best month 
        b_b_m = pd.read_sql_query("SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(stay, ' ', -2),' ', 1) AS 'Month' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY SUBSTRING_INDEX(SUBSTRING_INDEX(stay, ' ', -2),' ', 1) ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        b_best_month = pd.DataFrame(b_b_m, columns=['Month'])
        booking_best_month = b_best_month['Month'][0]

        #agoda best country
        a_b_c = pd.read_sql_query("SELECT SUBSTRING_INDEX(country, ' ', -1) AS 'Countries' FROM agoda_data WHERE year=(YEAR(CURDATE())-1) GROUP BY Countries ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        a_best_country = pd.DataFrame(a_b_c, columns=['Countries'])
        agoda_best_country = a_best_country['Countries'][0]

        #booking best country
        b_b_c = pd.read_sql_query("SELECT SUBSTRING_INDEX(country, ' ', -1) AS 'Countries' FROM booking_data WHERE year=(YEAR(CURDATE())-1) GROUP BY Countries ORDER BY COUNT(hotel_name) DESC LIMIT 1", mydb)
        b_best_country = pd.DataFrame(b_b_c, columns=['Countries'])
        booking_best_country = b_best_country['Countries'][0]

        template_vars = {"hotel_name" : hotel_name,
                        "hotel_location": hotel_location,
                        "recommended_hotel_name" : recommended_hotel_name,
                        "reviews_count": reviews_count,
                        "Jan_Bookings" : jan_bookings,
                        "Feb_Bookings" : feb_bookings,
                        "Mar_Bookings" : mar_bookings,
                        "Apr_Bookings" : apr_bookings,
                        "May_Bookings" : may_bookings,
                        "Jun_Bookings" : jun_bookings,
                        "Jul_Bookings" : july_bookings,
                        "Aug_Bookings" : aug_bookings,
                        "Sep_Bookings" : sept_bookings,
                        "Oct_Bookings" : oct_bookings,
                        "Nov_Bookings" : nov_bookings,
                        "Dec_Bookings" : dec_bookings,
                        "Agoda_Room_Types" : agoda_room.to_html(),
                        "one_night" : one_night,
                        "two_night" : two_night,
                        "three_night" : three_night,
                        "four_night" : four_night,
                        "five_night" : five_night,
                        "six_night" : six_night,
                        "seven_night" : seven_night,
                        "eight_night" : eight_night,
                        "nine_night" : nine_night,
                        "Agoda_Group_Types" : group_type.to_html(),
                        "exceptional" :exceptional,
                        "excellent" : excellent,
                        "very_good" : very_good,
                        "good" : good,
                        "below_expectation" : a_below_expectation,
                        "a_country" : a_country.to_html(),
                        "b_reviews" : b_reviews,
                        "b_jan" : b_jan_bookings,
                        "b_feb" : b_feb_bookings,
                        "b_mar" : b_mar_bookings,
                        "b_apr" : b_apr_bookings, 
                        "b_may" : b_may_bookings, 
                        "b_jun" : b_jun_bookings, 
                        "b_jul" : b_jul_bookings, 
                        "b_aug" : b_aug_bookings, 
                        "b_sep" : b_sep_bookings, 
                        "b_oct" : b_oct_bookings,  
                        "b_nov" : b_nov_bookings, 
                        "b_dec" : b_dec_bookings,
                        "b_room_types" : b_room_types.to_html(),
                        "b_one_night" : b_one_night,
                        "b_two_night" : b_two_night,
                        "b_three_night" : b_three_night,
                        "b_four_night" : b_four_night,
                        "b_five_night" : b_five_night,
                        "b_six_night" : b_six_night,
                        "b_seven_night" : b_seven_night,
                        "b_eight_night" : b_eight_night,
                        "b_nine_night" : b_nine_night,
                        "b_group" : b_group.to_html(),
                        "b_exceptional" : b_exceptional,
                        "b_excellent" : b_excellent,
                        "b_very_good" : b_very_good,
                        "b_good" : b_good,
                        "b_below" : b_below,
                        "b_country" : b_country.to_html(),
                        "google_clicks" : google_clicks,
                        "google_impression" : google_impression,
                        "google_cost" : google_cost,
                        "click_through_rate" : click_through_rate,
                        "cost_per_click" : cost_per_click,
                        "fb_clicks" : fb_clicks,
                        "fb_linkclick" : fb_link_clicks,
                        "fb_amt" : fb_amount,
                        "fb_impression" :fb_impression,
                        "cpm" : CPM,
                        "ctr" : CTR,
                        "cpc" : CPC,
                        "lctr" : LCTR,
                        "cplc" : CPLC,
                        "agoda_cleanliness1": agoda_cleanliness1,
                        "agoda_cleanliness2": agoda_cleanliness2,
                        "agoda_facilities1": agoda_facilities1,
                        "agoda_facilities2": agoda_facilities2,
                        "agoda_location1": agoda_location1,
                        "agoda_location2": agoda_location2,                    
                        "agoda_room_comfort1": agoda_room_comfort1,
                        "agoda_room_comfort2": agoda_room_comfort2,
                        "agoda_service1": agoda_service1,
                        "agoda_service2": agoda_service2,
                        "agoda_value1": agoda_value1,
                        "agoda_value2": agoda_value2,
                        "agoda_average_rating1": agoda_average_rating1,
                        "agoda_average_rating2": agoda_average_rating2,
                        "p1" : p1,
                        "p2" : p2,
                        "p3" : p3,
                        "p4" : p4,
                        "p5" : p5,
                        "p6" : p6,
                        "booking_cleanliness1": booking_cleanliness1,
                        "booking_facilities1": booking_facilities1,
                        "booking_location1" : booking_location1,
                        "booking_room_comfort1": booking_room_comfort1,
                        "booking_service1": booking_service1,
                        "booking_value1": booking_value1,
                        "booking_average_rating1": booking_average_rating1,
                        "agoda_best_room": agoda_best_room,
                        "agoda_best_night" : agoda_best_night,
                        "agoda_best_group": agoda_best_group,
                        "agoda_best_month" : agoda_best_month,
                        "agoda_best_country" : agoda_best_country,
                        "booking_best_room": booking_best_room,
                        "booking_best_night" : booking_best_night,
                        "booking_best_group" : booking_best_group,
                        "booking_best_month" : booking_best_month,
                        "booking_best_country" : booking_best_country,
                        "best_website": msg1,
                        }

        html_out = template.render(template_vars)  
        html_out1 = template1.render(template_vars)  

        x = datetime.datetime.now() 
        day = x.strftime("%d") 
        month = x.strftime("%m")  
        year = x.strftime("%Y")
        date = day + "-" + month + "-" + year
        print(date)

        # write html to file
        file_name = hotel_name + " " + date + ".html"
        text_file = open(file_name, "w") 
        text_file.write(html_out) 
        text_file.close()

        # write html1 to file
        file_name1 = 'Customer ' + hotel_name + " " + date +  ".html"
        text_file = open(file_name1, "w") 
        text_file.write(html_out1) 
        text_file.close()

        name = [file_name, file_name1]
        name_list =[]
        name_list.append(name)

        try:
            sql = "INSERT INTO reports (admin_report , customer_report) VALUES (%s, %s)"
            mycursor.executemany(sql, name_list)
            mydb.commit()
        except:
            print("cant be inserted")

        # path_wkhtmltopdf = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        # config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        # pdf_file = hotel_name + '.pdf'
        # pdfkit.from_string(html_out, pdf_file, configuration=config)

        # path_wkhtmltopdf = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
        # config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        # pdf_file = 'Customer ' + hotel_name + '.pdf'
        # pdfkit.from_string(html_out1, pdf_file, configuration=config)

        return redirect(url_for('viewreport'))
    else:
        return redirect(url_for('admin'))


if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run()

