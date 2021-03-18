from documentController.userService.userSerializer import DocUserSerializer
from documentController.models import DocUser
from django.http import HttpResponse, JsonResponse
from documentController.userService.userSerializer import UserRequestSerializer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
import logging
from documentController.constants import *
from documentController.ExceptionHandler import returnExceptionResult

logger = logging.getLogger("User_View_Service")

@api_view([GET,POST])
def user_list(request):

    """
    List all users.
    """
    if request.method == GET:
        try:
            return getUsers()
        except Exception as e:
            return returnExceptionResult(e, logger)

    elif request.method == POST:
        try:
            return createUser(request)
        except Exception as e:
            return returnExceptionResult(e, logger)

@api_view([GET])
def getUserById(request, userId):
    # """
    # Retrieve a user with userId PK.
    # """
    try:
        try:
            user = DocUser.objects.get(pk=userId)
        except DocUser.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == GET:
            serializer = DocUserSerializer(user)
            return JsonResponse(serializer.data, status=200)
    except Exception as e:
        return returnExceptionResult(e, logger)

def createUser(request):
    response_data = {}
    data = JSONParser().parse(request)
    serializer = UserRequestSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        response_data[RESULT] = SUCCESS
        response_data[MESSAGE] = 'Succesfully saved in DB'
        return JsonResponse(response_data, status=201)
    logger.error('Error while saving user')
    response_data[RESULT] = FAILURE
    response_data[MESSAGE] = ERROR_MESSAGE
    return JsonResponse(response_data, status=500)



def getUsers():
    querySet = DocUser.objects.all()
    serializer = DocUserSerializer(querySet, many=True)
    logger.info("Succesfully fetched all the list of users")
    return JsonResponse(serializer.data, safe=False)

