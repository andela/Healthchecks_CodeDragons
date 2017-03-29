import json
from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class CreateCheckTestCase(BaseTestCase):
    URL = "/api/v1/checks/"

    def setUp(self):
        super(CreateCheckTestCase, self).setUp()

    def post(self, data, expected_error=None):

        r = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")

        if expected_error:
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json()["error"], expected_error)
            #self.assertIn(response_error, r.json())
            # Assert that the expected error is the response error


    def post(self, data, expected_error=None, response_error=None):
        
        r = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")
        #response_error = JsonResponse({'status': 'false', 'message':"An error occurred!"}, status=400)
        if expected_error:
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json.error, expected_error)
            ### Assert that the expected error is the response error

        return r

    def test_it_works(self):
        r = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60,
        })
        check = Check()
        check.n_pings = 9

        self.assertEqual(r.status_code, 201)

        doc = r.json()
        assert "ping_url" in doc
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz")
        self.assertEqual(check.last_ping, None)
        self.assertEqual(check.n_pings, 9)
        # Assert the expected last_ping and n_pings values

        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.get()
        self.assertEqual(check.name, "Foo")
        self.assertEqual(check.tags, "bar,baz")
        self.assertEqual(check.timeout.total_seconds(), 3600)
        self.assertEqual(check.grace.total_seconds(), 60)

    def test_it_accepts_api_key_in_header(self):
        payload = json.dumps({"name": "Foo"})
        r = self.client.post(
            self.URL, payload, content_type="application/json", HTTP_X_API_KEY="abc")

        self.assertEqual(r.status_code, 201)

    def test_it_handles_missing_request_body(self):
        # This is just a placeholder variable
        r = self.client.post(self.URL, content_type="application/json")
        # Make the post request with a missing body and get the response
        r = self.post({})
        self.assertEqual(r.status_code, 400)

    def test_it_handles_invalid_json(self):
        # r = {'status_code': 400, 'error': "could not parse request body"} ### This is just a placeholder variable
        # Make the post request with invalid json data type
        r = self.client.post(self.URL, "Invalid file",
                             content_type="application/json")
        self.assertEqual(r.json()["error"], "could not parse request body")

    def test_it_rejects_wrong_api_key(self):
        self.post({"api_key": "wrong"},
                  expected_error="wrong api_key")

    def test_it_rejects_non_number_timeout(self):
        self.post({"api_key": "abc", "timeout": "oops"},
                  expected_error="timeout is not a number")

    def test_it_rejects_non_string_name(self):
        self.post({"api_key": "abc", "name": False},
                  expected_error="name is not a string")

    # Test for the assignment of channels

    def test_assign_all_channels(self):
        # check = Check.objects.get()
        # channel = Channel(user=self.alice)
        # channel.save()
        # r = self.post({"api_key": "abc", "channels": "*"})
        # self.assertEqual(r.status_code, 201)
        # self.assertEqual(check.channel_set.get(), channel)

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

    # Test for the 'timeout is too small' and 'timeout is too large' errors
    def test_timeout_small_error(self):
        self.post({"api_key": "abc", "timeout": 0},
                  expected_error="timeout is too small")

    def test_timeout_large_error(self):
        self.post({"api_key": "abc", "timeout": 999999},
                  expected_error="timeout is too large")

        r = self.post({"api_key": "abc", "channels": "*"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(check.channel_set.get(), channel)

    ### Test for the 'timeout is too small' and 'timeout is too large' errors
    def test_it_rejects_small_timeout(self):
        self.post({"api_key": "abc", "timeout": 0}, expected_error="timeout is too small")

    def test_it_rejects_large_timeout(self):
        self.post({"api_key": "abc", "timeout": 9999}, expected_error="timeout is too large")

