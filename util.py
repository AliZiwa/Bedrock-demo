import boto3
import textwrap

region_name = 'us-east-1' # make sure this is the same region as the region where you created your agent

def invoke_agent(agentId: str, agentAliasId: str, inputText: str, sessionId: str, enableTrace: bool = False,
                           endSession: bool = False, width: int = 70):
    bedrock_agent_runtime = boto3.client(service_name='bedrock-agent-runtime', region_name=region_name)

    response = bedrock_agent_runtime.invoke_agent(
        agentId=agentId,
        agentAliasId=agentAliasId,
        sessionId=sessionId,
        inputText=inputText,
        endSession=endSession,
        enableTrace=enableTrace
    )

    event_stream = response["completion"]
    agent_response = ""

    print(f"User: {textwrap.fill(inputText, width=width)}\n")
    # print("Agent:", end=" ", flush=True)

    for event in event_stream:
        # print(f"event: {event}")
        if 'chunk' in event:
            chunk_text = event['chunk'].get('bytes', b'').decode('utf-8')
            if not enableTrace:  # Only print chunks if trace is not enabled
                print(textwrap.fill(chunk_text, width=width, subsequent_indent='       '), end='', flush=True)
            agent_response += chunk_text
        elif 'trace' in event and enableTrace:
            trace = event['trace']

            if 'trace' in trace:
                trace_details = trace['trace']

                if 'orchestrationTrace' in trace_details:
                    orch_trace = trace_details['orchestrationTrace']

                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        print("\nInvocation Input:")
                        print(f"  Type: {inv_input.get('invocationType', 'N/A')}")
                        if 'actionGroupInvocationInput' in inv_input:
                            agi = inv_input['actionGroupInvocationInput']
                            print(f"  Action Group: {agi.get('actionGroupName', 'N/A')}")
                            print(f"  Function: {agi.get('function', 'N/A')}")
                            print(f"  Parameters: {agi.get('parameters', 'N/A')}")

                    if 'rationale' in orch_trace:
                        thought = orch_trace['rationale']['text']
                        print(f"\nAgent's thought process:")
                        print(textwrap.fill(thought, width=width, initial_indent='  ', subsequent_indent='  '))

                    if 'observation' in orch_trace:
                        obs = orch_trace['observation']
                        print("\nObservation:")
                        print(f"  Type: {obs.get('type', 'N/A')}")
                        if 'actionGroupInvocationOutput' in obs:
                            print(f"  Action Group Output: {obs['actionGroupInvocationOutput'].get('text', 'N/A')}")
                        if 'knowledgeBaseLookupOutput' in obs:
                            print("  Knowledge Base Lookup:")
                            for ref in obs['knowledgeBaseLookupOutput'].get('retrievedReferences', []):
                                print(f"    - {ref['content'].get('text', 'N/A')[:50]}...")
                        if 'codeInterpreterInvocationOutput' in obs:
                            cio = obs['codeInterpreterInvocationOutput']
                            print("  Code Interpreter Output:")
                            print(f"    Execution Output: {cio.get('executionOutput', 'N/A')[:50]}...")
                            print(f"    Execution Error: {cio.get('executionError', 'N/A')}")
                            print(f"    Execution Timeout: {cio.get('executionTimeout', 'N/A')}")
                        if 'finalResponse' in obs:
                            final_response = obs['finalResponse']['text']
                            print(f"\nFinal response:")
                            print(
                                textwrap.fill(final_response, width=width, initial_indent='  ', subsequent_indent='  '))

                if 'guardrailTrace' in trace_details:
                    guard_trace = trace_details['guardrailTrace']
                    print("\nGuardrail Trace:")
                    print(f"  Action: {guard_trace.get('action', 'N/A')}")

                    for assessment in guard_trace.get('inputAssessments', []) + guard_trace.get('outputAssessments',
                                                                                                []):
                        if 'contentPolicy' in assessment:
                            for filter in assessment['contentPolicy'].get('filters', []):
                                print(
                                    f"  Content Filter: {filter['type']} (Confidence: {filter['confidence']}, Action: {filter['action']})")

                        if 'sensitiveInformationPolicy' in assessment:
                            for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
                                print(f"  PII Detected: {pii['type']} (Action: {pii['action']})")

    print(f"\n\nSession ID: {response.get('sessionId')}")
    return
