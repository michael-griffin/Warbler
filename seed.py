"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db
from models import User, Message, Follow, Like

db.drop_all()
db.create_all()

with open('generator/users.csv') as users:
    db.session.bulk_insert_mappings(User, DictReader(users))

with open('generator/messages.csv') as messages:
    db.session.bulk_insert_mappings(Message, DictReader(messages))

with open('generator/follows.csv') as follows:
    db.session.bulk_insert_mappings(Follow, DictReader(follows))

db.session.commit()

like1 = Like.create_like(1, 322) #political red message by rgeorge
like2 = Like.create_like(2, 322) #politcal red message
like3 = Like.create_like(2, 200) #former hospital message by john05

db.session.commit()
