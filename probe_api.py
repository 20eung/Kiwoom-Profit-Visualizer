import requests

base_url = "https://api.kiwoom.com"
paths = [
    "/oauth2/token",
    "/oauth2/v1/token",
    "/v1/oauth2/token",
    "/openapi/v1/oauth2/token",
    "/v1/token",
    "/token"
]

print(f"Probing {base_url}...")

# Check Root
try:
    resp = requests.get(base_url, timeout=5)
    print(f"ROOT: {resp.status_code}")
except Exception as e:
    print(f"ROOT: Failed ({e})")

# Check Paths
for path in paths:
    url = f"{base_url}{path}"
    try:
        # Try POST (likely for token)
        resp = requests.post(url, timeout=5)
        print(f"POST {path}: {resp.status_code}")
        
        # Try GET if POST fails/404 just in case
        if resp.status_code == 404:
             resp_get = requests.get(url, timeout=5)
             print(f"GET  {path}: {resp_get.status_code}")
             
    except Exception as e:
        print(f"{path}: Failed ({e})")
