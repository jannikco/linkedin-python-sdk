"""Research-to-CRM orchestration using exact stored prospect identities and explicit write approval."""
import copy
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from . import LeadAdapterError
from .types import job_id

CONTRACT=json.loads(Path(__file__).with_name('workflow-contract.json').read_text())

def plan_research_to_crm():
    return {'workflow':'research-to-crm','mode':'plan','destination':'leadadapter-native-crm','steps':['people.search','jobs.wait','prospects.list/get: exact identity match','review exact prospect IDs','approved prospects.promote','optional explicitly approved crm.sync_lead with named provider'],'requires_live':['LEADADAPTER_API_KEY','connected LinkedIn execution and required consent','api:read; api:write only for approved promotion/sync'],'network_calls':0,'writes':0}

def _save(path,state):
    if path is None:return
    path=Path(path)
    if path.is_symlink():raise ValueError('Checkpoint symlinks are refused')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'-',dir=str(path.parent))
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(state,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextmanager
def _lock(path):
    if path is None:yield;return
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);lock=target.with_name(target.name+'.lock')
    try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise ValueError('Checkpoint is locked; inspect any interrupted run before removing its lock') from None
    try:os.close(fd);yield
    finally:lock.unlink(missing_ok=True)

def _identities(row):
    if not isinstance(row,dict):return set()
    result=set()
    for kind,fields in [('urn',CONTRACT['identity']['urnFields']),('public_id',CONTRACT['identity']['publicIdFields'])]:
        for field in fields:
            value=row.get(field)
            if isinstance(value,str) and value:result.add((kind,value))
    return result

def _rows(result):
    if isinstance(result,list):return [r for r in result if isinstance(r,dict)]
    if isinstance(result,dict):
        for key in CONTRACT['identity']['resultContainers']:
            if isinstance(result.get(key),list):return [r for r in result[key] if isinstance(r,dict)]
    return []

def _data(receipt):
    if not isinstance(receipt,dict) or receipt.get('ok') is not True or not isinstance(receipt.get('data'),dict):raise LeadAdapterError('invalid_response')
    return receipt['data']

def _public(state):
    status={'awaiting_selection':'review-required','awaiting_promotion_approval':'review-required','pending_ingestion':'pending-ingestion','awaiting_external_crm_approval':'external-approval-required','reconciliation_required':'reconciliation-required','research_failed':'research-failed'}.get(state['stage'],state['stage'].replace('_','-'))
    records=[{k:r[k] for k in ['prospect_id','lead_id','promote_state','sync_state','external_id'] if k in r} for r in state.get('records',[])]
    for record in records:
        if record.get('promote_state')=='done':record['promote_state']='complete'
        if record.get('sync_state')=='done':record['sync_state']='complete'
        elif not state.get('provider'):record['sync_state']='not-requested'
        elif record.get('lead_id') and 'sync_state' not in record:record['sync_state']='approval-required'
    prospects=[]
    for candidate in state.get('candidates',[]):
        row=copy.deepcopy(candidate)
        matched=next((r for r in records if r['prospect_id']==row['prospect_id']),None)
        if matched and matched.get('lead_id'):row['lead_id']=matched['lead_id']
        prospects.append(row)
    return {'workflow':'research-to-crm','mode':state['mode'],'run_id':state['run_id'],'status':status,'stage':state['stage'],'job_id':state.get('job_id'),'destination':state.get('provider') or 'leadadapter-native-crm','candidates':state.get('candidates',[]),'prospects':prospects,'records':records,'reason':state.get('reason'),'resumable':state['stage'] not in ['complete','research_failed']}

