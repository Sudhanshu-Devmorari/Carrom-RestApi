from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    if isinstance(exc, AuthenticationFailed):
        if "Invalid token header" in str(exc):
            return Response(
                {"status": "error", "message": "Invalid token header. No credentials provided."},
                status=401,
            )
       
        if "Invalid token" in str(exc):
            return Response(
                {"status": "error", "message": "Invalid token."},
                status=401,
            )
       
       
        
        return Response(
            {"status": "error", "message": "Authentication credentials were not provided."},
            status=401,
        )
   
    if "Authentication credentials were not provided" in str(exc):
        return Response(
            {"status": "error", "message": "Authentication credentials were not provided."},
            status=401,
        )
    
    # Handle other exceptions if needed
    return Response(
        {"status": "error", "message": "Something went wrong. Please try again."},
        status=400,
    )
