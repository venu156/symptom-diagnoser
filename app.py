import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime

app = Flask(__name__)


UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vamshivolkaji27@gmail.com'
app.config['MAIL_PASSWORD'] = 'dgbyzaqdqjooytlu'
app.config['MAIL_DEFAULT_SENDER'] = 'vamshivolkaji27@gmail.com'

mail = Mail(app)

# App config
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diagnosis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_user_view'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(100))
    phone = db.Column(db.String(15))

class Doctor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(100))
    photo = db.Column(db.String(100)) 

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    symptoms = db.Column(db.String(300))
    status = db.Column(db.String(20), default='Pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='appointments')
    doctor = db.relationship('Doctor', backref='appointments')


@login_manager.user_loader
def load_user(user_id):
    role = session.get('role')
    if role == 'doctor':
        return Doctor.query.get(int(user_id))
    return User.query.get(int(user_id))
# ------------------ CONDITIONS & DIAGNOSIS ------------------
conditions = {
    'Flu': {
        'symptoms': ['fever', 'cough', 'fatigue', 'body aches'],
        'description': 'A viral infection that attacks your respiratory system — your nose, throat, and lungs.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Common Cold': {
        'symptoms': ['cough', 'sore throat', 'runny nose', 'fatigue', 'cold'],
        'description': 'A viral infection of your nose and throat (upper respiratory tract).',
        'stages': ['Early Stage', 'Peak Stage', 'Recovery']
    },
    'Migraine': {
        'symptoms': ['headache', 'nausea', 'sensitivity to light', 'dizziness'],
        'description': 'A primary headache disorder characterized by recurrent headaches that are moderate to severe.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Heart Disease': {
        'symptoms': ['chest pain', 'shortness of breath', 'fatigue', 'dizziness'],
        'description': 'A range of conditions that affect your heart, including coronary artery disease.',
        'stages': ['Stable', 'Critical', 'Emergency']
    },
    'Anemia': {
        'symptoms': ['fatigue', 'dizziness', 'shortness of breath', 'pale skin'],
        'description': 'A condition in which you lack enough healthy red blood cells to carry adequate oxygen to your tissues.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Asthma': {
        'symptoms': ['shortness of breath', 'wheezing', 'chest pain', 'cough'],
        'description': 'A condition in which your airways narrow and swell and may produce extra mucus.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Arthritis': {
        'symptoms': ['joint pain', 'stiffness', 'swelling', 'reduced range of motion'],
        'description': 'Inflammation of one or more of your joints, causing pain and stiffness that can worsen with age.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'COVID-19': {
    'symptoms': ['fever', 'dry cough', 'shortness of breath', 'fatigue', 'loss of taste or smell'],
    'description': 'An infectious disease caused by the SARS-CoV-2 virus, primarily affecting the respiratory system.',
    'stages': ['Asymptomatic', 'Mild', 'Moderate', 'Severe']
    },
    'Allergies': {
        'symptoms': ['sneezing', 'itchy eyes', 'runny nose', 'skin rash'],
       'description': 'An overreaction of the immune system to harmless substances like pollen, dust, or certain foods.',
        'stages': ['Exposure', 'Reaction', 'Resolution']
    },
    'Asthma': {
       'symptoms': ['wheezing', 'shortness of breath', 'chest tightness', 'coughing'],
        'description': 'A chronic condition that inflames and narrows the airways in the lungs, causing breathing difficulties.',
       'stages': ['Mild Intermittent', 'Mild Persistent', 'Moderate Persistent', 'Severe Persistent']
    },
    'Pneumonia': {
        'symptoms': ['cough with phlegm', 'fever', 'chills', 'shortness of breath', 'chest pain'],
       'description': 'An infection that inflames the air sacs in one or both lungs, which may fill with fluid or pus.',
       'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Bronchitis': {
        'symptoms': ['cough with mucus', 'fatigue', 'shortness of breath', 'chest discomfort'],
        'description': 'Inflammation of the bronchial tubes that carry air to and from your lungs.',
        'stages': ['Acute', 'Chronic']
    },
    'Strep Throat': {
        'symptoms': ['sore throat', 'fever', 'swollen lymph nodes', 'pain when swallowing'],
        'description': 'A bacterial infection that can cause throat pain and inflammation.',
        'stages': ['Incubation', 'Symptomatic Stage', 'Recovery']
    },
    'Sinusitis': {
        'symptoms': ['facial pain', 'nasal congestion', 'headache', 'runny nose'],
        'description': 'An inflammation or swelling of the tissue lining the sinuses, which can be caused by infection, allergies, or pollutants.',
        'stages': ['Acute', 'Subacute', 'Chronic']
    },
    'Tuberculosis': {
        'symptoms': ['persistent cough', 'fever', 'night sweats', 'fatigue', 'weight loss'],
        'description': 'A potentially serious infectious disease that mainly affects the lungs, caused by the bacterium Mycobacterium tuberculosis.',
        'stages': ['Latent', 'Active', 'Extrapulmonary']
    },
    'Chronic Obstructive Pulmonary Disease (COPD)': {
        'symptoms': ['chronic cough', 'shortness of breath', 'wheezing', 'fatigue'],
        'description': 'A group of lung diseases that block airflow and make it difficult to breathe.',
        'stages': ['Mild', 'Moderate', 'Severe', 'Very Severe']
    },
    'Emphysema': {
        'symptoms': ['shortness of breath', 'chronic cough', 'fatigue', 'weight loss'],
        'description': 'A type of COPD that involves damage to the air sacs in the lungs, causing shortness of breath.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Pertussis (Whooping Cough)': {
        'symptoms': ['severe coughing fits', 'runny nose', 'fever', 'vomiting after coughing'],
        'description': 'A highly contagious bacterial infection that causes uncontrollable, violent coughing.',
        'stages': ['Catarrhal Stage', 'Paroxysmal Stage', 'Convalescent Stage']
    },
    'Lung Cancer': {
        'symptoms': ['persistent cough', 'chest pain', 'shortness of breath', 'coughing up blood'],
        'description': 'A type of cancer that begins in the lungs, often caused by smoking or exposure to certain toxins.',
        'stages': ['Stage I', 'Stage II', 'Stage III', 'Stage IV']
    },
    'Pulmonary Embolism': {
        'symptoms': ['shortness of breath', 'chest pain', 'cough', 'leg swelling'],
        'description': 'A blockage in one of the pulmonary arteries in your lungs, often caused by blood clots that travel from the legs.',
        'stages': ['Small', 'Moderate', 'Massive']
    },
    'Acute Respiratory Distress Syndrome (ARDS)': {
        'symptoms': ['severe shortness of breath', 'rapid breathing', 'low blood pressure', 'fatigue'],
        'description': 'A life-threatening condition where fluid builds up in the air sacs of the lungs, preventing oxygen from getting to the organs.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Cystic Fibrosis': {
        'symptoms': ['persistent cough', 'frequent lung infections', 'wheezing', 'shortness of breath'],
        'description': 'A genetic disorder that causes severe damage to the lungs, digestive system, and other organs in the body.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Sleep Apnea': {
        'symptoms': ['loud snoring', 'gasping for air during sleep', 'morning headache', 'daytime fatigue'],
        'description': 'A sleep disorder in which breathing repeatedly stops and starts during sleep.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Pulmonary Hypertension': {
        'symptoms': ['shortness of breath', 'chest pain', 'fatigue', 'dizziness'],
        'description': 'A type of high blood pressure that affects the arteries in your lungs and the right side of your heart.',
        'stages': ['Class I', 'Class II', 'Class III', 'Class IV']
    },
    'Sarcoidosis': {
        'symptoms': ['persistent cough', 'shortness of breath', 'chest pain', 'fatigue'],
        'description': 'An inflammatory disease that affects multiple organs in the body, but mostly the lungs and lymph glands.',
        'stages': ['Acute', 'Chronic']
    },
    'Interstitial Lung Disease': {
    'symptoms': ['shortness of breath', 'dry cough', 'fatigue', 'chest discomfort'],
    'description': 'A group of diseases that cause progressive scarring of lung tissue, making it difficult to breathe deeply.',
    'stages': ['Early Stage', 'Progressive Stage', 'Advanced Stage']
    },
    'Chronic Sinusitis': {
        'symptoms': ['nasal congestion', 'facial pain', 'headache', 'reduced sense of smell'],
        'description': 'A prolonged inflammation of the sinuses that can result from infection, allergies, or other factors.',
        'stages': ['Acute', 'Recurrent', 'Chronic']
    },
    'Heart Failure': {
        'symptoms': ['shortness of breath', 'fatigue', 'swelling in legs and ankles', 'persistent cough'],
        'description': 'A chronic condition where the heart doesnt pump blood as well as it should, leading to fluid buildup.',
        'stages': ['Stage A', 'Stage B', 'Stage C', 'Stage D']
    },
    'Coronary Artery Disease': {
        'symptoms': ['chest pain', 'shortness of breath', 'fatigue', 'heart palpitations'],
        'description': 'A condition caused by the buildup of plaque in the coronary arteries, which supply blood to the heart.',
        'stages': ['Stable Angina', 'Unstable Angina', 'Myocardial Infarction']
    },
    'Stroke': {
        'symptoms': ['sudden numbness', 'confusion', 'trouble speaking', 'loss of balance'],
        'description': 'A medical emergency that occurs when the blood supply to part of the brain is interrupted or reduced.',
        'stages': ['Transient Ischemic Attack (TIA)', 'Ischemic Stroke', 'Hemorrhagic Stroke']
    },
    'Arrhythmia': {
        'symptoms': ['palpitations', 'dizziness', 'fainting', 'shortness of breath'],
        'description': 'An irregular heartbeat caused by issues with the electrical signals that control the heartbeat.',
        'stages': ['Atrial Fibrillation', 'Ventricular Tachycardia', 'Ventricular Fibrillation']
    },
    'Peripheral Artery Disease (PAD)': {
        'symptoms': ['leg pain during walking', 'numbness', 'weakness', 'coldness in lower leg or foot'],
        'description': 'A common circulatory problem in which narrowed arteries reduce blood flow to the limbs.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Anemia': {
        'symptoms': ['fatigue', 'weakness', 'pale skin', 'shortness of breath'],
        'description': 'A condition in which you lack enough healthy red blood cells to carry adequate oxygen to your bodys tissues.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Diabetes Mellitus': {
        'symptoms': ['increased thirst', 'frequent urination', 'extreme fatigue', 'blurry vision'],
        'description': 'A chronic disease that occurs when the body cannot properly process food for use as energy.',
        'stages': ['Pre-diabetes', 'Type 1 Diabetes', 'Type 2 Diabetes', 'Gestational Diabetes']
    },
    'Hypothyroidism': {
        'symptoms': ['fatigue', 'weight gain', 'cold intolerance', 'dry skin'],
        'description': 'A condition in which the thyroid gland doesnt produce enough thyroid hormones.',
        'stages': ['Subclinical', 'Mild', 'Moderate', 'Severe']
    },
    'Hyperthyroidism': {
        'symptoms': ['weight loss', 'rapid heartbeat', 'increased appetite', 'sweating'],
        'description': 'A condition where the thyroid gland produces too much thyroid hormone, leading to a fast metabolism.',
        'stages': ['Subclinical', 'Mild', 'Moderate', 'Severe']
    },
    'Hashimoto’s Thyroiditis': {
        'symptoms': ['fatigue', 'weight gain', 'cold intolerance', 'muscle weakness'],
        'description': 'An autoimmune disorder in which the immune system attacks the thyroid gland, leading to hypothyroidism.',
        'stages': ['Early Stage', 'Progressive Stage', 'Advanced Stage']
    },
    'Addison’s Disease': {
        'symptoms': ['fatigue', 'low blood pressure', 'darkening of the skin', 'weight loss'],
        'description': 'A disorder that occurs when the adrenal glands do not produce enough hormones.',
        'stages': ['Primary', 'Secondary', 'Acute Adrenal Crisis']
    },
    'Gastroesophageal Reflux Disease (GERD)': {
        'symptoms': ['heartburn', 'regurgitation', 'difficulty swallowing', 'chest pain'],
        'description': 'A digestive disorder in which stomach acid or bile irritates the food pipe lining.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Irritable Bowel Syndrome (IBS)': {
        'symptoms': ['abdominal pain', 'bloating', 'gas', 'diarrhea or constipation'],
        'description': 'A common disorder that affects the large intestine, leading to abdominal discomfort.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Crohn’s Disease': {
        'symptoms': ['abdominal pain', 'diarrhea', 'weight loss', 'fatigue'],
        'description': 'A chronic inflammatory bowel disease that affects the lining of the digestive tract.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Ulcerative Colitis': {
        'symptoms': ['abdominal pain', 'bloody diarrhea', 'urgent bowel movements', 'fatigue'],
        'description': 'A chronic inflammatory bowel disease that causes inflammation in the digestive tract.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Peptic Ulcer Disease': {
        'symptoms': ['burning stomach pain', 'bloating', 'nausea', 'indigestion'],
        'description': 'Sores that develop on the lining of the stomach, small intestine, or esophagus.',
        'stages': ['Acute', 'Chronic']
    },
    'Gallstones': {
        'symptoms': ['sudden and intense abdominal pain', 'back pain between the shoulder blades', 'nausea', 'vomiting'],
        'description': 'Solid particles that form from bile cholesterol and bilirubin in the gallbladder.',
        'stages': ['Asymptomatic', 'Symptomatic']
    },
    'Acid Reflux': {
        'symptoms': ['heartburn', 'regurgitation', 'chest pain', 'difficult swallowing'],
        'description': 'A chronic digestive condition where stomach acid flows back into the esophagus.',
        'stages': ['Mild', 'Moderate', 'Severe']
    },
    'Diverticulitis': {
        'symptoms': ['abdominal pain', 'fever', 'nausea', 'changes in bowel habits'],
        'description': 'An inflammation or infection of small pouches that can form in the lining of your digestive system.',
        'stages': ['Uncomplicated', 'Complicated']
    },
    'Hepatitis A': {
        'symptoms': ['fatigue', 'nausea', 'abdominal pain', 'loss of appetite'],
        'description': 'A highly contagious liver infection caused by the hepatitis A virus.',
        'stages': ['Incubation', 'Acute Phase', 'Recovery Phase']
    },
    'Hepatitis B': {
        'symptoms': ['fatigue', 'abdominal pain', 'joint pain', 'dark urine'],
        'description': 'A serious liver infection caused by the hepatitis B virus that can become chronic.',
        'stages': ['Acute', 'Chronic']
    },
    'Hepatitis C': {
        'symptoms': ['fatigue', 'jaundice', 'abdominal pain', 'dark urine'],
        'description': 'A liver infection caused by the hepatitis C virus that can lead to chronic liver disease.',
        'stages': ['Acute', 'Chronic']
    },
    'Pancreatitis': {
        'symptoms': ['upper abdominal pain', 'nausea', 'vomiting', 'fever'],
        'description': 'Inflammation of the pancreas that can occur as acute or chronic.',
        'stages': ['Acute', 'Chronic']
    },
    'Kidney Stones': {
        'symptoms': ['severe pain in the side and back', 'blood in urine', 'nausea', 'vomiting'],
        'description': 'Hard mineral deposits formed in the kidneys that can cause pain when passed.',
        'stages': ['Asymptomatic', 'Symptomatic']
    },
    'Chronic Kidney Disease (CKD)': {
        'symptoms': ['fatigue', 'swelling', 'urination changes', 'shortness of breath'],
        'description': 'A gradual loss of kidney function over time, often due to diabetes or high blood pressure.',
        'stages': ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5']
    }
}

def get_diagnosis(user_symptoms):
    user_symptoms = [symptom.lower().strip() for symptom in user_symptoms]
    diagnosis_results = []
    for condition, details in conditions.items():
        matched = set(user_symptoms).intersection(details['symptoms'])
        match_percentage = len(matched) / len(details['symptoms']) * 100
        if match_percentage > 0:
            if match_percentage >= 75:
                stage = details['stages'][2]
            elif match_percentage >= 50:
                stage = details['stages'][1]
            else:
                stage = details['stages'][0]
            diagnosis_results.append({
                'condition': condition,
                'match_percentage': round(match_percentage, 2),
                'stage': stage,
                'description': details['description'],
                'matched_symptoms': list(matched)
            })
    diagnosis_results.sort(key=lambda x: x['match_percentage'], reverse=True)
    return diagnosis_results

# ------------------ ROUTES ------------------
@app.route('/')
def app_details():
    return render_template('app_details.html')

@app.route('/diagnosis_page')
@login_required
def index():
    if session.get('role') != 'user':
        return redirect('/login_user')
    doctors = Doctor.query.all()
    return render_template('index.html', selected_symptoms=["", "", "", ""], diagnosis_results=None, doctors=doctors)

@app.route('/diagnosis', methods=['POST'])
@login_required
def diagnosis():
    if session.get('role') != 'user':
        return redirect('/login_user')
    symptoms = [request.form.get(f'symptom{i+1}', '') for i in range(4)]
    filtered = sorted([s for s in symptoms if s and s.lower() != 'none'])
    results = get_diagnosis(filtered)
    doctors = Doctor.query.all()
    return render_template('index.html', diagnosis_results=results, selected_symptoms=symptoms, doctors=doctors)

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        user = User(username=request.form['username'], email=request.form['email'], password=request.form['password'],phone=request.form['phone'])
        db.session.add(user)
        db.session.commit()
        return redirect('/login_user')
    return render_template('register_user.html')

@app.route('/login_user', methods=['GET', 'POST'])
def login_user_view():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if user:
            session['role'] = 'user'
            login_user(user)
            return redirect('/diagnosis_page')
        flash('Invalid credentials',"error")
    return render_template('login_user.html')

@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        specialization = request.form['specialization']

        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
        else:
            flash("Invalid file format.")
            return redirect(request.url)

        new_doctor = Doctor(
            name=name,
            email=email,
            password=password,
            specialization=specialization,
            photo=filename
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash("Doctor registered successfully.", "success")
        return redirect('/login_doctor')
    return render_template('register_doctor.html')

@app.route('/login_doctor', methods=['GET', 'POST'])
def login_doctor_view():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        doc = Doctor.query.filter_by(email=email).first()

        if doc and check_password_hash(doc.password, password):
            login_user(doc)
            session['role'] = 'doctor'
            return redirect('/doctor_dashboard')
        else:
            flash('Invalid doctor credentials', "error")
    
    return render_template('login_doctor.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None)
    return redirect('/')

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    if session.get('role') != 'user':
        return redirect('/')

    doctor_id = request.form['doctor_id']
    condition = request.form['condition']
    
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        flash('Selected doctor not found.')
        return redirect('/diagnosis_page')

    new_appointment = Appointment(user_id=current_user.id, doctor_id=doctor.id, symptoms=condition)
    db.session.add(new_appointment)
    db.session.commit()

    # Send confirmation email
    msg = Message(subject="Appointment Confirmation",
                  recipients=[current_user.email])
    msg.body = f"""Hello {current_user.username},

Your appointment has been successfully booked with Dr. {doctor.name} for the condition: {condition}.

Doctor Specialization: {doctor.specialization}
Date: {new_appointment.timestamp.strftime('%Y-%m-%d %H:%M')}

Thank you for using Digital Health Assistant for Symtom Diagnosis and Doctor Recommendation System.

Regards,
Healthcare Support Team
"""
    mail.send(msg)

    flash('Appointment booked successfully! A confirmation email has been sent.', "success")
    return redirect('/diagnosis_page')

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if session.get('role') != 'doctor':
        flash("Access denied. Only doctors allowed.")
        return redirect('/')

    doctor = Doctor.query.get(current_user.id)
    if not doctor:
        flash("Doctor not found. Please log in again.")
        return redirect('/login_doctor')

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    return render_template('doctor_dashboard.html', appointments=appointments, doctor=doctor)

@app.route('/suggestions')
def suggestions():
    return render_template('suggestions.html')

# ------------------ MAIN ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)