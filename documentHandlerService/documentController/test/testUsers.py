from django.test import TestCase
from rest_framework.test import RequestsClient

class UserTests(TestCase):

    client = RequestsClient()

    user1 = '{"userName": "Michael Carrick"}'
    user2= '{"userName": "George Best"}'

    @classmethod
    def setUpTestData(self):
        # Set up data for the whole TestCase
        response = self.client.post('http://testserver/v1/user/', self.user1)
        response = self.client.post('http://testserver/v1/user/', self.user2)

    def testGetAllUsers(self):
        # Some test using self.foo
        response = self.client.get('http://testserver/v1/user/')

        assert response.status_code==200

        userNames = ["Michael Carrick", "George Best"]


        for userName in userNames:
            assert str(userName) in str(response.content)

    def testGetAUser(self):
        # Some test using self.foo
        response = self.client.get('http://testserver/v1/user/1/')

        assert response.status_code==200

        userName = "Michael Carrick"
        userName_absent = "George Best"

        assert str(userName) in str(response.content)
        assert not str(userName_absent) in str(response.content)

    def testGetAUserWhichIsAbsent(self):
        # Some test using self.foo
        response = self.client.get('http://testserver/v1/user/11/')

        assert response.status_code==404

        userName = "Michael Carrick"
        userName_absent = "George Best"

        assert not str(userName) in str(response.content)
        assert not str(userName_absent) in str(response.content)
