---
name: requests
description: >-
  Python HTTP for Humans.
  Use when working with the requests Python package.
license: "Apache-2.0"
compatibility: "Requires python3 and pip. Install with: pip install requests"
metadata:
  version: "2.34.2"
  tool-count: "20"
  generated-by: pip-skill
---

# requests

Python HTTP for Humans.

## Prerequisites

```bash
pip install requests
```

This package requires: charset_normalizer, idna, urllib3, certifi

## Quick Start

```python
import requests

import requests
req = requests.request('GET', 'https://httpbin.org/get')
req
```

## Available Functions

### `requests.request`

Constructs and sends a :class:`Request <Request>`.

**Parameters:**
- `method` (str): method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
- `url` (_t.UriType): URL for the new :class:`Request` object.
**Returns:** Response

```python
import requests
req = requests.request('GET', 'https://httpbin.org/get')
req
```

### `requests.delete`

> [CAUTION] This function modifies or deletes data. Confirm with the user before calling.

Sends a DELETE request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
**Returns:** Response


### `requests.get`

Sends a GET request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
- `params` (_t.ParamsType), optional: (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`.
**Returns:** Response


### `requests.patch`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a PATCH request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
- `data` (_t.DataType), optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
**Returns:** Response


### `requests.post`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a POST request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
- `data` (_t.DataType), optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
- `json` (_t.JsonType), optional: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
**Returns:** Response


### `requests.put`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a PUT request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
- `data` (_t.DataType), optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
**Returns:** Response


### `requests.head`

Sends a HEAD request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
**Returns:** Response


### `requests.options`

Sends an OPTIONS request.

**Parameters:**
- `url` (_t.UriType): URL for the new :class:`Request` object.
**Returns:** Response


### `requests.ConnectTimeout`

The request timed out while trying to connect to the remote server.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** ConnectTimeout


### `requests.ConnectionError`

A Connection error occurred.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** ConnectionError


### `requests.HTTPError`

An HTTP error occurred.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** HTTPError


### `requests.JSONDecodeError`

Couldn't decode the text into json

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** JSONDecodeError


### `requests.PreparedRequest`

The fully mutable :class:`PreparedRequest <PreparedRequest>` object,

**Returns:** PreparedRequest

```python
import requests
req = requests.Request('GET', 'https://httpbin.org/get')
r = req.prepare()
r
```

### `requests.ReadTimeout`

The server did not send any data in the allotted amount of time.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** ReadTimeout


### `requests.RequestException`

There was an ambiguous exception that occurred while handling your

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** RequestException


### `requests.Session`

A Requests session.

**Returns:** Session

```python
import requests
s = requests.Session()
s.get('https://httpbin.org/get')
```

### `requests.Timeout`

The request timed out.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** Timeout


### `requests.TooManyRedirects`

Too many redirects.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** TooManyRedirects


### `requests.URLRequired`

A valid URL is required to make a request.

**Parameters:**
- `args` (Any)
- `kwargs` (Any)
**Returns:** URLRequired


### `requests.Response`

The :class:`Response <Response>` object, which contains a

**Returns:** Response



## Usage Pattern

To use requests, write inline Python and execute via the Bash tool:

```python
python3 -c "
import requests
# your code here
"
```

## Safety Guidelines

- Never output API keys, tokens, or credentials in responses
- When writing files, confirm the path with the user first
- If a function modifies external state (writes files, sends requests, deletes data), describe the action before executing

## Full API Reference

For detailed API documentation including all parameters, types, and examples,
read the file `references/api-reference.md` in this skill directory.

