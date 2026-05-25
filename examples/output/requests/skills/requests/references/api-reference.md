# requests API Reference

Package: requests v2.32.5
Import: `import requests`
Homepage: https://requests.readthedocs.io

---

## `requests.Request`

Used to prepare a :class:`PreparedRequest <PreparedRequest>`, which is sent to the server.

Parameters:
  method: HTTP method to use.
  url: URL to send.
  headers: dictionary of headers to send.
  files: dictionary of {filename: fileobject} files to multipart upload.
  data: the body to attach to the request. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place.
  json: json for the body to attach to the request (if files or data is not specified).
  params: URL parameters to append to the URL. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place.
  auth: Auth handler or (user, pass) tuple.
  cookies: dictionary or CookieJar of cookies to attach to this request.
  hooks: dictionary of callback hooks, for internal usage.
Usage::

  >>> import requests
  >>> req = requests.Request('GET', 'https://httpbin.org/get')
  >>> req.prepare()
  <PreparedRequest [GET]>

### Signature

```python
requests.Request(method = None, url = None, headers = None, files = None, data = None, params = None, auth = None, cookies = None, hooks = None, json = None) -> Request
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `method` | `any` | No | None | HTTP method to use. |
| `url` | `any` | No | None | URL to send. |
| `headers` | `any` | No | None | dictionary of headers to send. |
| `files` | `any` | No | None | dictionary of {filename: fileobject} files to multipart upload. |
| `data` | `any` | No | None | the body to attach to the request. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place. |
| `params` | `any` | No | None | URL parameters to append to the URL. If a dictionary or
list of tuples ``[(key, value)]`` is provided, form-encoding will
take place. |
| `auth` | `any` | No | None | Auth handler or (user, pass) tuple. |
| `cookies` | `any` | No | None | dictionary or CookieJar of cookies to attach to this request. |
| `hooks` | `any` | No | None | dictionary of callback hooks, for internal usage.
Usage::

  >>> import requests
  >>> req = requests.Request('GET', 'https://httpbin.org/get')
  >>> req.prepare()
  <PreparedRequest [GET]> |
| `json` | `any` | No | None | json for the body to attach to the request (if files or data is not specified). |

### Returns

`Request`

### Example

```python
import requests
req = requests.Request('GET', 'https://httpbin.org/get')
req.prepare()
```

### JSON Schema

```json
{
  "properties": {
    "auth": {
      "description": "Auth handler or (user, pass) tuple."
    },
    "cookies": {
      "description": "dictionary or CookieJar of cookies to attach to this request."
    },
    "data": {
      "description": "the body to attach to the request. If a dictionary or\nlist of tuples ``[(key, value)]`` is provided, form-encoding will\ntake place."
    },
    "files": {
      "description": "dictionary of {filename: fileobject} files to multipart upload."
    },
    "headers": {
      "description": "dictionary of headers to send."
    },
    "hooks": {
      "description": "dictionary of callback hooks, for internal usage.\nUsage::\n\n  \u003e\u003e\u003e import requests\n  \u003e\u003e\u003e req = requests.Request(\u0027GET\u0027, \u0027https://httpbin.org/get\u0027)\n  \u003e\u003e\u003e req.prepare()\n  \u003cPreparedRequest [GET]\u003e"
    },
    "json": {
      "description": "json for the body to attach to the request (if files or data is not specified)."
    },
    "method": {
      "description": "HTTP method to use."
    },
    "params": {
      "description": "URL parameters to append to the URL. If a dictionary or\nlist of tuples ``[(key, value)]`` is provided, form-encoding will\ntake place."
    },
    "url": {
      "description": "URL to send."
    }
  },
  "type": "object"
}
```

---

## `requests.PreparedRequest`

containing the exact bytes that will be sent to the server.

Instances are generated from a :class:`Request <Request>` object, and
should not be instantiated manually; doing so may produce undesirable
effects.

Usage::

  >>> import requests
  >>> req = requests.Request('GET', 'https://httpbin.org/get')
  >>> r = req.prepare()
  >>> r
  <PreparedRequest [GET]>

  >>> s = requests.Session()
  >>> s.send(r)
  <Response [200]>

### Signature

```python
requests.PreparedRequest() -> PreparedRequest
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|

### Returns

`PreparedRequest`

### Example

```python
import requests
req = requests.Request('GET', 'https://httpbin.org/get')
r = req.prepare()
r
```

### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.Session`

Provides cookie persistence, connection-pooling, and configuration.

Basic Usage::

  >>> import requests
  >>> s = requests.Session()
  >>> s.get('https://httpbin.org/get')
  <Response [200]>

