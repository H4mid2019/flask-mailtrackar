from flask import Flask, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import os
import threading
import urllib.request
import json

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": 'foo@gmail.com',# change this to your email address
    "MAIL_PASSWORD": 'supersecret_password' # change this to your email password
}
app.config.update(mail_settings)
mail = Mail(app)


class ContactForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=True)
    data = db.Column(db.String(400), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.email


body = ''

@app.route('/', methods=['GET'])
def index():
    # ip = request.headers['X-Forwarded-For'].split(',')[0] # with cloudflare
    ip = request.headers['X-Forwarded-For']
    with urllib.request.urlopen("https://geolocation-db.com/jsonp/"+ip) as url:
        ipinfo = json.loads(url.read().decode().split("(")[1].strip(")"))
    mmeta = "--Country : {}\n--State : {}\n--City : {}\n--IP : {}\n--user-agent : {}\n".format(ipinfo['country_name'],ipinfo['state'],ipinfo['city'],ip, request.headers['User-Agent'])
    email = request.args.get('email')
    new_contact = ContactForm(email=email, data=mmeta)
    db.session.add(new_contact)
    db.session.commit()
    global body
    body = "--Email = {}\nInfo \n {}".format(email, mmeta)
    threading.Thread(name="retriever", target=sender).start()
    return send_file('img.png', mimetype='image/png')


def sender():
    global body
    with app.app_context():
        msg = Message(
            subject='EmailOpened',
            sender=app.config.get("MAIL_USERNAME"),# You can change this or set MAIL_DEFAULT_SENDER and use that here or directly type the sender here
            recipients=['receiver@foo.com', ], # receiver of notification emails
            body=body
        )
        mail.send(msg)

    return


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
