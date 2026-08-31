import json, tempfile, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))

from runtime import run_production, EvaluationHarness
from runtime.adapters import DeterministicLLMAdapter, ResilientLLMAdapter, GuardedToolAdapter, OpenAIResponsesAdapter, AnthropicMessagesAdapter
from runtime.adapters.base import LLMRequest, LLMResponse
from runtime.production import RetryPolicy, CircuitBreaker, BudgetPolicy, ProductionPolicy, BudgetExceeded, CircuitOpen, ApprovalGate, ApprovalRequired, ExecutionJournal, HTTPResult, ProviderHTTPError, ProviderResponseError, redact

class FakeTransport:
    def __init__(self, data, status=200): self.data=data; self.status=status; self.calls=[]
    def post(self,url,*,headers,payload,timeout): self.calls.append((url,headers,payload,timeout)); return HTTPResult(self.status,self.data,{})

class FakeTool:
    def __init__(self,capability,effect=None): self.capability=capability; self.effect=effect; self.calls=[]
    def invoke(self,args): self.calls.append(args); return {"ok":True,"args":args}

class ToolRequestLLM(DeterministicLLMAdapter):
    def complete(self,request):
        r=super().complete(request)
        if request.purpose=='command_execution': r.content['tool_requests']=[{"capability":"github.write","arguments":{"path":"x"}}]
        return r

class Flaky:
    name='flaky'; thread_safe=True
    def __init__(self,n): self.n=n; self.calls=0
    def complete(self,request):
        self.calls+=1
        if self.calls<=self.n: raise TimeoutError('retry me')
        return LLMResponse(content={"summary":"ok","outputs":{},"epistemic":{"facts":[],"inferences":[],"assumptions":[],"unknowns":[]},"confidence":{"level":"high","reason":"ok"}},usage={"input_tokens":3,"output_tokens":2})

