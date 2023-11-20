"""User model tests."""

# run these tests like:
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, bcrypt, User, Message, Follow, Like
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


class UserModelTestCase(TestCase):
    def setUp(self):
        #Oddly, like delete and message delete need to be included here when
        #running ALL test suites in succession for pytest. Regular unittest handled
        #this fine, which was odd.
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Confirm """
        u1 = User.query.get(self.u1_id)

        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)


    def test_is_following(self):
        """Test whether is_following checks follower
        status of user.following"""
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertEqual(u1.is_following(u2), False)
        u1.following.append(u2)
        db.session.commit()

        self.assertEqual(u1.is_following(u2), True)


    def test_is_followed_by(self):
        """Test whether is_followed_by checks
        follower status of user.followers"""
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertEqual(u1.is_followed_by(u2), False)
        u1.followers.append(u2)
        db.session.commit()

        self.assertEqual(u1.is_followed_by(u2), True)

    def test_user_signup(self):
        """Test whether we can successfully make a new user with valid credentials"""

        new_user = User.signup("jimbob", "jimbob@gmail.com", "password1")
        db.session.commit()
        self.assertTrue(bcrypt.check_password_hash(new_user.password, "password1"))

    def test_failed_signup(self):
        """Test failed sign-ups from bad password/already taken username"""
        try:
            bad_user = User.signup("jimbob", "jimbob@gmail.com")
        except TypeError as exc:
            self.assertIsInstance(exc, TypeError)

        duplicate_user = User.signup("u1", "u11@email.com", "password1", None)
        self.assertRaises(IntegrityError, db.session.commit)


    def test_authenticate_valid(self):
        """Test if authenticate returns user given valid credentials."""
        u1 = User.query.get(self.u1_id)
        user = User.authenticate(u1.username, "password")

        self.assertEqual(user, u1)

    def test_authenticate_invalid(self):
        """Test if authenticate returns False given invalid credentials."""
        u1 = User.query.get(self.u1_id)

        login_attempt = User.authenticate("incorrect_username", "password")
        self.assertFalse(login_attempt)

        login_attempt = User.authenticate(u1.username, "bad_password")
        self.assertFalse(login_attempt)