from django.test import TestCase
from django.http import JsonResponse
from unittest.mock import patch
from documentController.models import DocUser,Document,DocumentPermissions


class UserTests(TestCase):

    userNames=["User1", "User2", "User3", "user4"]

    @classmethod
    def setUpTestData(self):
        for userName in self.userNames:
            docUser = DocUser(userName=userName)
            docUser.save()
        doc = Document(docName="doc_name_1", docPath="docPath", ownerId=DocUser(userId=2))
        doc.save()
        doc = Document(docName="doc_name_2", docPath="docPath", ownerId=DocUser(userId=1))
        doc.save()
        docPermission=DocumentPermissions(userId=DocUser(userId=1), documentId=Document(documentId=1))
        docPermission.save()
        docPermission = DocumentPermissions(userId=DocUser(userId=3), documentId=Document(documentId=2))
        docPermission.save()
        docPermission = DocumentPermissions(userId=DocUser(userId=3), documentId=Document(documentId=1))
        docPermission.save()

    @patch('documentController.documentService.documentView.downloadFile')
    def testDownload(self, downloadFile):
        downloadFile.return_value=JsonResponse({}, status=206)
        response = self.client.get('http://testserver/v1/downloadDocument/document/1/user/1/')
        assert response.status_code==206

    @patch('documentController.documentService.documentView.downloadFile')
    def testDownloadForOwner(self, downloadFile):
        downloadFile.return_value=JsonResponse({}, status=206)
        response = self.client.get('http://testserver/v1/downloadDocument/document/1/user/2/')
        assert response.status_code == 206

    def testDownloadForOwnerUserNotAuthorised(self):
        response = self.client.get('http://testserver/v1/downloadDocument/document/1/user/4/')
        assert response.status_code == 401

    def testDownloadForOwnerDocumentNotFound(self):
        response = self.client.get('http://testserver/v1/downloadDocument/document/14/user/3/')
        assert response.status_code == 404

    def testDownloadForOwnerDocumentNotFound(self):
        response = self.client.get('http://testserver/v1/downloadDocument/document/14/user/3/')
        assert response.status_code == 404

    @patch('documentController.documentService.documentView.downloadFile')
    def testStartUpdate(self, downloadFile):
        downloadFile.return_value=JsonResponse({}, status=206)
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/1/')
        assert response.status_code == 206
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/1/')
        assert response.status_code == 200


    @patch('documentController.documentService.documentView.downloadFile')
    def testStartUpdateOwner(self, downloadFile):
        downloadFile.return_value = JsonResponse({}, status=206)
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/2/')
        assert response.status_code == 206
        downloadFile.return_value = JsonResponse({}, status=206)
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/1/')
        assert response.status_code == 401
        response = self.client.get('http://testserver/v1/downloadDocument/document/1/user/1/')
        assert response.status_code == 401
        response = self.client.get('http://testserver/v1/downloadDocument/document/1/user/2/')
        assert response.status_code == 206

    @patch('documentController.documentService.documentView.downloadFile')
    @patch('documentController.documentService.documentView.uploadFile')
    def testUpdateOperations(self, downloadFile, uploadFile):
        downloadFile.return_value = ""
        uploadFile.return_value = JsonResponse({}, status=206)

        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/1/')
        assert response.status_code == 401
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/1/')
        assert response.status_code == 206
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/1/')
        assert response.status_code == 200

    @patch('documentController.documentService.documentView.downloadFile')
    @patch('documentController.documentService.documentView.uploadFile')
    def testUpdateOperationsOwner(self, downloadFile, uploadFile):
        downloadFile.return_value = ""
        uploadFile.return_value = JsonResponse({}, status=206)

        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/1/')
        assert response.status_code == 206
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/3/')
        assert response.status_code == 206
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/1/user/2/')
        assert response.status_code == 206
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/1/')
        assert response.status_code == 401
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/2/')
        assert response.status_code == 200
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/3/')
        assert response.status_code == 406
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/1/')
        assert response.status_code == 406
        response = self.client.post('http://testserver/v1/endUpdatingDocument/document/1/user/1/')
        assert response.status_code == 401
        response = self.client.get('http://testserver/v1/startUpdatingDocument/document/11/user/1/')
        assert response.status_code == 404