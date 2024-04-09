from flask import Flask, render_template, request, redirect, session, url_for
from geopy.geocoders import Nominatim
from flask_sqlalchemy import SQLAlchemy
import time
from pprint import pprint
import random, smtplib

import json
from difflib import get_close_matches
import base64
import os

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new_users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///new_users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.secret_key = 's_secret'

app.secret_key = 's_secret'

db = SQLAlchemy()
db.init_app(app)

app1 = Nominatim(user_agent="tutorial")

def get_address_by_location(latitude, longitude, language="en"):
    coordinates = f"{latitude}, {longitude}"
    time.sleep(1)
    try:
        return app1.reverse(coordinates, language=language).raw
    except:
        return get_address_by_location(latitude, longitude)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    phone_number = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    gender = db.Column(db.String(100))
    password = db.Column(db.String(100))
    profile_photo = db.Column(db.BLOB)

class Companies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    c_name = db.Column(db.String(50))
    c_image = db.Column(db.String(200))
    c_def = db.Column(db.String(3000))
    c_rating = db.Column(db.Integer)
    c_location = db.Column(db.String(50))
    c_emp_count = db.Column(db.Integer)
    c_industry = db.Column(db.String(50))
    c_reviews = db.Column(db.String(15))
    c_job = db.Column(db.String(50))
    c_link = db.Column(db.String(200))
    c_address = db.Column(db.String(200))
    c_zones = db.Column(db.Integer)

with app.app_context():
    db.create_all()


@app.route("/", methods= ['GET', 'POST'])
def home():
    if request.method == "POST":
         latitude = request.form['latitude']
         longitude = request.form['longitude']
         address = get_address_by_location(latitude, longitude)
        #  city = address['address']['city']
        #  session['city'] = city
         return redirect(url_for('one_star'))
        #  return render_template("1.html", city = city)
    return render_template("1.html")

@app.route("/courses")
def courses():
    return render_template("courses.html")


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        print(user.email)
        if user and user.password == password:
            # profile_photo_data_uri = None
            # profile_photo_data_uri = "data:image/jpeg;base64," + base64.b64encode(user.profile_photo).decode('utf-8')

            if user.profile_photo is not None:
                profile_photo_data_uri = "data:image/jpeg;base64," + base64.b64encode(user.profile_photo).decode('utf-8')
            else:
                 profile_photo_data_uri = None


            print("Login Success")
            return render_template("1.html", login=True, u_name = user.name, u_email = user.email, u_number = user.phone_number, u_profile = profile_photo_data_uri)
        else:
            print("login not success")
            return redirect('/registration')

    return render_template("login.html")


@app.route("/registration", methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        gender = request.form['gender']
        password = request.form['password']
        new_user = User(name=name, phone_number= phone, email=email, gender=gender, password=password)
        db.session.add(new_user)
        db.session.commit()
        return render_template("login.html", registered = True)

    return render_template("registration1.html")

my_email = os.environ.get('MY_EMAIL')
password = os.environ.get('MY_EMAIL_PASSWORD')

@app.route("/forget_password", methods=['GET', 'POST'])
def forget_password():
    if request.method == "POST":
        if 'email_for_otp' in request.form:
            email = request.form["email_for_otp"]
            otp = ''.join(random.choices('0123456789', k=6))
            session['otp'] = otp  
            print(otp, type(otp))
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=my_email, to_addrs=email, msg=f"Subject:InternSculpt\n\nFint the otp to change the password: {otp}")
            return render_template("forget pass page.html", otp_generated=True, email_otp_sent=email)
        else:
            user_otp = request.form.get('otp_by_user')
            otp = session.get('otp') 
            if user_otp == otp:
                return render_template("change_password.html")
            else:
                print('otp check not success')
                return render_template("forget pass page.html", error=True)

    return render_template("forget pass page.html")

@app.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if request.method == "POST":
        email = request.form['emailPassword']
        confirmPass = request.form.get("confirmPassword")

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = confirmPass
            db.session.commit()
            print("password changed!")
            return render_template("login.html")
        else:
            return render_template("registration1.html", unregistered= True)
    return render_template("change_password.html")



def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

def find_best_match(user_question: str, questions:list[str]) -> str | None:
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.3)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]
        

def chat_bot(user_input: str):
    knowledge_base: dict = load_knowledge_base("knowledge_base.json")
    best_match: str | None = find_best_match(user_input, [q["question"] for q in knowledge_base['questions']])

    if best_match:
        answer: str = get_answer_for_question(best_match, knowledge_base)
        return answer
    else:
        return "I didn't understand. please contact customer care!"
            
chat_que = []
chat_ans = []

