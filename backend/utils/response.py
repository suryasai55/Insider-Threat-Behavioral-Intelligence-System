from flask import jsonify

def api_response(success=True, message="", data=None, status_code=200):
    """
    Generate a standardized JSON API response.
    """
    response_payload = {
        "success": success,
        "message": message
    }
    if data is not None:
        response_payload["data"] = data
        
    return jsonify(response_payload), status_code

def api_error(message="", errors=None, status_code=400):
    """
    Generate a standardized JSON API error response.
    """
    response_payload = {
        "success": False,
        "message": message
    }
    if errors is not None:
        response_payload["errors"] = errors
        
    return jsonify(response_payload), status_code
