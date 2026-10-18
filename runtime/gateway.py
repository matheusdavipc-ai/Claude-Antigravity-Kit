"""Ephemeral loopback filter. Calls only explicit OpenRouter free variants."""
import http.client
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from context_config import response_budget
from core import KIT, ROLES, MODELS, get_catalog, safe_candidate, MODEL_NAMES, PRIMARY_ROLES

class Gateway(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, upstream_token, catalog=None, upstream='https://openrouter.ai', testing=False):
        super().__init__(('127.0.0.1', 0), Handler)
        self.token = secrets.token_urlsafe(32)
        self.upstream_token = upstream_token
        self.upstream = urlsplit(upstream)
        if not testing and (self.upstream.hostname != 'openrouter.ai' or self.upstream.scheme != 'https'):
            raise ValueError('Upstream deve ser o OpenRouter oficial.')
        self.catalog = catalog if catalog is not None else get_catalog()
        self.catalog_time = time.monotonic()
        self.context_ceiling = {model: item.get('context') for model, item in self.catalog.items()}
        self.active = 0
        self.lock = threading.Lock()
        self.events = []

    def fresh_catalog(self):
        if time.monotonic() - self.catalog_time > 300:
            self.catalog = get_catalog()  # Fail closed if refresh fails.
            self.catalog_time = time.monotonic()
        return self.catalog

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    def log_message(self, *args):
        pass

    def authenticated(self):
        provided = self.headers.get('Authorization','').removeprefix('Bearer ')
        return secrets.compare_digest(provided, self.server.token)

    def send_json(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.authenticated():
            return self.send_json(401, {'error':{'type':'authentication_error','message':'Local gateway authentication required'}})
        if self.path.split('?')[0] in ('/v1/models','/api/v1/models'):
            return self.send_json(200, {'data':[{'id':model,'type':'model','display_name':name,'created_at':'2026-10-18T00:00:00Z'} for model,name in MODEL_NAMES.items()], 'has_more':False})
        return self.send_json(404, {'error':{'message':'Unsupported local endpoint'}})

    def do_POST(self):
        if not self.authenticated():
            # Drain a small body before closing so Windows does not reset the 401 response.
            try:
                length = int(self.headers.get('Content-Length','0'))
                if 0 < length <= 4096:
                    self.connection.settimeout(.5)
                    self.rfile.read(length)
            except (ValueError,OSError):
                pass
            finally:
                self.connection.settimeout(180)
            return self.send_json(401, {'error':{'type':'authentication_error','message':'Local gateway authentication required'}})
        path = self.path.split('?')[0]
        if path not in ('/v1/messages','/v1/messages/count_tokens'):
            return self.send_json(403, {'error':{'type':'permission_error','message':'Endpoint blocked by free-model filter'}})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 32*1024*1024:
                return self.send_json(413, {'error':{'message':'Invalid request size'}})
            body = json.loads(self.rfile.read(length))
            requested = body.get('model','').removesuffix('[1m]')
            role = PRIMARY_ROLES.get(requested, requested)
            if role in ROLES:
                candidates = ROLES[role]
            elif role in MODELS:
                # Explicit model requests do not acquire an unrelated role's reserve.
                candidates = (role,)
            else:
                return self.send_json(403, {'error':{'type':'permission_error','message':'Model outside the mandatory free team'}})
            visual = role == 'router-visual' or contains_image(body)
            catalog = self.server.fresh_catalog()
            candidates = [m for m in candidates if safe_candidate(m, catalog, visual)]
            if not candidates:
                return self.send_json(503, {'error':{'type':'api_error','message':'No verified free compatible model for this role'}})
            if any(isinstance(self.server.context_ceiling.get(model), int) and catalog[model].get('context', 0) < self.server.context_ceiling[model] for model in candidates):
                return self.send_json(409, {'error':{'type':'invalid_request_error','message':'Provider context limit decreased; restart clauderouter to recalculate safe compaction before continuing'}})
            if path == '/v1/messages':
                budget = response_budget(role, candidates, catalog)
                requested_output = body.get('max_tokens', budget)
                if not isinstance(requested_output, int) or isinstance(requested_output, bool) or requested_output <= 0:
                    return self.send_json(400, {'error':{'type':'invalid_request_error','message':'max_tokens must be a positive integer'}})
                body['max_tokens'] = min(requested_output, budget)
            # No advanced Anthropic-only reasoning/effort parameters on arbitrary models.
            body.pop('thinking',None)
            body.pop('output_config',None)
            body.pop('speed',None)
            body.pop('service_tier',None)
            # Remove upstream routing overrides supplied by caller.
            body.pop('models',None)
            body.pop('route',None)
            body.pop('provider',None)
            body.pop('plugins',None)
            body.pop('web_search_options',None)
            # Hosted search tools can incur separate charges; keep ordinary function tools.
            if 'tools' in body:
                body['tools'] = [tool for tool in body['tools'] if tool.get('type','custom') == 'custom']
            with self.server.lock:
                self.server.active += 1
            try:
                for index, model in enumerate(candidates):
                    body['model'] = model
                    payload = json.dumps(body).encode()
                    cls = http.client.HTTPSConnection if self.server.upstream.scheme == 'https' else http.client.HTTPConnection
                    connection = cls(self.server.upstream.hostname, self.server.upstream.port, timeout=180)
                    headers = {'Content-Type':'application/json','Authorization':'Bearer '+self.server.upstream_token,
                               'anthropic-version':self.headers.get('anthropic-version','2023-06-01')}
                    # Preserve authentic harness attribution; never fabricate a different app.
                    for key in ('User-Agent','X-App','X-Title','HTTP-Referer','X-OpenRouter-Title','X-Stainless-Lang','X-Stainless-Package-Version'):
                        if self.headers.get(key):
                            headers[key] = self.headers[key]
                    try:
                        connection.request('POST','/api'+path,payload,headers)
                        response = connection.getresponse()
                    except (OSError, http.client.HTTPException):
                        connection.close()
                        # Transport outcome uncertain: never replay to another model.
                        return self.send_json(502, {'error':{'type':'api_error','message':'Upstream transport failure; no automatic replay'}})
                    restricted_model = False
                    buffered = None
                    if response.status == 403:
                        buffered = response.read()
                        # A model-specific harness eligibility refusal is unavailability,
                        # not invalid credentials. Other 403s never trigger reserve.
                        restricted_model = b'only available on agentic harnesses' in buffered and model.encode() in buffered
                    if (response.status in (404,408,429,500,502,503,529) or restricted_model) and index + 1 < len(candidates):
                        if buffered is None:
                            response.read()
                        connection.close()
                        self.record(role,model,'reserve-next',response.status)
                        print('[clauderouter] '+role+': principal indisponivel (HTTP '+str(response.status)+'); reserva '+candidates[index+1],flush=True)
                        continue
                    self.record(role,model,'response',response.status)
                    self.send_response(response.status)
                    for key in ('Content-Type','Retry-After'):
                        if response.getheader(key):
                            self.send_header(key,response.getheader(key))
                    self.send_header('X-Claude-Perfis-Model',model)
                    self.send_header('Connection','close')
                    self.end_headers()
                    try:
                        if buffered is not None:
                            self.wfile.write(buffered)
                        else:
                            while data := response.read1(65536):
                                self.wfile.write(data)
                                self.wfile.flush()
                    finally:
                        connection.close()
                    return
            finally:
                with self.server.lock:
                    self.server.active -= 1
        except (ValueError, KeyError, OSError):
            # Never send exception details, prompt bodies or credentials to logs/client.
            if not self.wfile.closed:
                try:
                    self.send_json(503, {'error':{'type':'api_error','message':'Local verification failed; request blocked'}})
                except OSError:
                    pass

    def record(self, role, model, outcome, status):
        event = {'time':time.time(),'role':role,'model':model,'outcome':outcome,'status':status}
        with self.server.lock:
            self.server.events.append(event)

def contains_image(value):
    if isinstance(value,dict):
        return value.get('type') in ('image','image_url') or any(contains_image(v) for v in value.values())
    if isinstance(value,list):
        return any(contains_image(v) for v in value)
    return False
