from django.test import Client, TestCase, tag
from hc.api.models import Check, Ping


class PingTestCase(TestCase):

    def setUp(self):
        super(PingTestCase, self).setUp()
        self.check = Check.objects.create()

    def test_it_works(self):
        response = self.client.get("/ping/%s/" % self.check.code)
        assert response.status_code == 200

        self.check.refresh_from_db()
        assert self.check.status == "up"

        ping = Ping.objects.latest("id")
        assert ping.scheme == "http"

    def test_it_handles_bad_uuid(self):
        response = self.client.get("/ping/not-uuid/")
        assert response.status_code == 400

    def test_it_handles_120_char_ua(self):
        ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/44.0.2403.89 Safari/537.36")

        response = self.client.get("/ping/%s/" % self.check.code, HTTP_USER_AGENT=ua)
        assert response.status_code == 200

        ping = Ping.objects.latest("id")
        assert ping.ua == ua

    def test_it_truncates_long_ua(self):
        ua = "01234567890" * 30

        response = self.client.get("/ping/%s/" % self.check.code, HTTP_USER_AGENT=ua)
        assert response.status_code == 200

        ping = Ping.objects.latest("id")
        assert len(ping.ua) == 200
        assert ua.startswith(ping.ua)

    def test_it_reads_forwarded_ip(self):
        ip = "1.1.1.1"
        response = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_FOR=ip)
        ping = Ping.objects.latest("id")
        assert response.status_code == 200
        assert ping.remote_addr == "1.1.1.1"
        ### Assert the expected response status code and ping's remote address
        ip = "1.1.1.1, 2.2.2.2"
        response = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_FOR=ip, REMOTE_ADDR="3.3.3.3")
        ping = Ping.objects.latest("id")
        assert response.status_code == 200
        assert ping.remote_addr == "1.1.1.1"

    def test_it_reads_forwarded_protocol(self):
        response = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_PROTO="https")
        ping = Ping.objects.latest("id")
        ### Assert the expected response status code and ping's scheme
        assert response.status_code == 200
        assert ping.remote_addr == "127.0.0.1"

    def test_it_never_caches(self):
        response = self.client.get("/ping/%s/" % self.check.code)
        assert "no-cache" in response.get("Cache-Control")
    ### Test that when a ping is made a check with a paused status changes status

    def test_change_status_for_paused_status(self):
        self.check.status = "paused"
        response = self.client.get("/ping/%s/" % self.check.code)
        self.check.refresh_from_db()
        assert self.check.status == "up"

    ### Test that a post to a ping works
    def test_post_to_ping(self):
        response = self.client.get("/ping/%s/" % self.check.code)
        assert response.status_code == 200
    ### Test that the csrf_client head works

    def test_csrf_client(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        response = self.csrf_client.head("/ping/%s/" % self.check.code)
        assert response.status_code == 200