class Alpha5Tests(unittest.TestCase):
    def req(self): return LLMRequest(purpose='test',system='s',user='u')

    def test_retry_succeeds(self):
        inner=Flaky(2); p=ProductionPolicy(retry=RetryPolicy(max_attempts=3,base_delay_s=0,jitter_s=0))
        r=ResilientLLMAdapter(inner,policy=p,sleeper=lambda _:None).complete(self.req())
        self.assertEqual(inner.calls,3); self.assertEqual(r.content['summary'],'ok')

    def test_retry_stops(self):
        inner=Flaky(3); p=ProductionPolicy(retry=RetryPolicy(max_attempts=2,base_delay_s=0,jitter_s=0))
        with self.assertRaises(TimeoutError): ResilientLLMAdapter(inner,policy=p,sleeper=lambda _:None).complete(self.req())
        self.assertEqual(inner.calls,2)

    def test_non_retryable_http(self):
        class Bad: name='bad'; thread_safe=True
        bad=Bad(); bad.calls=0
        def complete(req): bad.calls+=1; raise ProviderHTTPError(400,'bad')
        bad.complete=complete
        with self.assertRaises(ProviderHTTPError): ResilientLLMAdapter(bad,policy=ProductionPolicy(retry=RetryPolicy(max_attempts=3,base_delay_s=0)),sleeper=lambda _:None).complete(self.req())
        self.assertEqual(bad.calls,1)

    def test_budget_requests(self):
        a=ResilientLLMAdapter(DeterministicLLMAdapter(),policy=ProductionPolicy(budget=BudgetPolicy(max_requests=1)))
        a.complete(self.req())
        with self.assertRaises(BudgetExceeded): a.complete(self.req())

    def test_budget_tokens(self):
        a=ResilientLLMAdapter(Flaky(0),policy=ProductionPolicy(budget=BudgetPolicy(max_total_tokens=4)))
        with self.assertRaises(BudgetExceeded): a.complete(self.req())

    def test_circuit_opens_and_recovers(self):
        class Clock:
            t=0
            def __call__(self): return self.t
        clock=Clock(); cb=CircuitBreaker(failure_threshold=2,recovery_timeout_s=10,clock=clock)
        cb.record_failure(); cb.record_failure()
        with self.assertRaises(CircuitOpen): cb.before_call()
        clock.t=11; cb.before_call(); self.assertEqual(cb.state,'HALF_OPEN'); cb.record_success(); self.assertEqual(cb.state,'CLOSED')

    def test_approval_read_allowed(self): ApprovalGate().require('read',{})
    def test_approval_write_blocked(self):
        with self.assertRaises(ApprovalRequired): ApprovalGate().require('write',{})
    def test_approval_write_allowed(self): ApprovalGate(approver=lambda effect,ctx:True).require('write',{})

    def test_guarded_tool_read(self):
        t=FakeTool('web.search','read'); self.assertTrue(GuardedToolAdapter(t).invoke({'q':'x'})['ok'])
    def test_guarded_tool_write_blocked(self):
        t=FakeTool('github.write','write')
        with self.assertRaises(ApprovalRequired): GuardedToolAdapter(t).invoke({'x':1})
    def test_guarded_tool_write_approved(self):
        t=FakeTool('github.write','write'); g=GuardedToolAdapter(t,approval_gate=ApprovalGate(approver=lambda e,c:True)); self.assertTrue(g.invoke({})['ok'])

    def test_redaction(self):
        x=redact({'api_key':'abc','nested':{'Authorization':'Bearer supersecret'},'ok':'yes'})
        self.assertEqual(x['api_key'],'***REDACTED***'); self.assertNotIn('supersecret',json.dumps(x)); self.assertEqual(x['ok'],'yes')

    def test_journal_redacts(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'j.jsonl'; ExecutionJournal(p).append({'token':'secret','message':'Bearer xyz'})
            raw=p.read_text(); self.assertNotIn('secret',raw); self.assertNotIn('xyz',raw)

    def test_openai_payload_and_parse(self):
        tr=FakeTransport({'model':'m','output_text':json.dumps({'summary':'ok','outputs':{},'epistemic':{},'confidence':{}}),'usage':{'input_tokens':4}})
        a=OpenAIResponsesAdapter('m',api_key='k',transport=tr); r=a.complete(self.req())
        self.assertEqual(r.content['summary'],'ok'); self.assertFalse(tr.calls[0][2]['store']); self.assertIn('Bearer k',tr.calls[0][1]['Authorization'])

    def test_openai_nested_output_parse(self):
        tr=FakeTransport({'output':[{'content':[{'type':'output_text','text':'{\"summary\":\"ok\"}'}]}]})
        self.assertEqual(OpenAIResponsesAdapter('m',api_key='k',transport=tr).complete(self.req()).content['summary'],'ok')

    def test_openai_invalid_json(self):
        tr=FakeTransport({'output_text':'not json'})
        with self.assertRaises(ProviderResponseError): OpenAIResponsesAdapter('m',api_key='k',transport=tr).complete(self.req())

    def test_anthropic_payload_and_parse(self):
        tr=FakeTransport({'model':'c','content':[{'type':'text','text':'{\"summary\":\"ok\"}'}],'usage':{'input_tokens':2}})
        a=AnthropicMessagesAdapter('c',api_key='k',transport=tr); r=a.complete(self.req())
        self.assertEqual(r.content['summary'],'ok'); self.assertEqual(tr.calls[0][1]['x-api-key'],'k')

    def test_anthropic_invalid_json(self):
        tr=FakeTransport({'content':[{'type':'text','text':'oops'}]})
        with self.assertRaises(ProviderResponseError): AnthropicMessagesAdapter('c',api_key='k',transport=tr).complete(self.req())

    def test_production_tool_request_blocked_without_approval(self):
        tool=FakeTool('github.write','write'); r=run_production('/build cible',ToolRequestLLM(),tool_adapters={'github.write':tool})
        build=next(x for x in r['execution']['steps'] if x.get('command')=='build')
        self.assertEqual(build['status'],'PARTIALLY_EXECUTED'); self.assertEqual(build['tool_results'][0]['status'],'BLOCKED')

    def test_production_tool_request_executes_with_approval(self):
        tool=FakeTool('github.write','write'); r=run_production('/build cible',ToolRequestLLM(),tool_adapters={'github.write':tool},approval_gate=ApprovalGate(approver=lambda e,c:True))
        build=next(x for x in r['execution']['steps'] if x.get('command')=='build')
        self.assertEqual(build['tool_results'][0]['status'],'EXECUTED'); self.assertEqual(len(tool.calls),1)

    def test_production_budget_exposed(self):
        r=run_production('/audit cible',DeterministicLLMAdapter()); self.assertIsInstance(r['execution']['budget'],dict)

    def test_eval_corpus_all_passes(self):
        report=EvaluationHarness.from_json(ROOT/'tests/evals/corpus.json').run(); self.assertEqual(report['failed'],0)

def _make_retry_matrix(failures,attempts):
    def test(self):
        inner=Flaky(failures); p=ProductionPolicy(retry=RetryPolicy(max_attempts=attempts,base_delay_s=0,jitter_s=0)); a=ResilientLLMAdapter(inner,policy=p,sleeper=lambda _:None)
        if failures < attempts:
            a.complete(self.req()); self.assertEqual(inner.calls,failures+1)
        else:
            with self.assertRaises(TimeoutError): a.complete(self.req())
            self.assertEqual(inner.calls,attempts)
    return test
for failures in range(0,5):
    for attempts in range(1,6): setattr(Alpha5Tests,f'test_retry_matrix_{failures}_{attempts}',_make_retry_matrix(failures,attempts))

if __name__=='__main__': unittest.main()
