#!/usr/bin/env python

"""
randomapi.py: a Python implementation of the RANDOM.org JSON-RPC API

Author: Mitchell Cohen (mitch.cohen@me.com)
http://github.com/mitchchn/randomapi

Date: April 20, 2014
Version: 0.1

RANDOM.org API reference:
- https://api.random.org/json-rpc/1/

randomapi.py supports all basic and signed methods in Release 1
of the RANDOM.ORG API. It respects delay requests from the server
and has the ability to verify digitally-signed data.

RPC code based on python-jsonrpc:
- https://pypi.python.org/pypi/python-jsonrpc

Example usage:

    # Returns a list of 5 random numbers between 0 and 10

    random_client = RandomJSONRPC(api_key) # Requires a valid API key
    nums = random_client.generate_integers(n=5, min=0, max=10)

"""

import time
import json
import logging
import urllib2
import uuid
from collections import OrderedDict

###################### Constants #############################

JSON_URL = "https://api.random.org/json-rpc/1/invoke"

# RANDOM.org API method names

INTEGER_METHOD = "generateIntegers"
DECIMAL_METHOD = "generateDecimalFractions"
GAUSSIAN_METHOD = "generateGaussians"
STRING_METHOD = "generateStrings"
UUID_METHOD = "generateUUIDs"
BLOB_METHOD = "generateBlobs"
USAGE_METHOD = "getUsage"

SIGNED_INTEGER_METHOD = "generateSignedIntegers"
SIGNED_DECIMAL_METHOD = "generateDecimalFractions"
SIGNED_GAUSSIAN_METHOD = "generateSignedGaussians"
SIGNED_STRING_METHOD = "generateSignedStrings"
SIGNED_UUID_METHOD = "generateSignedUUIDs"
SIGNED_BLOB_METHOD = "generateSignedBlobs"
VERIFY_SIGNATURE_METHOD = "verifySignature"

# RANDOM.org API parameters

ADVISORY_DELAY = "advisoryDelay"
API_KEY = "apiKey"

# JSON keys

RESULT = "result"
RANDOM = "random"
AUTHENTICITY = "authenticity"
SIGNATURE = "signature"

# RANDOM.org blob formats

FORMAT_BASE64 = "base64"
FORMT_HEX = "hex"


def valid_json_methods():
    return [INTEGER_METHOD, DECIMAL_METHOD, GAUSSIAN_METHOD, STRING_METHOD,
            UUID_METHOD, BLOB_METHOD, USAGE_METHOD, SIGNED_INTEGER_METHOD,
            SIGNED_BLOB_METHOD, SIGNED_DECIMAL_METHOD, SIGNED_GAUSSIAN_METHOD,
            SIGNED_STRING_METHOD, SIGNED_UUID_METHOD, VERIFY_SIGNATURE_METHOD]


def parse_random(json_string):
    """
    Returns the randomly-generated data from a RANDOM.org JSON request

    :param json_string a fully-formed JSON-RPC response string
    """

    data = json_to_ordered_dict(json_string)
    random = []
    if RANDOM in data[RESULT]:
        random = data[RESULT][RANDOM]
    return random

def json_to_ordered_dict(json_string):
    return json.loads(json_string, object_pairs_hook=OrderedDict)


def compose_api_call(json_method_name, *args, **kwargs):
    """
    Returns a fully-formed JSON-RPC string for a RANDOM.org API method

    :param json_method_name: Name of the method. Can be one of:
        INTEGER_METHOD, DECIMAL_METHOD, GAUSSIAN_METHOD, STRING_METHOD, 
        UUID_METHOD, BLOB_METHOD, USAGE_METHOD, SIGNED_INTEGER_METHOD,
        SIGNED_BLOB_METHOD, SIGNED_DECIMAL_METHOD, SIGNED_GAUSSIAN_METHOD,
        SIGNED_STRING_METHOD, SIGNED_UUID_METHOD, VERIFY_SIGNATURE_METHOD 
    :param args: Positional parameters
    :param kwargs: Named parameters. See: https://api.random.org/json-rpc/1/basic
    for descriptions of methods and their parameters.
    """

    if json_method_name not in valid_json_methods():
        raise Exception(
            "'{}' is not a valid RANDOM.org JSON-RPC method".format(
                json_method_name))
    if kwargs:
        params = kwargs
        if args:
            params["__args"] = args
    else:
        params = args

    request_data = {
        "method": unicode(json_method_name),
        "id": unicode(uuid.uuid4()),
        "jsonrpc": u"2.0",
        "params": params
    }
    return json.dumps(request_data)


def http_request(url, json_string):
    """
    Request data from server (POST)

    :param json_string: JSON-String
    """

    request = urllib2.Request(url, data=json_string)
    request.add_header("Content-Type", "application/json")
    response = urllib2.urlopen(request)
    response_string = response.read()
    response.close()

    return response_string


