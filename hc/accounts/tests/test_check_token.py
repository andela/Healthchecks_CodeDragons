from django.contrib.auth.hashers import make_password
from hc.test import BaseTestCase
from django.test import tag


class CheckTokenTestCase(BaseTestCase): 

    def setUp(self):
        super(CheckTokenTestCase, self).setUp()
        self.profile.token = make_password("secret-token")
        self.profile.save()

    def test_it_shows_form(self):
        r = self.client.get("/accounts/check_token/alice/secret-token/")
        self.assertContains(r, "You are about to log in")

    def test_it_redirects(self):
        r = self.client.post("/accounts/check_token/alice/secret-token/")
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, "/checks/")

     # After login, token should be blank
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.token, "")

    ### Login and test it redirects already logged in
    @tag("test_redirects_if_already_logged_in")
    def test_redirects_if_already_logged_in(self):
        self.client.login(username="ben@example.org", password="password")

        form = {"email": "ben@example.org"}
        result = self.client.post("/accounts/profile/", form)
        assert result.status_code == 302
        self.assertRedirects(result, '/accounts/login/?next=/accounts/profile/')



    ### Login with a bad token and check that it redirects
    def test_redirects_login_with_bad_token(self):
        r = self.client.post("/accounts/check_token/alice/bad-token/")
        self.assertRedirects(r, "/accounts/login/")


    ### Any other tests?
