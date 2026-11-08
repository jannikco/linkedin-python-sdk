"""Selected request and envelope types from the public contract. Provider data stays open-ended."""
from typing import Any, Dict, List, Optional, TypedDict

class ApiError(TypedDict):
    code: str
    message: str

class Envelope(TypedDict, total=False):
    ok: bool
    data: Dict[str, Any]
    error: ApiError
    governance: Optional[Dict[str, Any]]
    action_id: Optional[str]
    request_id: str
    status: str
    job_id: str
    eta_seconds: int

class PeopleSearchRequired(TypedDict):
    keywords: List[str]
class PeopleSearchRequest(PeopleSearchRequired, total=False):
    limit: int
    page: int
    profile_id: str
    wait: bool
    dry_run: bool
class ProfileEnrichmentRequest(TypedDict, total=False):
    linkedin_urn: str
    public_id: str
    lead_id: str
    include_email: bool
    profile_id: str
    wait: bool
    dry_run: bool
class PostEngagersRequired(TypedDict):
    post_urn: str
class PostEngagersRequest(PostEngagersRequired, total=False):
    limit: int
    page: int
    profile_id: str
    wait: bool
    dry_run: bool
class JobData(TypedDict, total=False):
    job_id: str
    status: str
    result: Any
    error: Any
    finished: bool
    delivery_state: Optional[str]
class ProspectRecord(TypedDict, total=False):
    id: str
    kind: str
    data: Dict[str, Any]
    lead_id: Optional[str]

def require_data(receipt: Envelope) -> Dict[str, Any]:
    """Return actual API data, never reinterpret queued or malformed receipts as completed results."""
    if receipt.get('ok') is not True or not isinstance(receipt.get('data'),dict): raise ValueError('A successful API data envelope is required')
    return receipt['data']

def job_id(receipt: Envelope) -> Optional[str]:
    data=receipt.get('data')
    value=receipt.get('job_id') or (data.get('job_id') if isinstance(data,dict) else None)
    return value if isinstance(value,str) and value else None