def run_research_to_crm(client, *, keywords=None, profile_id=None, prospect_ids=None, prospect_urns=None, provider=None, approve_promote=False, approve_crm=False, checkpoint=None, mode='live', poll_timeout=60, poll_interval=1, max_pages=10):
    """Default target is native CRM; selecting records never grants write approval.

    Missing ingestion and selection/approval waits return resumable stages. A write with
    an ambiguous outcome is held for manual reconciliation, never blindly replayed.
    """
    if mode not in ('live','fixture'):raise ValueError('mode must be live or fixture')
    if mode=='live' and not checkpoint:raise ValueError('Live workflows require a durable checkpoint')
    fingerprint=getattr(client,'account_fingerprint',None)
    if not isinstance(fingerprint,str) or not re.fullmatch(r'[a-f0-9]{64}',fingerprint):raise ValueError('Workflow requires an SDK client with a credential-context fingerprint')
    if not isinstance(max_pages,int) or max_pages<1 or max_pages>100:raise ValueError('max_pages must be1-100')
    with _lock(checkpoint):
        if checkpoint and Path(checkpoint).exists():
            if Path(checkpoint).is_symlink():raise ValueError('Checkpoint symlinks are refused')
            state=json.loads(Path(checkpoint).read_text())
            if state.get('version')!=1 or state.get('workflow')!='research-to-crm':raise ValueError('Unsupported checkpoint')
            if state.get('account_fingerprint')!=fingerprint:raise ValueError('Checkpoint account/key fingerprint differs or is missing; use the original credential context or a new checkpoint')
            for key,value in [('keywords',keywords),('profile_id',profile_id),('provider',provider)]:
                if value is not None and value!=state.get(key):raise ValueError('Resume parameters differ from checkpoint: '+key)
            if state.get('mode')!=mode:raise ValueError('Cannot resume a checkpoint in a different execution mode')
            provider=state.get('provider');profile_id=state.get('profile_id');keywords=state['keywords']
        else:
            if not isinstance(keywords,list) or not keywords or any(not isinstance(k,str) or not k.strip() for k in keywords):raise ValueError('At least one explicit keyword is required')
            state={'version':1,'workflow':'research-to-crm','mode':mode,'run_id':str(uuid.uuid4()),'keywords':keywords,'profile_id':profile_id,'provider':provider,'research_key':str(uuid.uuid4()),'account_fingerprint':fingerprint,'stage':'research_pending','records':[],'selected_ids':[],'selected_urns':[]}
        if approve_crm and not provider:raise ValueError('An explicit provider is required for external CRM approval')
        for key,value in [('selected_ids',prospect_ids),('selected_urns',prospect_urns)]:
            if value:
                value=sorted(set(value))
                if state.get(key) and value!=state[key]:raise ValueError('Selected identities differ from checkpoint')
                state[key]=value
        def save(stage=None,reason=None):
            if stage:state['stage']=stage
            state['reason']=reason;_save(checkpoint,state)
        if any(r.get(k) in ('pending','uncertain') for r in state['records'] for k in ('promote_state','sync_state')):
            save('reconciliation_required','A previous write intent has an uncertain outcome; inspect provider state before creating a new run.')
            return _public(state)
        if state.get('stage')=='complete':return _public(state)
        if 'research_identities' not in state:
            if not state.get('job_id'):
                save('research_pending')
                receipt=client.people.search(keywords,idempotency_key=state['research_key'],profile_id=profile_id,limit=10)
                identifier=job_id(receipt)
                inline=_data(receipt)
                if identifier:state['job_id']=identifier;save('research_queued')
                elif inline.get('job_status')=='done':
                    if inline.get('error') is not None:save('research_failed','Research returned an error with its terminal receipt; no promotion was attempted.');return _public(state)
                    state['research_identities']=[list(x) for r in _rows(inline.get('result')) for x in sorted(_identities(r))];save('research_completed')
                else:raise LeadAdapterError('missing_job_receipt')
            if 'research_identities' not in state:
                try:receipt=client.jobs.wait(state['job_id'],timeout=poll_timeout,interval=poll_interval)
                except LeadAdapterError as error:
                    if error.code=='poll_timeout':save('research_queued','Research is still running; resume the same checkpoint.');return _public(state)
                    raise
                data=_data(receipt)
                if data.get('job_id')!=state['job_id']:raise LeadAdapterError('job_identity_mismatch')
                if data.get('status')!='done' or data.get('error') is not None:save('research_failed','Research ended without completed results: '+str(data.get('status')));return _public(state)
                state['research_identities']=[list(x) for r in _rows(data.get('result')) for x in sorted(_identities(r))];save('research_completed')
        observed={tuple(x) for x in state['research_identities']}
        if not observed:save('awaiting_identity','Completed result has no supported exact identity; no name matching or promotion was attempted.');return _public(state)
        if state['selected_urns'] and not all(('urn',x) in observed for x in state['selected_urns']):save('identity_mismatch','A selected full URN is not in the completed research result.');return _public(state)
        records=[];more=False
        if state['selected_ids']:
            for identifier in state['selected_ids']:
                try:records.append(_data(client.prospects.get(identifier,profile_id=profile_id)).get('record'))
                except LeadAdapterError as error:
                    if error.code=='not_found':save('pending_ingestion','An exact selected prospect is not available yet; resume after ingestion.');return _public(state)
                    raise
        else:
            for page in range(1,max_pages+1):
                data=_data(client.prospects.list(kind='person',page=page,profile_id=profile_id));items=data.get('items')
                if not isinstance(items,list):raise LeadAdapterError('invalid_prospect_response')
                records.extend(items);more=data.get('has_more') is True
                if not more:break
        matched=[]
        for record in records:
            if not isinstance(record,dict) or record.get('kind')!='person' or not isinstance(record.get('id'),str):continue
            identity=_identities(record.get('data'))
            if not identity.intersection(observed):continue
            if state['selected_urns'] and not identity.intersection({('urn',x) for x in state['selected_urns']}):continue
            matched.append(record)
        state['candidates']=[{'prospect_id':r['id'],'identities':[list(x) for x in sorted(_identities(r.get('data')).intersection(observed))]} for r in matched]
        if not state['selected_ids'] and not state['selected_urns']:
            save('awaiting_selection' if matched else 'pending_ingestion','Select exact prospect IDs or full URNs after reviewing the completed research. No record is selected by name.');return _public(state)
        if (state['selected_ids'] and set(state['selected_ids'])!={r['id'] for r in matched}) or not matched:
            save('pending_ingestion','The selected prospect has not been ingested with a matching research identity.');return _public(state)
        if state['selected_urns']:
            for urn in state['selected_urns']:
                matches=[r for r in matched if ('urn',urn) in _identities(r.get('data'))]
                if len(matches)!=1:save('pending_ingestion' if not matches else 'identity_ambiguous','Each selected full URN must identify exactly one stored prospect.');return _public(state)
        if not approve_promote and any(not r.get('lead_id') for r in matched):save('awaiting_promotion_approval','Review the exact candidates and approve promotion explicitly.');return _public(state)
        for record in matched:
            item=next((x for x in state['records'] if x['prospect_id']==record['id']),None)
            if item is None:
                item={'prospect_id':record['id'],'promotion_key':str(uuid.uuid4()),'sync_key':str(uuid.uuid4())};state['records'].append(item)
            if not item.get('lead_id'):
                if record.get('lead_id'):item.update(lead_id=record['lead_id'],promote_state='existing');save('native_crm')
                else:
                    # Re-read and verify exact identity immediately before an approved mutation.
                    fresh=_data(client.prospects.get(record['id'],profile_id=profile_id)).get('record')
                    if not isinstance(fresh,dict) or fresh.get('id')!=record['id'] or fresh.get('kind')!='person' or not _identities(fresh.get('data')).intersection(observed) or (state['selected_urns'] and not _identities(fresh.get('data')).intersection({('urn',x) for x in state['selected_urns']})):save('identity_mismatch','Prospect identity changed before promotion.');return _public(state)
                    item['promote_state']='pending';save('promoting')
                    try:
                        promoted=_data(client.prospects.promote(record['id'],profile_id=profile_id,idempotency_key=item['promotion_key'],approved=True)).get('record')
                        if not isinstance(promoted,dict) or promoted.get('id')!=record['id'] or not promoted.get('lead_id') or not _identities(promoted.get('data')).intersection(observed) or (state['selected_urns'] and not _identities(promoted.get('data')).intersection({('urn',x) for x in state['selected_urns']})):raise LeadAdapterError('invalid_promotion_receipt')
                        item.update(lead_id=promoted['lead_id'],promote_state='done');save('native_crm')
                    except Exception:
                        item['promote_state']='uncertain';save('reconciliation_required','Promotion outcome requires reconciliation; this workflow will not repeat the write.');raise
            if provider and item.get('sync_state')!='done':
                if not approve_crm:save('awaiting_external_crm_approval','Native CRM lead is ready; external sync requires separate explicit approval.');return _public(state)
                item['sync_state']='pending';save('syncing')
                try:
                    synced=_data(client.crm.sync_lead(item['lead_id'],provider=provider,idempotency_key=item['sync_key'],approved=True,profile_id=profile_id))
                    if synced.get('lead_id')!=item['lead_id'] or synced.get('provider')!=provider or synced.get('outcome') not in ('created','updated','already_exists','skipped'):raise LeadAdapterError('invalid_sync_receipt')
                    item.update(sync_state='done',external_id=synced.get('external_id'));save('external_crm')
                except Exception:
                    item['sync_state']='uncertain';save('reconciliation_required','External CRM outcome requires reconciliation; this workflow will not repeat the write.');raise
        save('complete');return _public(state)

def fixture_transport():
    """Source-shaped synthetic backend; exercises the actual request adapter without provider calls."""
    from urllib.parse import urlsplit,parse_qs
    receipts=copy.deepcopy(CONTRACT['receipts'])
    def transport(url,method,headers,body,timeout):
        path=urlsplit(url).path;query=parse_qs(urlsplit(url).query)
        if method=='POST' and path=='/api/v1/linkedin/searches/people':receipt=receipts['queued']
        elif method=='GET' and path=='/api/v1/jobs/fixture-job-1':receipt=receipts['completed']
        elif method=='GET' and path=='/api/v1/prospects':receipt=receipts['prospect'] if query.get('id') else receipts['prospects']
        elif method=='POST' and path=='/api/v1/prospects/fixture-prospect-1/promotions':receipt=receipts['promoted']
        elif method=='POST' and path=='/api/v1/leads/fixture-lead-1/crm-syncs':
            receipt=copy.deepcopy(receipts['synced']);receipt['data']['provider']=json.loads(body)['provider']
        else:raise AssertionError('Unexpected synthetic backend request')
        return 200,{'Content-Type':'application/json'},json.dumps(receipt).encode()
    return transport
