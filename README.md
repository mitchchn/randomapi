randomapi
=========

Python implementation of the RANDOM.org JSON-RPC API:
http://api.random.org/json-rpc/1/

RANDOM.org generates true random numbers using a seed based on atmospheric radio noise. This is useful for applications where pseudo-random generators are not good enough, such as cryptography.

Features
--------

- Implements all basic methods and signed methods
- Downloads random data over a 4096-bit SSL connection
- Respects advisory delay requests from the server
- Has no external dependencies
- Optional: Verifies signed data with RANDOM.org, using SHA-512 hashes to ensure that it's legitimate

Requirements
------------

- Python 2.6 or higher
- An API key from: http://api.random.org

Example Usage
-------------

    # Returns a list of 5 true random numbers between 0 and 10

    random_client = RandomJSONRPC(api_key) # Requires a valid API key
    nums = random_client.generate_integers(n=5, min=0, max=10)