@app.route("/chatbot", methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        question = request.form['chat_que']
        chat_que.append(question)
        answer = chat_bot(question)
        chat_ans.append(answer)
        return render_template("chatbot.html", questions=chat_que, answers=chat_ans)
    return render_template("chatbot.html")


@app.route("/companies", methods=['GET', 'POST'])
def one_star():
    if request.method == "POST":
        # location = request.form['loc']
        industry = request.form['industry']
        reviews = request.form['reviews']
        job = request.form['job']
        zone = request.form['zone']
        print(industry, reviews, job, zone)
        print(type(industry), type(reviews), type(zone))
        if zone != "all":
            filtered_companies = Companies.query.filter_by(c_industry = industry,c_zones = zone).all()
            print("if executed")
        else:
            Weblinksfiltered_companies = Companies.query.filter_by(c_industry = industry, c_zones = zone).all()
            print("else exucrg")
        return render_template("companies.html", filter_companies = filtered_companies, filter=True)
    all_companies = db.session.query(Companies).all()
    return render_template("companies.html", all_the_companies = all_companies)


@app.route("/navigate", methods=['GET','POST'])
def navigate():
    if request.method == 'POST':
        star = request.form['starinput']
        print(star)
        return render_template(f'{star}.html')
    return render_template("1.html")

@app.route("/add_company")
def add():
    name = "Magic Clickz"
    image = "Feedbox.png"
    defi = "Choose Magic Clickz as your digital marketing agency and propel your business to new heights with our award-winning digital marketing services and proprietary technology platform. Magic Clickz is a tech-enabled digital marketing solutions provider, and we create custom strategies for each of our clients based on their needs and goals."
    rating = 4.8
    location = "Indore"
    count = 6000
    industry = "Marketing & Advertising "
    review = "4.8 Star Ratings"
    job_type ="Graphic Designer"
    link = "https://feedbox.co.in/"

    company = Companies(c_name=name, c_image = image, c_def=defi, c_rating = rating, c_location = location, c_emp_count = count, c_industry = industry, c_reviews= review, c_job = job_type, c_link = link)
    db.session.add(company)
    db.session.commit()
    return 'data added successfully'


@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if request.method == "POST":
        user_name = request.form['d_name']
        user_email = request.form['d_email']
        user_number = request.form['d_number']
        user_profile = request.form['d_profile']
        print(f"details:", user_name, user_email, user_number, user_profile)
        return render_template("dashboard.html", name = user_name, email = user_email, number = user_number, profile = user_profile)
    print("if not executed")
    return render_template("dashboard.html")

@app.route("/update_profile", methods=['GET', 'POST'])
def update_profile():
    if request.method == "POST":
        if "user_name" in request.form:
            u_name = request.form['user_name']
            u_email = request.form['user_email']
            u_number = request.form['user_number']
            u_profile = request.form['user_profile']
            return render_template("update-profile.html", name = u_name, email = u_email, number = u_number, profile= u_profile)
        else:
            user_update_email = request.form['update_email']
            user_update_mobile = request.form['update_mobile']
            user_old_password = request.form['update_old_password']
            user_new_password = request.form['update_new_password']
            user_profile_photo = request.files['update_pic']

            print(user_update_email, user_update_mobile, user_old_password, user_new_password, user_profile_photo)

            update_user = User.query.filter_by(email = user_update_email).first()
            if update_profile:
                print("profile found")
                print(update_user.name)
                image_data = user_profile_photo.read()
                if update_user.password == user_old_password:
                    update_user.password = user_new_password
                    update_user.phone_number = user_update_mobile
                    update_user.profile_photo = image_data
                    db.session.commit()
                    print("profile has been updated")
                    return redirect("/login")
                else:
                    print("old password do not match")
            else:
                print("user not found")    

    return render_template("update-profile.html")



@app.route("/job-listing")
def job_listing():
    return render_template("job-listing.html")

@app.route("/job-description-accenture")
def job_description1():
    return render_template("job-description1_accenture.html")

@app.route("/job-description-infosys")
def job_description2():
    return render_template("job-description2_infosys.html")

@app.route("/job-description-yash")
def job_description3():
    return render_template("job-description3_yash.html")

@app.route("/job-description-hcl")
def job_description4():
    return render_template("job-description4_hcl.html")

@app.route("/job-description-wipro")
def job_description5():
    return render_template("job-description5_wipro.html")

@app.route("/job-description-techmahindra")
def job_description6():
    return render_template("job-description6_techmahindra.html")

@app.route("/job-description-capgemini")
def job_description7():
    return render_template("job-description7_capgemini.html")

@app.route("/job-description-deloitte")
def job_description8():
    return render_template("job-description8_deloitte.html")

@app.route("/job-description-dxc")
def job_description9():
    return render_template("job-description9_dxc.html")

@app.route("/job-description-infobeans")
def job_description10():
    return render_template("job-description10_infobeans.html")

@app.route("/job-description-impetus")
def job_description11():
    return render_template("job-description11_impetus.html")

@app.route("/job-description-deqode")
def job_description12():
    return render_template("job-description12_deqode.html")

@app.route("/job-description-cognizant")
def job_description13():
    return render_template("job-description13_cognizant.html")

@app.route("/job-description-rws")
def job_description14():
    return render_template("job-description14_rws.html")

@app.route("/job-description-immersive")
def job_description15():
    return render_template("job-description15_immersive.html")




@app.route("/playlist")
def playlist():
    return render_template("playlist.html")


@app.route("/css_tutorial")
def css_playlist():
    return render_template("playlist-1.html")


if __name__ == '__main__':
    app.run(debug=False)


