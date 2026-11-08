"""SDK transport and error contract fixtures; no external network."""
import json, unittest
from leadadapter import LeadAdapterClient, LeadAdapterError, operations
class Contract(unittest.TestCase):
    def test_mock_request_and_errors(self):
        selected=next(key for key,op in operations.items() if op['method']=='GET' and not any(p.get('required') for p in op['parameters']))
        for status in (200,202,401,403,422,429):
            def transport(url,method,headers,body,timeout):
                return status, {'Retry-After':'2'}, json.dumps({'ok':status<300,'data':{'status':'pending'},'error':{'code':'fixture_error'}}).encode()
            client=LeadAdapterClient('fixture-token',transport=transport)
            if status<300: self.assertEqual(client.request(selected)['data']['status'],'pending')
            else:
                with self.assertRaises(LeadAdapterError) as caught: client.request(selected)
                self.assertEqual(caught.exception.status,status)
if __name__=='__main__': unittest.main()
