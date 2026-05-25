---
name: requests
description: >-
  Python HTTP for Humans.
  Use when working with the requests Python package.
license: Apache-2.0
compatibility: Requires python3 and pip. Install with: pip install requests
metadata:
  version: "2.32.5"
  tool-count: "20"
  generated-by: pip-skill
  homepage: "https://requests.readthedocs.io"
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
req = requests.Request('GET', 'https://httpbin.org/get')
req.prepare()
```

## Available Functions

### `requests.Request`

A user-created :class:`Request <Request>` object.

**Parameters:**
- `method`, optional: HTTP method to use.
- `url`, optional: URL to send.
- `headers`, optional: dictionary of headers to send.
- `files`, optional: dictionary of {filename: fileobject} files to multipart upload.
- `data`, optional: the body to attach to the request. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place.
- `params`, optional: URL parameters to append to the URL. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place.
- `auth`, optional: Auth handler or (user, pass) tuple.
- `cookies`, optional: dictionary or CookieJar of cookies to attach to this request.
- `hooks`, optional: dictionary of callback hooks, for internal usage.
Usage::

  >>> import requests
  >>> req = requests.Request('GET', 'https://httpbin.org/get')
  >>> req.prepare()
  <PreparedRequest [GET]>
- `json`, optional: json for the body to attach to the request (if files or data is not specified).
**Returns:** Request

```python
import requests
req = requests.Request('GET', 'https://httpbin.org/get')
req.prepare()
```

### `requests.PreparedRequest`

The fully mutable :class:`PreparedRequest <PreparedRequest>` object,

**Returns:** PreparedRequest

```python
import requests
req = requests.Request('GET', 'https://httpbin.org/get')
r = req.prepare()
r
```

### `requests.Session`

A Requests session.

**Returns:** Session

```python
import requests
s = requests.Session()
s.get('https://httpbin.org/get')
```

### `requests.Response`

The :class:`Response <Response>` object, which contains a

**Returns:** Response


### `requests.delete`

> [CAUTION] This function modifies or deletes data. Confirm with the user before calling.

Sends a DELETE request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.


### `requests.get`

Sends a GET request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.
- `params`, optional: (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`.


### `requests.patch`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a PATCH request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.
- `data`, optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.


### `requests.post`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a POST request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.
- `data`, optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
- `json`, optional: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.


### `requests.put`

> [NOTE] This function writes or sends data. Verify parameters before calling.

Sends a PUT request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.
- `data`, optional: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.


### `requests.head`

Sends a HEAD request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.


### `requests.options`

Sends an OPTIONS request.

**Parameters:**
- `url`: URL for the new :class:`Request` object.


### `requests.ConnectTimeout`

The request timed out while trying to connect to the remote server.

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** ConnectTimeout


### `requests.ConnectionError`

A Connection error occurred.

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** ConnectionError


### `requests.FileModeWarning`

A file was opened in text mode, but Requests determined its binary length.

**Parameters:**
- `args`
- `kwargs`
**Returns:** FileModeWarning


### `requests.HTTPError`

An HTTP error occurred.

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** HTTPError


### `requests.JSONDecodeError`

Couldn't decode the text into json

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** JSONDecodeError


### `requests.ReadTimeout`

The server did not send any data in the allotted amount of time.

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** ReadTimeout


### `requests.RequestException`

There was an ambiguous exception that occurred while handling your

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** RequestException


### `requests.RequestsDependencyWarning`

An imported dependency doesn't match the expected version range.

**Parameters:**
- `args`
- `kwargs`
**Returns:** RequestsDependencyWarning


### `requests.Timeout`

The request timed out.

**Parameters:**
- `args`, optional
- `kwargs`, optional
**Returns:** Timeout



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

## External Documentation

Official docs: https://requests.readthedocs.io
