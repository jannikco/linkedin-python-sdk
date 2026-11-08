"""python -m leadadapter: deliberate agent workflows; no network by default."""
import argparse
import json
import os
import sys
from . import LeadAdapterClient, LeadAdapterError
from .reports import write_report
from .workflows import run_research_to_crm,plan_research_to_crm,fixture_transport

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv[:2]==['agents','install']:
        try:from .agentkit.install import main as install
        except ImportError:raise SystemExit('Agentkit installer is not included in this source build yet')
        return install(argv[2:])
    parser=argparse.ArgumentParser(prog='python -m leadadapter');commands=parser.add_subparsers(dest='command');workflow=commands.add_parser('workflows');workflow.add_argument('name',choices=['research-to-crm']);mode=workflow.add_mutually_exclusive_group();mode.add_argument('--fixture',action='store_true');mode.add_argument('--live',action='store_true');workflow.add_argument('--keywords',action='append');workflow.add_argument('--profile-id');workflow.add_argument('--prospect-id',action='append');workflow.add_argument('--prospect-urn',action='append');workflow.add_argument('--provider');workflow.add_argument('--approve-promote',action='store_true');workflow.add_argument('--approve-crm',action='store_true');workflow.add_argument('--checkpoint');workflow.add_argument('--output');workflow.add_argument('--poll-timeout',type=float,default=60);workflow.add_argument('--poll-interval',type=float,default=1)
    args=parser.parse_args(argv)
    if args.command!='workflows':parser.print_help();return 0
    if not args.live and not args.fixture:print(json.dumps(plan_research_to_crm(),indent=2));return 0
    if args.live and not os.environ.get('LEADADAPTER_API_KEY'):parser.error('--live requires LEADADAPTER_API_KEY in the environment')
    if args.live and not args.checkpoint:parser.error('--live requires --checkpoint for durable idempotency and resume')
    if not args.keywords and not (args.checkpoint and os.path.exists(args.checkpoint)):
        if args.fixture:args.keywords=['synthetic research']
        else:parser.error('Provide --keywords or resume an existing --checkpoint')
    try:
        client=LeadAdapterClient(os.environ['LEADADAPTER_API_KEY']) if args.live else LeadAdapterClient('fixture-not-a-real-key',transport=fixture_transport())
        result=run_research_to_crm(client,keywords=args.keywords,profile_id=args.profile_id,prospect_ids=args.prospect_id,prospect_urns=args.prospect_urn,provider=args.provider,approve_promote=args.approve_promote,approve_crm=args.approve_crm,checkpoint=args.checkpoint,mode='live' if args.live else 'fixture',poll_timeout=args.poll_timeout,poll_interval=args.poll_interval)
        if args.output:result['exports']=write_report(result,args.output)
        print(json.dumps(result,indent=2));return 0
    except LeadAdapterError as error:
        print(json.dumps({'ok':False,'code':error.code,'status':error.status,'request_id':error.request_id}),file=sys.stderr);return 1
    except (ValueError,OSError) as error:
        print(json.dumps({'ok':False,'code':'workflow_input_error','message':str(error)}),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
