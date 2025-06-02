from django.shortcuts import HttpResponse
# Create your views here.


def home(request):
    """
    This is the home view of the Directions app
    """
    message = "Welcome to the Directions home"
    return HttpResponse(message)
