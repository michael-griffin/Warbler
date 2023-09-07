"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        #db.session.flush()
        db.session.commit()

        m1 = Message(text="m1-text", user_id=u1.id)
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



class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)
            Message.query.filter_by(text="Hello").one()

    def test_display_new_message_form(self):
        """Test whether the form to add a new message shows up"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Add my message!', html)

    def test_fail_when_logged_out(self):
        """If there is no current logged in user, no messages should be added."""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            no_message = Message.query.filter_by(text="Hello").one_or_none()
            self.assertIsNone(no_message)


class MessageShowViewTestCase(MessageBaseViewTestCase):
    def test_show_message(self):
        """If there is a logged in user, show message details"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            url = f"/messages/{self.m1_id}"

            resp = c.get(url)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("m1-text", html)

            self.assertIn("Follow", html)
            self.assertIn("star-fill", html) #Check for filled star on message 1

            url = f"/messages/{self.m2_id}"
            resp = c.get(url, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertNotIn("m1-text", html)
            self.assertIn('bi-star"', html) #Check for unfilled star on message 2

    def dont_show_when_logged_out(self):
        """If there is no current logged in user, message details shouldn't be shown."""
        with self.client as c:
            url = f"/messages/{self.m1_id}"
            resp = c.get(url, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_delete_message(self):
        """test whether a logged in user can successfully delete a message and
        clear its likes"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            post_url = f"/messages/{self.m1_id}/delete"
            resp = c.post(post_url, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertNotIn("m1-text", html)
            self.assertIn("test_text2", html)

            self.assertEqual(len(Like.query.all()), 0)
            self.assertIsNone(Message.query.get(self.m1_id))


    def test_fail_when_logged_out(self):
        """If there is no current logged in user, no messages should be deleted."""
        with self.client as c:
            post_url = f"/messages/{self.m1_id}/delete"
            resp = c.post(post_url, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

            message = Message.query.get(self.m1_id)
            self.assertEqual(message.id, self.m1_id)









# class LikeViewTestCase(MessageBaseViewTestCase):
#     def test_add_like(self):
#         """Test liking another users' message"""

#     def test_toggle_like_off(self):
#         """Test removing a like from a message that was previously liked"""
#         #like1 = Like.create_like(user_id = self.u2_id, message_id = self.m1_id)