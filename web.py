from flask import Flask,render_template,request,redirect,url_for,flash,render_template_string,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from torchvision import models, transforms
from PIL import Image
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from flask_mail import Mail,Message
import json
# ResNet setup
resnet = models.resnet18(pretrained=True)
resnet.fc = nn.Identity()  # remove final classification layer
resnet.eval()

# Transformation for input image
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# Extract features from image
def extract_features(image_path):
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)  # add batch dimension
    with torch.no_grad():
        features = resnet(image)
    return features.numpy().flatten()


app = Flask(__name__)
app.secret_key = 'qwertyuiopasdfghjkl'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/lostfound'

# SMTP Process
with open('config.json') as config_file:
    config_data = json.load(config_file)
    app.config.update(config_data)
    mail = Mail(app)

db = SQLAlchemy(app)

class Contactus(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    email = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    dateTime = db.Column(db.DateTime, nullable=False, default=datetime.now)

UPLOAD_FOLDER_LOST = 'static/uploads/lost'
app.config['UPLOAD_FOLDER_LOST'] = UPLOAD_FOLDER_LOST

class LostItem(db.Model):
    __tablename__ = 'lostitem'
    sno = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.String(80),nullable=False)
    item =  db.Column(db.String(80),nullable=False ) 
    location =  db.Column(db.String(120),nullable=False)
    descr =  db.Column(db.String(120))
    email = db.Column(db.String(50), nullable=False)
    date =  db.Column(db.String,nullable=False)
    time =  db.Column(db.String, nullable=False)
    file =  db.Column(db.String(255))

UPLOAD_FOLDER_FOUND = 'static/uploads/found'
app.config['UPLOAD_FOLDER_FOUND'] = UPLOAD_FOLDER_FOUND

class FoundItem(db.Model):
    __tablename__ = 'founditem'
    sno = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.String(80),nullable=False)
    item =  db.Column(db.String(80),nullable=False ) 
    location =  db.Column(db.String(120),nullable=False)
    descr =  db.Column(db.String(120))
    email = db.Column(db.String(50), nullable=False)
    date =  db.Column(db.String,nullable=False)
    time =  db.Column(db.String, nullable=False)
    file =  db.Column(db.String(255))

@app.route("/")
def home():
    return render_template('main.html')

@app.route("/contactUs",methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        entry = Contactus(name = name,email = email,message=message)
        db.session.add(entry)
        db.session.commit()
    return render_template('contactUs.html')

@app.route('/lost', methods=['GET', 'POST'])
def lost():
    if request.method == 'POST':
        name = request.form.get('name')
        item = request.form.get('item')
        location = request.form.get('location')
        descr = request.form.get('descr')
        email = request.form.get('email')
        date = request.form.get('date')
        time = request.form.get('time')

        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER_LOST'], filename))

        entry = LostItem(
            name=name,
            item=item,
            location=location,
            descr=descr,
            email=email,
            date=date,
            time=time,
            file=filename
        )
        db.session.add(entry)
        db.session.commit()
        return render_template_string("""
            <script>
                alert("Lost Item Submitted Successfully");
                window.location.href = "{{ url_for('home') }}";
            </script>
        """)

    return render_template('lost.html')

@app.route('/found', methods=['GET', 'POST'])
def found():
    if request.method == 'POST':
        name = request.form.get('name')
        item = request.form.get('item')
        location = request.form.get('location')
        descr = request.form.get('descr')
        email = request.form.get('email')
        date = request.form.get('date')
        time = request.form.get('time')

        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER_FOUND'], filename))

        entry1 = FoundItem(
            name=name,
            item=item,
            location=location,
            descr=descr,
            email=email,
            date=date,
            time=time,
            file=filename
        )

        found_image_path = os.path.join(app.config['UPLOAD_FOLDER_FOUND'], filename)
        found_features = extract_features(found_image_path)

        lost_items = LostItem.query.all()
        best_match = None
        best_similarity = 0.0

        for lost in lost_items:
            lost_image_path = os.path.join(app.config['UPLOAD_FOLDER_LOST'], lost.file)
            if os.path.exists(lost_image_path):
                lost_features = extract_features(lost_image_path)
                similarity = cosine_similarity(
                    [found_features], [lost_features]
                )[0][0]
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = lost

        # Save FoundItem to DB
        db.session.add(entry1)
        db.session.commit()

        if best_similarity > 0.65:
            try:
                msg = Message(
                subject="Regarding Potential Match For Your Lost Item",
                recipients=[best_match.email],
                body=f"Hello {best_match.name},\n\nA potential match has been found for your lost item {best_match.item}\n\n"
                     f"It was found at {location} on {date} at {time}. Please visit the website for more details.\n"
                     f" \nThank You"
                )
                mail.send(msg)
            except Exception as e:
                print("Mail Send Failed: ",e)

            return render_template_string(f"""
                <script>
                    alert("Found Item Submitted Successfully. Match Found: {best_match.item} at {best_match.location} (Similarity: {best_similarity*100:.2f}%)");
                    window.location.href = "{ url_for('item',item_id = best_match.sno) }";
                </script>
            """)
        else:
            return render_template_string("""
                <script>
                    alert("Found Item Submitted Successfully. No match found.");
                    window.location.href = "{{ url_for('home') }}";
                </script>
            """)
    return render_template('found.html')

@app.route('/item/<int:item_id>', methods=['GET', 'POST'])
def item(item_id):
    matched_item = LostItem.query.get_or_404(item_id)
    return render_template('item.html',item=matched_item)


if __name__ == '__main__':
    app.run(debug=True)
