from django.test import TestCase
from rest_framework.test import RequestsClient
from documentController.models import DocUser,Document
from unittest.mock import patch

class DocumentTests(TestCase):
    client = RequestsClient()

    userNames=["User1", "User2"]

    @classmethod
    def setUpTestData(self):

        for userName in self.userNames:
            docUser=DocUser(userName=userName)
            docUser.save()
        doc=Document(docName="doc_name_1", docPath="docPath", ownerId=DocUser(userId=2))
        doc.save()
        doc=Document(docName="doc_name_2", docPath="docPath", ownerId=DocUser(userId=1))
        doc.save()

    @patch('documentController.documentService.documentView.addFile')
    def testGetDocument(self, addFileFunc):
        addFileFunc.return_value="someFilePath"
        request={"ownerId": "1", "docName": "doc1"}
        response = self.client.post('http://testserver/v1/document/', request, content_type='application/json')
        assert response.status_code==201

    def testGetDocumentInvalidUser(self):
        request = {"ownerId": "11", "docName": "doc1"}
        response = self.client.post('http://testserver/v1/document/', request, content_type='application/json')
        assert response.status_code == 404

    def testGetDocument(self):
        response = self.client.get('http://testserver/v1/document/')
        assert "doc_name_1" in str(response.content)
        assert "doc_name_2" in str(response.content)

        assert response.status_code == 200

    def testGetDocumentById(self):
        response = self.client.get('http://testserver/v1/document/1/')
        assert "doc_name_1" in str(response.content)
        assert "doc_name_2" not in str(response.content)

        assert response.status_code == 200

    def testGetDocumentInvalidId(self):
        response = self.client.get('http://testserver/v1/document/11/')
        assert response.status_code == 404

    def testGetDocumentInvalidId(self):
        response = self.client.get('http://testserver/v1/document/11/')
        assert response.status_code == 404

    def testGrantPermission(self):
        request={"ownerId": 2, "documentId": "1", "userId":1}
        response = self.client.post('http://testserver/v1/grantDocumentPermission/', request, content_type='application/json')
        assert response.status_code == 201

    def testGrantPermissionUnauthorisedUser(self):
        request={"ownerId": 1, "documentId": "1", "userId":2}
        response = self.client.post('http://testserver/v1/grantDocumentPermission/', request, content_type='application/json')
        message="Not enough permissions to grant access"
        assert message in str(response.content)
        assert response.status_code == 401

    def testGrantPermissionOwnerPermission(self):
        request={"ownerId": 2, "documentId": 1, "userId":2}
        response = self.client.post('http://testserver/v1/grantDocumentPermission/', request, content_type='application/json')
        message="Already an owner"
        assert message in str(response.content)
        assert response.status_code == 200

    def testGrantPermissionPermissionAlreadyPresent(self):
        request={"ownerId": 2, "documentId": 1, "userId":1}
        response = self.client.post('http://testserver/v1/grantDocumentPermission/', request, content_type='application/json')
        response = self.client.post('http://testserver/v1/grantDocumentPermission/', request, content_type='application/json')
        message = "Already has permissions"
        assert message in str(response.content)

