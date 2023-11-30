from urllib.parse import urlencode, parse_qs, urlsplit, urlunsplit

def setQueryParameter(url, params: dict) -> str:
    """Given a URL, set or replace a query parameter and return the
    modified URL.

    >>> set_query_parameter('http://example.com?foo=bar&biz=baz', {'foo', 'stuff'})
    'http://example.com?foo=stuff&biz=baz'

    """
    if params is None:
        return url
    elif type(params) != dict:
        raise Exception('Parameter [params] should be a dict.')
    elif len(params) == 0:
        return url
    elif url is None:
        return None
    
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    if params is not None:
        for key, value in params.items():
            query_params[key] = [value]
    new_query_string = urlencode(query_params, doseq=True)
    return str(urlunsplit((scheme, netloc, path, new_query_string, fragment)))
