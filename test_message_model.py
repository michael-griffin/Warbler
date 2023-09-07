"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, bcrypt, User, Message, Follow
from sqlalchemy.exc import IntegrityError
# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        m1 = Message(text="test_text1", user_id=u1.id)
        m2 = Message(text="test_text2", user_id=u2.id)

        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id
        self.m2_id = m2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Confirm message model creates expected fields."""
        m1 = Message.query.get(self.m1_id)

        self.assertIsInstance(m1, Message)
        self.assertEqual(m1.text, "test_text1")
        self.assertIsNotNone(m1.timestamp)
        self.assertEqual(m1.user_id, self.u1_id)
        self.assertEqual(len(m1.users_like), 0)

"""
Test relationships user.messages, message.user
test blank message/blank user
test likes
"""