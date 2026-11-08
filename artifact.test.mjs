import test from 'node:test';
import {execFileSync} from 'node:child_process';
test('Python SDK mock contracts and dry-run example',()=>{execFileSync('python3',['-m','unittest','test_sdk.py']);execFileSync('python3',['example.py','--dry-run']);});