class RandomJSONRPC:

    def __init__(self, api_key):
        """
        Creates a client which can call RANDOM.org API functions to generate
        various kinds of random data.

        The class is simple to use. Simply instantiate a RandomJSONRPC object
        with a valid API key, and call the appropriate method on the server::

        For a list of available methods and parameters, see: 

        :param api_key: String representing a RANDOM.org JSON-RPC API key
        """
        self.api_key = api_key
        self._time_of_last_request = 0
        self._advisory_delay = 0

    def _refresh(self):
        self._json_data = {}
        self._result = {}
        self._random = []
        self._signature = ""

    def _populate(self):
        if RESULT in self._json_data:
            self._result = self._json_data[RESULT]
        if ADVISORY_DELAY in self._result:
            self._advisory_delay = float(self._result[ADVISORY_DELAY]) / 1000.0
        if RANDOM in self._result:
            self._random = self._result[RANDOM]
        if SIGNATURE in self._result:
            self._signature = self._result[SIGNATURE]

    def delay_request(self, requested_delay):
        elapsed = time.time() - self._time_of_last_request
        remaining_time = requested_delay - elapsed

        logging.info("Sleeping {} more seconds...".format(remaining_time))

        if remaining_time - elapsed > 0:
            time.sleep(remaining_time)

    def check_errors(self):
        if 'error' in self._json_data:
            error = self._json_data['error']
            code = error['code']
            message = error['message']
            raise Exception(
"""Error code: {}. Message: {}
See: https://api.random.org/json-rpc/1/error-codes""".format(code, message))

    def send_request(self, request_string):
        '''Wraps outgoing JSON requests'''

        # Wipe out any data from previous request
        self._refresh()

        # Respect delay requests from the server
        if self._time_of_last_request == 0:
            self._time_of_last_request = time.time()
        if self._advisory_delay > 0:
            self.delay_request(self._advisory_delay)

        # Make the connection now
        json_string = http_request(JSON_URL, request_string)
        self._time_of_last_request = time.time()

        # Use an ordered dict to preserve the integrity of signed data
        self._json_data = json_to_ordered_dict(json_string)
        self.check_errors()
        self._populate()
        return self

    def parse(self):
        '''Parses the received JSON data object and returns the random data'''
        return self._random['data']

####################### RANDOM.org API methods ##########################

    def generate_integers(self, n, min, max, replacement=True, base=10):
        request_string = compose_api_call(
            INTEGER_METHOD, apiKey=self.api_key,
            n=n, min=min, max=max, replacement=replacement, base=base)
        return self.send_request(request_string).parse()

    def generate_decimal_fractions(self, n, decimal_places, replacement=True):
        request_string = compose_api_call(
            DECIMAL_METHOD, apiKey=self.api_key,
            n=n, decimalPlaces=decimal_places, replacement=replacement)
        return self.send_request(request_string).parse()

    def generate_gaussians(self, n, mean, standard_deviation,
                           significant_digits):
        request_string = compose_api_call(
            GAUSSIAN_METHOD, apiKey=self.api_key,
            n=n, mean=mean,
            standardDeviation=standard_deviation,
            significantDigits=significant_digits)
        return self.send_request(request_string).parse()

    def generate_strings(self, n, length, characters, replacement=True):
        request_string = compose_api_call(
            STRING_METHOD, apiKey=self.api_key,
            n=n, length=length, characters=characters, replacement=replacement)
        return self.send_request(request_string).parse()

    def generate_uuids(self, n):
        request_string = compose_api_call(
            UUID_METHOD, apiKey=self.api_key, n=n)
        return self.send_request(request_string).parse()

    def generate_blobs(self, n, size, format=FORMAT_BASE64):
        request_string = compose_api_call(
            BLOB_METHOD, apiKey=self.api_key, n=n, size=size, format=format)
        return self.send_request(request_string).parse()

    def get_usage(self):
        request_string = compose_api_call(
            USAGE_METHOD, apiKey=self.api_key)
        self.send_request(request_string)
        return self._result

####################### Digitally-signed API methods ##########################

    def generate_signed_integers(self, n, min, max, replacement=True, base=10):
        request_string = compose_api_call(
            SIGNED_INTEGER_METHOD, apiKey=self.api_key, n=n, min=min, max=max,
            replacement=replacement, base=base)
        return self.send_request(request_string).parse()

    def generate_signed_decimal_fractions(self, n, decimal_places,
                                          replacement=True):
        request_string = compose_api_call(
            SIGNED_DECIMAL_METHOD, apiKey=self.api_key,
            n=n, decimalPlaces=decimal_places, replacement=replacement)
        return self.send_request(request_string).parse()

    def generate_signed_gaussians(self, n, mean, standard_deviation,
                                  significant_digits):
        request_string = compose_api_call(
            SIGNED_GAUSSIAN_METHOD, apiKey=self.api_key,
            n=n, mean=mean,
            standardDeviation=standard_deviation,
            significantDigits=significant_digits)
        return self.send_request(request_string).parse()

    def generate_signed_strings(self, n, length, characters, replacement=True):
        request_string = compose_api_call(
            SIGNED_STRING_METHOD, apiKey=self.api_key,
            n=n, length=length, characters=characters, replacement=replacement)
        return self.send_request(request_string).parse()

    def generate_signed_uuids(self, n):
        request_string = compose_api_call(
            SIGNED_UUID_METHOD, apiKey=self.api_key, n=n)
        return self.send_request(request_string).parse()

    def generate_signed_blobs(self, n, size, format=FORMAT_BASE64):
        request_string = compose_api_call(
            SIGNED_BLOB_METHOD,
            apiKey=self.api_key, n=n, size=size, format=format)
        return self.send_request(request_string).parse()

    def verify_signature(self):
        """
        Verifies signed data with RANDOM.org.
        """
        if not self._signature:
            return None

        json_string = compose_api_call(
            VERIFY_SIGNATURE_METHOD, random=self._random,
            signature=self._signature)

        self.send_request(json_string)

        if AUTHENTICITY in self._result:
            return self._result[AUTHENTICITY]
        else:
            raise Exception("Unable to verify authenticity of signed data")