Or as a context manager::

  >>> with requests.Session() as s:
  ...     s.get('https://httpbin.org/get')
  <Response [200]>

### Signature

```python
requests.Session() -> Session
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|

### Returns

`Session`

### Example

```python
import requests
s = requests.Session()
s.get('https://httpbin.org/get')
```

### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.Response`

server's response to an HTTP request.

### Signature

```python
requests.Response() -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|

### Returns

`Response`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.delete`

Parameters:
  url: URL for the new :class:`Request` object.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.delete(url)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |



### JSON Schema

```json
{
  "properties": {
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.get`

Parameters:
  url: URL for the new :class:`Request` object.
  params: (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.get(url, params = None)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |
| `params` | `any` | No | None | (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`. |



### JSON Schema

```json
{
  "properties": {
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "params": {
      "description": "(optional) Dictionary, list of tuples or bytes to send\nin the query string for the :class:`Request`."
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.patch`

Parameters:
  url: URL for the new :class:`Request` object.
  data: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
  json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.patch(url, data = None)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `any` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |



### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`."
    },
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.post`

Parameters:
  url: URL for the new :class:`Request` object.
  data: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
  json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.post(url, data = None, json = None)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `any` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |
| `json` | `any` | No | None | (optional) A JSON serializable Python object to send in the body of the :class:`Request`. |



### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`."
    },
    "json": {
      "description": "(optional) A JSON serializable Python object to send in the body of the :class:`Request`."
    },
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.put`

Parameters:
  url: URL for the new :class:`Request` object.
  data: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
  json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.put(url, data = None)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `any` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |



### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`."
    },
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.head`

Parameters:
  url: URL for the new :class:`Request` object.
  \*\*kwargs: Optional arguments that ``request`` takes. If
`allow_redirects` is not provided, it will be set to `False` (as
opposed to the default :meth:`request` behavior).

Returns: :class:`Response <Response>` object

### Signature

```python
requests.head(url)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |



### JSON Schema

```json
{
  "properties": {
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.options`

Parameters:
  url: URL for the new :class:`Request` object.
  \*\*kwargs: Optional arguments that ``request`` takes.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.options(url)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `any` | Yes | - | URL for the new :class:`Request` object. |



### JSON Schema

```json
{
  "properties": {
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "url"
  ],
  "type": "object"
}
```

---

## `requests.ConnectTimeout`

Requests that produced this error are safe to retry.

### Signature

```python
requests.ConnectTimeout(args = None, kwargs = None) -> ConnectTimeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`ConnectTimeout`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.ConnectionError`

A Connection error occurred.

### Signature

```python
requests.ConnectionError(args = None, kwargs = None) -> ConnectionError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`ConnectionError`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.FileModeWarning`

A file was opened in text mode, but Requests determined its binary length.

### Signature

```python
requests.FileModeWarning(args, kwargs) -> FileModeWarning
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | Yes | - | - |
| `kwargs` | `any` | Yes | - | - |

### Returns

`FileModeWarning`


### JSON Schema

```json
{
  "properties": {
    "args": {
      "type": "string"
    },
    "kwargs": {
      "type": "string"
    }
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.HTTPError`

An HTTP error occurred.

### Signature

```python
requests.HTTPError(args = None, kwargs = None) -> HTTPError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`HTTPError`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.JSONDecodeError`

Couldn't decode the text into json

### Signature

```python
requests.JSONDecodeError(args = None, kwargs = None) -> JSONDecodeError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`JSONDecodeError`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.ReadTimeout`

The server did not send any data in the allotted amount of time.

### Signature

```python
requests.ReadTimeout(args = None, kwargs = None) -> ReadTimeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`ReadTimeout`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.RequestException`

request.

### Signature

```python
requests.RequestException(args = None, kwargs = None) -> RequestException
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`RequestException`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---

## `requests.RequestsDependencyWarning`

An imported dependency doesn't match the expected version range.

### Signature

```python
requests.RequestsDependencyWarning(args, kwargs) -> RequestsDependencyWarning
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | Yes | - | - |
| `kwargs` | `any` | Yes | - | - |

### Returns

`RequestsDependencyWarning`


### JSON Schema

```json
{
  "properties": {
    "args": {
      "type": "string"
    },
    "kwargs": {
      "type": "string"
    }
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.Timeout`

Catching this error will catch both

### Signature

```python
requests.Timeout(args = None, kwargs = None) -> Timeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `any` | No | - | - |
| `kwargs` | `any` | No | - | - |

### Returns

`Timeout`


### JSON Schema

```json
{
  "properties": {},
  "type": "object"
}
```

---


*Generated by pip-skill v0.1.1.dev4+gb29a5d18a.d20260525 on 1970-01-01T00:00:00+00:00*
