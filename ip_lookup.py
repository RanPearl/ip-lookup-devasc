"""IP Address Lookup - DEVASC Project Activity 3 (Option 2)
Team: Ran, Chris, Elgenne

Retrieves the user's current public IPv4 and IPv6 addresses from a REST
API over HTTPS and shows the approximate location and ISP for an address.
"""
import ipaddress
import requests

IPV4_URL = "https://api.ipify.org?format=json"     # answers over IPv4 only
IPV6_URL = "https://api64.ipify.org?format=json"   # IPv6 if available
GEO_URL = "https://ipwho.is/{ip}"                  # location / ISP
TIMEOUT = 5


class LookupError_(Exception):
    """Raised when an API call fails in a way we can explain to the user."""


def get_json(url, timeout=TIMEOUT):
    """GET a REST endpoint over HTTPS and return the parsed JSON."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise LookupError_("The request timed out. Check your connection.")
    except requests.exceptions.HTTPError as err:
        code = err.response.status_code if err.response is not None else "?"
        if code == 429:
            raise LookupError_("API rate limit reached. Try again later.")
        raise LookupError_(f"The API returned an error (HTTP {code}).")
    except requests.exceptions.RequestException:
        raise LookupError_("Network problem. Are you online?")
    except ValueError:
        raise LookupError_("The API sent a response we could not read.")


def version_of(text):
    """Return 4 or 6 if text is a valid IP address, otherwise None."""
    try:
        return ipaddress.ip_address(text).version
    except (ValueError, TypeError):
        return None


def get_ipv4():
    ip = get_json(IPV4_URL).get("ip")
    return ip if version_of(ip) == 4 else None


def get_ipv6():
    """Return the IPv6 address, or None when the network has no IPv6.

    api64.ipify.org falls back to IPv4 when IPv6 is unavailable, so the
    returned value is checked before it is accepted.
    """
    try:
        ip = get_json(IPV6_URL).get("ip")
    except LookupError_:
        return None
    return ip if version_of(ip) == 6 else None


def get_location(ip):
    """Return city, region, country and ISP for an IP address."""
    if version_of(ip) is None:
        raise LookupError_("That is not a valid IP address.")
    data = get_json(GEO_URL.format(ip=ip))
    if not data.get("success", True):
        raise LookupError_(data.get("message", "Location lookup failed."))
    connection = data.get("connection") or {}
    return {
        "city": data.get("city") or "Unknown",
        "region": data.get("region") or "Unknown",
        "country": data.get("country") or "Unknown",
        "isp": connection.get("isp") or connection.get("org") or "Unknown",
    }


def show_addresses():
    v4, v6 = get_ipv4(), get_ipv6()
    print("\n--- Your public IP addresses ---")
    print(f"IPv4: {v4 or 'not available'}")
    print(f"IPv6: {v6 or 'not available on this network'}")
    return v4, v6


def show_location(ip):
    loc = get_location(ip)
    print("\n--- Approximate location ---")
    print(f"IP:       {ip}")
    print(f"City:     {loc['city']}")
    print(f"Region:   {loc['region']}")
    print(f"Country:  {loc['country']}")
    print(f"ISP:      {loc['isp']}")


MENU = """
=== IP Address Lookup ===
1. Show my IPv4 and IPv6 addresses
2. Show my approximate location and ISP
3. Quit
"""


def main():
    while True:
        print(MENU)
        choice = input("Choose an option (1-3): ").strip()
        try:
            if choice == "1":
                show_addresses()
            elif choice == "2":
                ip = get_ipv4() or get_ipv6()
                if ip is None:
                    print("Could not find your IP address.")
                else:
                    show_location(ip)
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Please enter 1, 2, or 3.")
        except LookupError_ as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    main()
