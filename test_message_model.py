"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow, Like
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
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        m1 = Message(text="test_text1", user_id=u1.id)
        m2 = Message(text="test_text2", user_id=u1.id)

        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id
        self.m2_id = m2.id

        like1 = Like.create_like(user_id = self.u2_id, message_id = self.m1_id)
        db.session.commit()

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

    def test_message_failure(self):
        """Test blank messages/no user attempts"""
        blank_message = Message(user_id = self.u1_id)
        db.session.add(blank_message)
        self.assertRaises(IntegrityError, db.session.commit)
        db.session.rollback()

        #FIXME: can split this part into a separate test
        nouser_message = Message(text="beautiful text")
        db.session.add(nouser_message)
        self.assertRaises(IntegrityError, db.session.commit)

    def test_message_relationships(self):
        """test whether new messages accurately link up to user model"""
        m1 = Message.query.get(self.m1_id)
        m2 = Message.query.get(self.m2_id)
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertEqual(m1.user.id, self.u1_id)
        self.assertEqual(m2.user.id, self.u1_id)
        self.assertEqual(len(u1.messages), 2)
        self.assertEqual(len(u2.messages), 0)

    def test_like_relationships(self):
        """Test whether user 2 has liked messages, message 1 has users_like"""
        m1 = Message.query.get(self.m1_id)
        m2 = Message.query.get(self.m2_id)
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertEqual(len(m1.users_like), 1)
        self.assertEqual(len(m2.users_like), 0)
        self.assertEqual(len(u1.liked_messages), 0)
        self.assertEqual(len(u2.liked_messages), 1)

    def test_duplicate_like(self):
        """Test whether likes fail when the same user likes a message twice"""
        duplicate_like = Like.create_like(user_id = self.u2_id, message_id = self.m1_id)
        self.assertRaises(IntegrityError, db.session.commit)

        ###You can also imagine we did:
        # duplicate = Like(user_id = self.u2_id, message_id = self.m1_id)
        # u2.liked_messages.append(duplicate)

