# requests API Reference

Package: requests v2.34.2
Import: `import requests`

---

## `requests.request`

Parameters:
  method: method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
  url: URL for the new :class:`Request` object.
  params: (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`.
  data: (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`.
  json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
  headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
  cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
  files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content_type'`` is a string
defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
to add for the file.
  auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
  timeout (float or tuple): (optional) How many seconds to wait for the server to send data
before giving up, as a float, or a :ref:`(connect timeout, read
timeout) <timeouts>` tuple.
  allow_redirects (bool): (optional) Boolean. Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``True``.
  proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
  verify: (optional) Either a boolean, in which case it controls whether we verify
the server's TLS certificate, or a string, in which case it must be a path
to a CA bundle to use. Defaults to ``True``.
  stream: (optional) if ``False``, the response content will be immediately downloaded.
  cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.

Returns: :class:`Response <Response>` object

### Signature

```python
requests.request(method: str, url: _t.UriType) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `method` | `str` | Yes | - | method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``. |
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |

### Returns

`Response`

### Example

```python
import requests
req = requests.request('GET', 'https://httpbin.org/get')
req
```

### JSON Schema

```json
{
  "properties": {
    "kwargs": {
      "additionalProperties": true,
      "description": "Additional keyword arguments (**kwargs)",
      "type": "object"
    },
    "method": {
      "description": "method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.",
      "type": "string"
    },
    "url": {
      "description": "URL for the new :class:`Request` object.",
      "type": "string"
    }
  },
  "required": [
    "method",
    "url"
  ],
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
requests.delete(url: _t.UriType) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |

### Returns

`Response`


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
requests.get(url: _t.UriType, params: _t.ParamsType = None) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |
| `params` | `_t.ParamsType` | No | None | (optional) Dictionary, list of tuples or bytes to send
in the query string for the :class:`Request`. |

### Returns

`Response`


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
      "description": "(optional) Dictionary, list of tuples or bytes to send\nin the query string for the :class:`Request`.",
      "type": "string"
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
requests.patch(url: _t.UriType, data: _t.DataType = None) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `_t.DataType` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |

### Returns

`Response`


### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`.",
      "type": "string"
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
requests.post(url: _t.UriType, data: _t.DataType = None, json: _t.JsonType = None) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `_t.DataType` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |
| `json` | `_t.JsonType` | No | None | (optional) A JSON serializable Python object to send in the body of the :class:`Request`. |

### Returns

`Response`


### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`.",
      "type": "string"
    },
    "json": {
      "description": "(optional) A JSON serializable Python object to send in the body of the :class:`Request`.",
      "type": "string"
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
requests.put(url: _t.UriType, data: _t.DataType = None) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |
| `data` | `_t.DataType` | No | None | (optional) Dictionary, list of tuples, bytes, or file-like
object to send in the body of the :class:`Request`. |

### Returns

`Response`


### JSON Schema

```json
{
  "properties": {
    "data": {
      "description": "(optional) Dictionary, list of tuples, bytes, or file-like\nobject to send in the body of the :class:`Request`.",
      "type": "string"
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
requests.head(url: _t.UriType) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |

### Returns

`Response`


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
requests.options(url: _t.UriType) -> Response
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `_t.UriType` | Yes | - | URL for the new :class:`Request` object. |

### Returns

`Response`


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
requests.ConnectTimeout(args: Any, kwargs: Any) -> ConnectTimeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`ConnectTimeout`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.ConnectionError`

A Connection error occurred.

### Signature

```python
requests.ConnectionError(args: Any, kwargs: Any) -> ConnectionError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`ConnectionError`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
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
requests.HTTPError(args: Any, kwargs: Any) -> HTTPError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`HTTPError`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.JSONDecodeError`

Couldn't decode the text into json

### Signature

```python
requests.JSONDecodeError(args: Any, kwargs: Any) -> JSONDecodeError
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`JSONDecodeError`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
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

## `requests.ReadTimeout`

The server did not send any data in the allotted amount of time.

### Signature

```python
requests.ReadTimeout(args: Any, kwargs: Any) -> ReadTimeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`ReadTimeout`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.RequestException`

request.

### Signature

```python
requests.RequestException(args: Any, kwargs: Any) -> RequestException
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`RequestException`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
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

## `requests.Timeout`

Catching this error will catch both

### Signature

```python
requests.Timeout(args: Any, kwargs: Any) -> Timeout
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`Timeout`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.TooManyRedirects`

Too many redirects.

### Signature

```python
requests.TooManyRedirects(args: Any, kwargs: Any) -> TooManyRedirects
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`TooManyRedirects`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
  "type": "object"
}
```

---

## `requests.URLRequired`

A valid URL is required to make a request.

### Signature

```python
requests.URLRequired(args: Any, kwargs: Any) -> URLRequired
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `args` | `Any` | Yes | - | - |
| `kwargs` | `Any` | Yes | - | - |

### Returns

`URLRequired`


### JSON Schema

```json
{
  "properties": {
    "args": {},
    "kwargs": {}
  },
  "required": [
    "args",
    "kwargs"
  ],
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


*Generated by pip-skill v0.1.1.dev0+g2ace04cc9.d20260525 on 1970-01-01T00:00:00+00:00*
