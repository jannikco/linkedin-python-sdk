"""Additive ergonomic resources over the public operation-ID contract; responses remain raw envelopes."""
from .types import Envelope

class _Resource:
    def __init__(self, client): self._client = client
    def _read(self, operation, **query) -> Envelope:
        return self._client.request(operation, query={k:v for k,v in query.items() if v is not None})
    def _post(self, operation, body, idempotency_key, path=None) -> Envelope:
        return self._client.request(operation, path=path or {}, body={k:v for k,v in body.items() if v is not None}, idempotency_key=idempotency_key)

class People(_Resource):
    def search(self, keywords, *, idempotency_key, limit=10, page=None, profile_id=None, wait=None, dry_run=None) -> Envelope:
        if not isinstance(keywords,list) or not keywords or any(not isinstance(k,str) or not k.strip() for k in keywords): raise ValueError('keywords must be a non-empty list of strings')
        return self._post('search_post',dict(keywords=keywords,limit=limit,page=page,profile_id=profile_id,wait=wait,dry_run=dry_run),idempotency_key)

class Profiles(_Resource):
    def enrich(self, *, idempotency_key, linkedin_urn=None, public_id=None, lead_id=None, include_email=None, profile_id=None, wait=None, dry_run=None) -> Envelope:
        if not any(isinstance(v,str) and v.strip() for v in (linkedin_urn,public_id,lead_id)): raise ValueError('Provide linkedin_urn, public_id or lead_id')
        return self._post('enrich_post',dict(linkedin_urn=linkedin_urn,public_id=public_id,lead_id=lead_id,include_email=include_email,profile_id=profile_id,wait=wait,dry_run=dry_run),idempotency_key)

class Posts(_Resource):
    def engagers(self, post_urn, *, idempotency_key, limit=10, page=None, profile_id=None, wait=None, dry_run=None) -> Envelope:
        if not isinstance(post_urn,str) or not post_urn.startswith('urn:li:'): raise ValueError('An explicit complete LinkedIn post URN is required')
        return self._post('list_post_engagers_post',dict(post_urn=post_urn,limit=limit,page=page,profile_id=profile_id,wait=wait,dry_run=dry_run),idempotency_key)

class Prospects(_Resource):
    def list(self, *, search=None, kind=None, page=None, profile_id=None) -> Envelope:
        return self._read('list_prospects_get',search=search,kind=kind,page=page,profile_id=profile_id)
    def get(self, prospect_id, *, profile_id=None) -> Envelope:
        if not isinstance(prospect_id,str) or not prospect_id: raise ValueError('prospect_id is required')
        return self._read('list_prospects_get',id=prospect_id,profile_id=profile_id)
    def promote(self, prospect_id, *, idempotency_key, approved=False, profile_id=None) -> Envelope:
        if approved is not True: raise ValueError('Explicit approved=True is required for prospect promotion')
        return self._post('manage_prospect_promote_post',dict(profile_id=profile_id),idempotency_key,path={'id':prospect_id})

class Leads(_Resource):
    def list(self, *, search=None, status=None, page=None, per_page=None, profile_id=None) -> Envelope:
        return self._read('list_leads_get',search=search,status=status,page=page,per_page=per_page,profile_id=profile_id)
    def export(self, *, source=None, tag=None, has_email=None, since=None, limit=None, cursor=None, profile_id=None) -> Envelope:
        return self._read('export_leads_get',source=source,tag=tag,has_email=has_email,since=since,limit=limit,cursor=cursor,profile_id=profile_id)

class Crm(_Resource):
    def sync_lead(self, lead_id, *, provider, idempotency_key, approved=False, profile_id=None) -> Envelope:
        if approved is not True: raise ValueError('Explicit approved=True is required for external CRM sync')
        if not isinstance(provider,str) or not provider.strip(): raise ValueError('Name an explicit connected external provider')
        return self._post('sync_lead_to_crm_post',dict(provider=provider,profile_id=profile_id),idempotency_key,path={'lead_id':lead_id})

class Jobs(_Resource):
    def wait(self, job_id, *, timeout=60, interval=1) -> Envelope:
        return self._client.wait_for_job(job_id,timeout=timeout,interval=interval)
    def get(self, job_id, *, wait=None, profile_id=None) -> Envelope:
        return self._client.request('get_job_get',path={'job_id':job_id},query={k:v for k,v in dict(wait=wait,profile_id=profile_id).items() if v is not None})

def attach(client):
    for name,resource in [('people',People),('profiles',Profiles),('posts',Posts),('prospects',Prospects),('leads',Leads),('crm',Crm),('jobs',Jobs)]: setattr(client,name,resource(client))
