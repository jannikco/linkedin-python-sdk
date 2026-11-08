"""Stdlib LeadAdapter client. Generated request metadata; no automatic action retries."""
import json
import math
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

operations = json.loads(Path(__file__).with_name('operations.json').read_text())

class LeadAdapterError(Exception):
    def __init__(self, code, status=0, request_id=None, retry_after=None, result=None):
        super().__init__('LeadAdapter request failed; inspect code and request_id.')
        self.code, self.status = code, status
        self.request_id, self.retry_after, self.result = request_id, retry_after, result

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _transport(url, method, headers, body, timeout):
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()
    except (URLError, TimeoutError, OSError):
        raise LeadAdapterError('transport_error') from None

def _query(value, name, output):
    if value is None: return
    if isinstance(value, (tuple,list)):
        for item in value: _query(item, name+'[]', output)
    elif isinstance(value, dict):
        for key,item in value.items(): _query(item, name+'['+str(key)+']', output)
    else:
        output.append((name, str(value).lower() if isinstance(value,bool) else str(value)))

def _parameters(value, metadata, location):
    if not isinstance(value,dict): raise ValueError(location+' must be an object')
    available={p['name']:p for p in metadata['parameters'] if p['in']==location}
    if set(value)-set(available): raise ValueError('Unknown '+location+' parameter')
    for key,p in available.items():
        if p.get('required') and value.get(key) is None: raise ValueError('Missing '+location+' parameter: '+key)

class LeadAdapterClient:
    def __init__(self, api_key, base_url='https://leadadapter.com/api/v1', *, allow_custom_origin=False, timeout=30, transport=None):
        if not isinstance(api_key,str) or not api_key.strip() or '\r' in api_key or '\n' in api_key: raise ValueError('A non-empty API key without line breaks is required')
        try:
            url=urlsplit(base_url)
            port=url.port
        except (ValueError, TypeError): raise ValueError('Invalid base URL') from None
        loopback=url.hostname in ('localhost','127.0.0.1','::1')
        if not url.hostname or url.username or url.password or url.query or url.fragment or url.scheme not in ('http','https'): raise ValueError('Unsafe base URL')
        if url.scheme!='https' and not (loopback and allow_custom_origin): raise ValueError('HTTPS is required')
        if not allow_custom_origin and (url.scheme!='https' or url.hostname!='leadadapter.com' or port not in (None,443)): raise ValueError('Custom origin requires allow_custom_origin=True')
        if not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or timeout<=0: raise ValueError('timeout must be positive and finite')
        self.__key=api_key
        self.__base=urlunsplit((url.scheme,url.netloc,url.path.rstrip('/'),'',''))
        self.__timeout=timeout
        self.__transport=transport or _transport

    def request(self, operation_id, *, path=None, query=None, body=None, idempotency_key=None, timeout=None):
        if operation_id not in operations: raise ValueError('Unknown LeadAdapter operation')
        op=operations[operation_id]
        path={} if path is None else path
        query={} if query is None else query
        _parameters(path,op,'path'); _parameters(query,op,'query')
        if op['idempotencyRequired'] and (not isinstance(idempotency_key,str) or not idempotency_key.strip()): raise ValueError('An explicit idempotency_key is required; preserve it for retries')
        if idempotency_key is not None and (not isinstance(idempotency_key,str) or not idempotency_key.strip() or '\r' in idempotency_key or '\n' in idempotency_key or len(idempotency_key.encode())>200): raise ValueError('Invalid idempotency_key')
        if body is not None and (op['method']=='GET' or op['requestSchema'] is None or not isinstance(body,dict)): raise ValueError('This operation requires an object JSON body or no body')
        resource=op['path']
        for key,value in path.items():
            if isinstance(value,bool) or not isinstance(value,(str,int)) or str(value) in ('','.','..'): raise ValueError('Invalid path parameter')
            resource=resource.replace('{'+key+'}',quote(str(value),safe=''))
        pairs=[]
        for key,value in query.items(): _query(value,key,pairs)
        url=self.__base+resource+('?' + urlencode(pairs) if pairs else '')
        headers={'Accept':'application/json','Authorization':'Bearer '+self.__key}
        if idempotency_key is not None: headers['Idempotency-Key']=idempotency_key
        payload=None
        if op['method']!='GET':
            headers['Content-Type']='application/json'
            payload=json.dumps({} if body is None else body,allow_nan=False).encode()
        effective_timeout=self.__timeout if timeout is None else timeout
        if not isinstance(effective_timeout,(int,float)) or not math.isfinite(effective_timeout) or effective_timeout<=0: raise ValueError('timeout must be positive and finite')
        status, response_headers, raw=self.__transport(url,op['method'],headers,payload,effective_timeout)
        normalized={key.lower():value for key,value in response_headers.items()}
        try: result=json.loads(raw)
        except (ValueError,TypeError): raise LeadAdapterError('invalid_response',status,normalized.get('x-request-id')) from None
        if not isinstance(result,dict) or (not op['legacy'] and 200<=status<300 and not isinstance(result.get('ok'),bool)): raise LeadAdapterError('invalid_response',status)
        if not 200<=status<300 or result.get('ok') is False:
            error=result.get('error')
            code=error.get('code') if isinstance(error,dict) else None
            raise LeadAdapterError(code or 'http_'+str(status),status,normalized.get('x-request-id',result.get('request_id')),normalized.get('retry-after'),result)
        return result

    def wait_for_job(self, job_id, *, timeout=60, interval=1):
        if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in (timeout,interval)): raise ValueError('timeout and interval must be positive and finite')
        deadline=time.monotonic()+timeout
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0: raise LeadAdapterError('poll_timeout')
            result=self.request('get_job_get',path={'job_id':job_id},timeout=min(remaining,self.__timeout))
            job=result.get('data')
            if not isinstance(job,dict) or not isinstance(job.get('status'),str): raise LeadAdapterError('invalid_response')
            if job.get('finished') is True or job['status'] in ('done','failed','cancelled'): return result
            time.sleep(min(interval,max(0,deadline-time.monotonic())))
