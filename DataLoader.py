from sodapy import Socrata

client = Socrata("data.iowa.gov", None)

results = client.get("cc6f-sgik", limit=1)

print(results)