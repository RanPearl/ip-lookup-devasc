import unittest
from unittest.mock import patch, Mock
import requests
import ip_lookup as app


class TestVersionOf(unittest.TestCase):
    def test_ipv4(self):
        self.assertEqual(app.version_of("203.0.113.5"), 4)

    def test_ipv6(self):
        self.assertEqual(app.version_of("2001:db8::1"), 6)

    def test_invalid(self):
        self.assertIsNone(app.version_of("not-an-ip"))
        self.assertIsNone(app.version_of(None))


class TestAddresses(unittest.TestCase):
    @patch("ip_lookup.get_json")
    def test_ipv4_returned(self, mock_get):
        mock_get.return_value = {"ip": "203.0.113.5"}
        self.assertEqual(app.get_ipv4(), "203.0.113.5")

    @patch("ip_lookup.get_json")
    def test_ipv6_returned(self, mock_get):
        mock_get.return_value = {"ip": "2001:db8::1"}
        self.assertEqual(app.get_ipv6(), "2001:db8::1")

    @patch("ip_lookup.get_json")
    def test_ipv6_fallback_to_ipv4_is_rejected(self, mock_get):
        mock_get.return_value = {"ip": "203.0.113.5"}
        self.assertIsNone(app.get_ipv6())

    @patch("ip_lookup.get_json", side_effect=app.LookupError_("down"))
    def test_ipv6_failure_returns_none(self, _):
        self.assertIsNone(app.get_ipv6())


class TestLocation(unittest.TestCase):
    @patch("ip_lookup.get_json")
    def test_parsing(self, mock_get):
        mock_get.return_value = {"success": True, "city": "Iloilo City", "region": "Western Visayas",
                                 "country": "Philippines", "connection": {"isp": "ExampleNet"}}
        loc = app.get_location("203.0.113.5")
        self.assertEqual(loc["city"], "Iloilo City")
        self.assertEqual(loc["isp"], "ExampleNet")

    @patch("ip_lookup.get_json")
    def test_missing_fields_become_unknown(self, mock_get):
        mock_get.return_value = {"success": True}
        self.assertEqual(app.get_location("203.0.113.5")["city"], "Unknown")

    def test_invalid_ip_rejected(self):
        with self.assertRaises(app.LookupError_):
            app.get_location("hello")

    @patch("ip_lookup.get_json")
    def test_api_error_field(self, mock_get):
        mock_get.return_value = {"success": False, "message": "reserved range"}
        with self.assertRaises(app.LookupError_):
            app.get_location("203.0.113.5")


class TestGetJson(unittest.TestCase):
    @patch("ip_lookup.requests.get", side_effect=requests.exceptions.Timeout)
    def test_timeout(self, _):
        with self.assertRaises(app.LookupError_):
            app.get_json("https://example.com")

    @patch("ip_lookup.requests.get", side_effect=requests.exceptions.ConnectionError)
    def test_no_network(self, _):
        with self.assertRaises(app.LookupError_):
            app.get_json("https://example.com")

    @patch("ip_lookup.requests.get")
    def test_rate_limit(self, mock_get):
        resp = Mock(status_code=429)
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        mock_get.return_value = resp
        with self.assertRaises(app.LookupError_) as ctx:
            app.get_json("https://example.com")
        self.assertIn("rate limit", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
