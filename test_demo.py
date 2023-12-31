'''
In the project, the majority of tasks will undergo script testing, with only a few being reviewed by the TA. 
Be aware that this testing material is not final and cannot cover all testing scenarios. 
If you are caught cheating during testing, the whole group will receive a score of 0 for the project.
The script checks using the requests library in Python.
Before testing, ensure that the server has three users with the usernames "client1", "client2", and "client3", and the passwords "123".
In the upcoming tests, if the Authorization field is needed, use "client1" and "123" as both the username and password.
'''

import requests

URL = 'http://localhost:8080'

'''
The initial check is the head request, a fundamental job of the server is to respond to the request.
Use the "headers" parameter for logging into the server.
Disregard this parameter if the server lacks the login feature.
'''

print('Test head request:')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
q=requests.head(URL,headers=headers)
print(q)
print()

# Test get request
print('Test get request:')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
q=requests.get(URL,headers=headers)
print(q)
print()

# Test post request
print('Test post request:')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
q=requests.post(URL,headers=headers)
print(q)
print()

'''
Next, we will provide test examples based on the chapters in the project documentation.
Each test is accompanied by a output.
We do not check exact string matches for your output, as long as you complete the corresponding task.
'''

#1.1
print('1.1')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})
response1 = session.get(URL,headers=headers)
response2 = session.get(URL,headers=headers)
print(response1)
print(response2)
print()

#1.2
#1.1
print('1.2 1.1')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
session1 = requests.Session()
session1.headers.update({'Connection': 'keep-alive'})
session2 = requests.Session()
session2.headers.update({'Connection': 'keep-alive'})
response1 = session1.get(URL,headers=headers)
response2 = session2.get(URL,headers=headers)
print(response1)
print(response2)
print()

#1.3
print('1.3')
headers1={"Authorization": "Basic Y2xpZW50MToxMjM="}
headers2={}
q=requests.head(URL,headers=headers1)
print(q)
q=requests.head(URL,headers=headers2)
print(q)
print()

#2
print('2')
url1=URL+'/?SUSTech-HTTP=1'
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=url1, headers=headers)
print(r)
print(r.content.decode())
print()

#2
print('2')
url2=URL+'/?SUSTech-HTTP=0'
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=url2, headers=headers)
print(r.content.decode())
print()

#2
print('2')
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=URL+'/a.txt', headers=headers)
print(r.content.decode())
print()

#3.1
print('3.1')
files = {"firstFile": open('data/a.txt', "rb")}
data={}
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.post(url=URL+'/upload?path=client1/',data=data,headers=headers, files=files)
print(r)
r=requests.post(url=URL+'/upload?path=client2/',data=data,headers=headers, files=files)
print(r)
print()

#3.2
print('3.2')
url=URL+'/delete?path=client1/a.py'
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.post(url=url, headers=headers)
print(r)
print()

#4
url=URL
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=url, headers=headers)
print(r.cookies.values()[0])
headers={"Cookie":'session-id='+r.cookies.values()[0]}
q=requests.get(URL,headers=headers)
print(q)
# print(q.cookies)
print()

#5
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=URL+'/client1/a.txt?chunked=1', headers=headers)
print(r)
print()

#Breakpoint Transmission
url=URL+'/client1/a.txt'
data={}
headers={"Authorization": "Basic Y2xpZW50MToxMjM=",
         "Range": "0-1,1-2,2-3"}
r=requests.get(url=url, data=data, headers=headers)
print(r.content.decode())
print()
