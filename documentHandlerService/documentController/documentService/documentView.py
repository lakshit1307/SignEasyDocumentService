from documentController.documentService.documentSerializer \
    import DocumentSerializer, DocumentRequestSerializer
from documentController.models import Document, DocUser, DocumentPermissions, DocumentEdits
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
import logging
import time
import os
from documentController.constants import *
import mimetypes
from django.db.utils import IntegrityError
from documentController.ExceptionHandler import returnExceptionResult
from documentController.ReadWriteLock import ReadWriteLock

# import threading

logger = logging.getLogger("Document_View_Service")

document_locks = {}


@api_view([GET, POST])
def document_control(request):
    #
    # """
    # List all users.
    # """
    if request.method == GET:
        try:
            return getDocument()
        except Exception as e:
            return returnExceptionResult(e, logger)

    elif request.method == POST:
        try:
            return createDocument(request)
        except Exception as e:
            return returnExceptionResult(e, logger)


@api_view([GET])
def downloadDocument(request, docId, userId):
    """
    downlaod document specified by @docId for the user with userId @userId
    """
    try:
        try:
            document = Document.objects.get(pk=docId)
        except Document.DoesNotExist as e:
            logger.error(e)
            return returnExceptionResult(e, logger, FAILURE, 'Document not found', 404)

        # Assuming that permissions are required for downloading: check for permissions
        if userId != document.ownerId.userId and not isDocumentPermissionForUser(document, userId):
            return returnExceptionResult(None, logger, FAILURE, 'User not authorised', 401)

        if request.method == GET:
            # check if owner is updating the document or if owner is requesting the download
            lock = getLock(docId)
            try:
                lock.acquire_read()
                if userId == document.ownerId.userId or not isOwnerUpdatingDocument(document):
                    return downloadFile(document.docPath, document.docName, userId == document.ownerId.userId)
                else:
                    response_data = {RESULT: FAILURE, MESSAGE: 'Owner is performing edits. Access denied'}
                    return JsonResponse(response_data, status=401)
            except Exception as e:
                return returnExceptionResult(e, logger, FAILURE, ERROR_MESSAGE, 500)
            finally:
                lock.release()

    except Exception as e:
        return returnExceptionResult(e, logger)


@api_view([GET])
def updateDocumentStart(request, docId, userId):
    try:
        doc = Document(documentId=docId)
        user = DocUser(userId=userId)

        if request.method == GET:
            try:
                document = Document.objects.get(pk=docId)
            except Document.DoesNotExist as e:
                return returnExceptionResult(e, logger, FAILURE, 'Document not found', 404)

            if not isDocumentPermissionForUser(document, userId):
                response_data = {RESULT: FAILURE, MESSAGE: 'User not authorised to edit document'}
                return JsonResponse(response_data, status=401)

            if isOwnerUpdatingDocument(document):
                if document.ownerId.userId==userId:
                    response_data = {RESULT: SUCCESS, MESSAGE: 'Already editing the document'}
                    return JsonResponse(response_data, status=401)
                response_data = {RESULT: FAILURE, MESSAGE: 'Access denied. Owner is performing Operations'}
                return JsonResponse(response_data, status=401)

            # Check if document has permissions for edit and if the owner is performing any edits
            # create a record stating that the user has started editing the file
            lock = getLock(docId)
            try:
                lock.acquire_read()
                documentEdit = DocumentEdits(userId=user, documentId=doc)
                documentEdit.save()
                return downloadFile(document.docPath, document.docName, document.ownerId.userId == userId)
            except IntegrityError:
                response = {RESULT: SUCCESS, MESSAGE: 'Already editing the document'}
                return JsonResponse(response, status=200)
            finally:
                lock.release()

    except Exception as e:
        return returnExceptionResult(e, logger)


@api_view([POST])
def updateDocumentEnd(request, docId, userId):
    """
    finish updating the file
    """

    try:
        document = Document(documentId=docId)
        # user = DocUser(userId=userId)
        docEdit = isUserUpdatingDocument(document, userId)
        if not docEdit:
            response_data = {RESULT: FAILURE, MESSAGE: 'User is not permforming edits yet.'}
            return JsonResponse(response_data, status=401)
        if request.method == POST:
            try:
                doc = Document.objects.get(pk=docId)
            except Document.DoesNotExist as e:
                return returnExceptionResult(e, logger, FAILURE, 'Document not found', 404)
            lock = getLock(docId)
            if userId == doc.ownerId.userId or not isOwnerUpdatingDocument(doc):
                try:
                    lock.acquire_write()
                    if docEdit.editIsValid:
                        uploadFile(request, doc.docPath, doc.docName)
                        invalidateEdits(document)
                        response_data = {RESULT: SUCCESS}
                        status = 200
                        if userId == doc.ownerId.userId:
                            logger.info("Owner - Upload")
                        else:
                            logger.info("Collaborator - Upload")

                    else:
                        response_data = {RESULT: FAILURE, MESSAGE: "Reload the document"}
                        status = 406
                    docEdit.delete()
                finally:
                    lock.release()
                return JsonResponse(response_data, status=status)
            else:
                response_data = {RESULT: FAILURE, MESSAGE: 'Owner is performing edits. Access denied'}
                return JsonResponse(response_data, status=401)


    except Exception as e:
        return returnExceptionResult(e, logger)


