""" Changes made include:
    - import client Module 
    - import auth/user Module 
    - import django.test/ tag module for testing individual files
    - set alice in the setUp() so we can have access to the user alice from every test case
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from hc.api.models import Channel, Check
from hc.test import BaseTestCase
from django.test import tag


class ApiAdminTestCase(BaseTestCase):

    
    def setUp(self):
        super(ApiAdminTestCase, self).setUp()
        alice = User.objects.create_user(username="alice@example.org", password="password", is_staff=True, is_superuser=True)
        ### Set Alice to be staff and superuser and save her :)
        
    @tag("pushB")
    def test_it_shows_channel_list_with_pushbullet(self):
        
        self.client.login(username="alice@example.org", password="password")

        ch = Channel(user=self.alice, kind="pushbullet", value="test-token")
        ch.save()

        ### Assert for the push bullet
        Channel.objects.filter(kind="pushbullet")
        self.assertEqual(ch.kind, "pushbullet")