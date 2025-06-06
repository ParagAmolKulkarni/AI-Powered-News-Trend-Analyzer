from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Headline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    topic = db.Column(db.String(50), nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)