@api_view([GET])
def getDocumentById(request, docId):
    try:
        document = Document.objects.get(pk=docId)
    except Document.DoesNotExist as e:
        return returnExceptionResult(e, logger, FAILURE, 'Document not found', 404)

    try:
        if request.method == GET:
            serializer = DocumentSerializer(document)
            return JsonResponse(serializer.data, status=200)
    except Exception as e:
        return returnExceptionResult(e, logger)


@api_view([POST])
def grantDocumentPermission(request):
    """
    grant permission to a user by the owner of the document
    """

    try:
        return grantPermissions(request)

    except Exception as e:
        return returnExceptionResult(e, logger)


def grantPermissions(request):
    data = JSONParser().parse(request)
    ownerId = data["ownerId"]
    docId = data["documentId"]
    userId = data["userId"]

    try:
        document = Document.objects.get(pk=docId)
    except Document.DoesNotExist as e:
        logger.error("Document with docId: " + str(docId) + " not found")
        return returnExceptionResult(e, logger, FAILURE, 'Document not found', 404)

    # if the requesting user is not the owner, then deny access
    if document.ownerId.userId != ownerId:
        return returnExceptionResult(None, logger, FAILURE, 'Not enough permissions to grant access', 401)

    # if owner is requesting access for itself then state that user already has access
    if ownerId == userId:
        response_data = {RESULT: SUCCESS, MESSAGE: 'Already an owner'}
        return JsonResponse(response_data, status=200)

    try:
        # add permissions to DB
        documentPermission = DocumentPermissions(documentId=Document(documentId=data["documentId"]),
                                                 userId=DocUser(userId=data["userId"]))
        documentPermission.save()

        response_data = {RESULT: SUCCESS, MESSAGE: 'Succesfully saved in DB'}
        return JsonResponse(response_data, status=201)

    # in case of permissions being already present, state that permission exists
    except IntegrityError as e:

        if str(e).__contains__('FOREIGN KEY constraint failed'):
            return returnExceptionResult(e, logger, FAILURE, 'User Not Found', 404)

        response_data = {RESULT: SUCCESS, MESSAGE: 'Already has permissions'}
        return JsonResponse(response_data, status=200)


def createDocument(request):
    """
    create a document
    """
    response_data = {}
    data = JSONParser().parse(request)
    ownerId = data["ownerId"]

    try:
        DocUser.objects.get(pk=ownerId)
    except DocUser.DoesNotExist as e:
        return returnExceptionResult(e, logger, FAILURE, 'User not found', 404)

    # add timestamp to fileName in case of multiple files with the same fileName
    fileName = data["docName"] + current_milli_time() + ".txt"
    filePath = addFile(fileName)

    if (filePath == False):
        # TODO: Can retry after a milliSecondToSaveIt Again
        # Avoid retry ideally as it could be due to the same Request being sent multiple times
        logger.error('File Already exists with the same name on this milliSecond')
        response_data[RESULT] = FAILURE
        response_data[MESSAGE] = ERROR_MESSAGE
        return JsonResponse(response_data, status=500)

    # save the file details to the DB
    data["docPath"] = filePath
    document = Document(docName=data["docName"], docPath=filePath, ownerId=DocUser(userId=ownerId))
    document.save()
    response_data[RESULT] = SUCCESS
    response_data[MESSAGE] = 'Succesfully saved in DB'
    return JsonResponse(response_data, status=201)


def getDocument():
    """
    get the list of all document
    """
    # get document details
    querySet = Document.objects.all()
    serializer = DocumentSerializer(querySet, many=True)
    logger.info("Succesfully fetched all the list of users")
    return JsonResponse(serializer.data, safe=False, status=200)


def addFile(fileName):
    """
    add file to the document repository
    """
    print()
    filePath = 'documentHandlerService/documentController/documentRepository/' + fileName
    if not os.path.exists(filePath):
        open(filePath, 'w').close()
        return filePath
    return False


# get current time
def current_milli_time():
    return round(time.time() * 1000).__str__()


def downloadFile(filePath, fileName, isOwner):
    fl = open(filePath, 'r')
    mime_type, _ = mimetypes.guess_type(filePath)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % fileName
    if isOwner:
        logger.info("Owner - Download")
    else:
        logger.info("Collaborator - Download")
    return response


def uploadFile(request, filePath, fileName):
    # parser_classes = (FileUploadParser,)
    file_obj = request.FILES['file']
    os.remove(filePath)
    destination = open(filePath, 'wb+')
    for chunk in file_obj.chunks():
        destination.write(chunk)
    destination.close()  # File should be closed only after all chunks are added


def isOwnerUpdatingDocument(document):
    """
    Check if owner is updating the document
    """
    return isUserUpdatingDocument(document, document.ownerId)


def isUserUpdatingDocument(document, userId):
    """
    check if user is updating the document
    """
    docEdits = DocumentEdits.objects.filter(documentId=document.documentId, userId=userId)
    if docEdits.count() == 0:
        return False
    return docEdits[0]


def isDocumentPermissionForUser(document, userId):
    """
    check if user has permission for the document
    """
    if document.ownerId.userId == userId:
        return True
    docPermission = DocumentPermissions.objects.filter(documentId=document.documentId, userId=userId)
    if docPermission.count() == 0:
        return False
    return True


def invalidateEdits(document):
    DocumentEdits.objects.filter(documentId=document.documentId).update(editIsValid=False)


def getLock(docId):
    if document_locks.get(docId) is None:
        document_locks[docId] = ReadWriteLock()
    return document_locks[docId]
