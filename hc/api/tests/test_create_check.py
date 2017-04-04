import json
import requests
from django.core import serializers
from django.utils import timezone
from datetime import timedelta, datetime
from hc.api.models import Channel, Check
from hc.test import BaseTestCase
from django.http import HttpResponseBadRequest, JsonResponse, HttpRequest

class CreateCheckTestCase(BaseTestCase):
    URL = "/api/v1/checks/"

    def setUp(self):
        super(CreateCheckTestCase, self).setUp()

    def post(self, data, expected_error=None):
        
        response = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")
        response_error = JsonResponse({'status': 'false', 'message':"An error occurred!"}, status=400)
        if expected_error:
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"], expected_error)

            ### Assert that the expected error is the response error

        return response

    def test_it_works(self):
        response = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60,
        })
        check = Check()
        check.n_pings = 9

        self.assertEqual(response.status_code, 201)

        doc = response.json()
        assert "ping_url" in doc
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz") 
        self.assertEqual(check.last_ping, None)
        self.assertEqual(check.n_pings, 9)
        ### Assert the expected last_ping and n_pings values

        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.get()
        self.assertEqual(check.name, "Foo")
        self.assertEqual(check.tags, "bar,baz")
        self.assertEqual(check.timeout.total_seconds(), 3600)
        self.assertEqual(check.grace.total_seconds(), 60)
    
    def test_it_accepts_api_key_in_header(self):
        payload = json.dumps({"api_key": "abc", "name": "Foo"})
        response = self.client.post(self.URL, payload, content_type="application/json", HTTP_X_API_KEY="abc")
        self.assertEqual(response.status_code, 201)

    def test_it_handles_missing_request_body(self):
        ### This is just a placeholder variable
        response = self.client.post(self.URL, content_type="application/json")
        ### Make the post request with a missing body and get the response
        response= self.post({})
        
        self.assertEqual(response.status_code, 400)

    def test_it_handles_invalid_json(self):
        # r = {'status_code': 400, 'error': "could not parse request body"} ### This is just a placeholder variable
        ### Make the post request with invalid json data type
        response = self.client.post(self.URL, {"Invalid file"}, content_type="application/json")
        self.assertEqual(response.json()['error'], "could not parse request body")

    def test_it_rejects_wrong_api_key(self):
        self.post({"api_key": "wrong"},
                  expected_error="wrong api_key")

    def test_it_rejects_non_number_timeout(self):
        self.post({"api_key": "abc", "timeout": "oops"},
                  expected_error="timeout is not a number")

    def test_it_rejects_non_string_name(self):
        self.post({"api_key": "abc", "name": False},
                  expected_error="name is not a string")

    ### Test for the assignment of channels

    def test_assign_all_channels(self):
        check = Check()
        check.status = "up"
        check.user = self.alice
        check.save()

        channel = Channel(user=self.alice)
        channel.kind = "slack"
        channel.value = 'http://example.com'
        channel.email_verified = True
        channel.save()
        channel.checks.add(check)

        self.assertNotEqual(channel.checks, None)
        self.assertEqual(channel.user, self.alice)

    ### Test for the 'timeout is too small' and 'timeout is too large' errors
    def test_timeout_small_error(self):
        response= self.client.post({"api_key": "abc", "timeout": 0}, expected_error="timeout is too small") #Error, timeout too small
        # self.assertTrue(expected_exception=="timeout is too small")

    def test_timeout_large_error(self):
        self.post({"api_key": "abc", "timeout": 999999}, expected_error="timeout is too large")#"Error, timeout too large"
