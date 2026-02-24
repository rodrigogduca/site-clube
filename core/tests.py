from django.test import TestCase, Client


class CoreTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_status_code(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
