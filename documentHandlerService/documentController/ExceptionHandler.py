from django.http import JsonResponse
from documentController.constants import *


def returnExceptionResult(exception, logger, result=FAILURE, message=ERROR_MESSAGE, status=500):
    logger.error(exception)
    response_data = {RESULT: result, MESSAGE: message}
    return JsonResponse(response_data, status=status)