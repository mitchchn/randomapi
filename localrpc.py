import json
import uuid
import urllib2


def http_request(url, json_string):
    """
    Fetch data from webserver (POST request)

    :param json_string: JSON-String
    """

    request = urllib2.Request(url, data=json_string)
    request.add_header("Content-Type", "application/json")
    response = urllib2.urlopen(request)
    response_string = response.read()
    response.close()

    return response_string


def create_request_dict(method, *args, **kwargs):
    """
    Returns a JSON-RPC-Dictionary for a method

    :param method: Name of the method
    :param args: Positional parameters
    :param kwargs: Named parameters
    """

    if kwargs:
        params = kwargs
        if args:
            params["__args"] = args
    else:
        params = args
    data = {
        "method": unicode(method),
        "id": unicode(uuid.uuid4()),
        "jsonrpc": u"2.0",
        "params": params
    }
    return data


def create_request_json(method, *args, **kwargs):
    """
    Returns a JSON-RPC-String for a method

    :param method: Name of the method
    :param args: Positional parameters
    :param kwargs: Named parameters
    """

    return json.dumps(create_request_dict(method, *args, **kwargs))
