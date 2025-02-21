from sodapy import Socrata

client = Socrata("data.iowa.gov", None)

check = True
ofst = 0

'''
    The while loop calls the API till all entries have been parsed through.
    There is 50,000 limit for the API so we change the offset to get all the data.
    results is a list of dictionaries
'''
while (check):
    results = client.get("cc6f-sgik", limit=50000, offset = 50000*ofst)
    print(ofst)
    if (len(results) == 0):
        check = False
    ofst += 1
    #MySQL code for insetion here
    