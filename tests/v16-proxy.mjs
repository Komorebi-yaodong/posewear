// v16：/api/proxy 端口与协议策略单元测试（node 直跑，不经浏览器）
// node tests/v16-proxy.mjs
import { onRequest } from '../functions/api/proxy.js';
let pass = 0, fail = 0;
const ok = (n, c, d) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (d ? ' :: ' + d : '')); c ? pass++ : fail++; };
const SELF = 'https://posewear.pages.dev';
async function call(target, headers = {}, withOrigin = true) {
  const h = new Headers(headers);
  if (withOrigin) h.set('origin', SELF);
  if (target) h.set('x-target-url', target);
  const req = new Request(SELF + '/api/proxy', { method: 'POST', headers: h, body: '{}' });
  const r = await onRequest({ request: req, env: {POSEWEAR_PROXY_ORIGINS:'https://example.com:8443'} });
  const t = await r.text().catch(() => '');
  return { status: r.status, body: t.slice(0, 120) };
}
let forwarded;
globalThis.fetch = async (url, init) => { forwarded = init.headers; return new Response('{}') };
let r = await call('https://example.com:8443/v1/images/generations', { 'x-proxy-custom': '1', 'cookie':'test-cookie', 'authorization':'Bearer test-only', 'x-unrelated':'test' });
ok('custom https 非443 端口放行', r.status === 200, r.status + ' ' + r.body);
ok('只转发上游必需的请求头', forwarded.get('authorization') === 'Bearer test-only' && !forwarded.has('cookie') && !forwarded.has('x-unrelated'));
r = await call('https://other.example/v1/models', { 'x-proxy-custom':'1' });
ok('未登记中转提示改用直连', r.status === 403 && r.body.includes('直连'));
r = await call('http://example.com:8080/v1/images/edits', { 'x-proxy-custom': '1' });
ok('custom http 拒绝明文', r.status === 400, r.status + ' ' + r.body);
r = await call('https://api.openai.com:8443/v1/images/generations', {});
ok('官方域名带端口仍拒绝', r.status === 400, r.status + ' ' + r.body);
r = await call('https://192.168.1.5:8188/v1/images/generations', { 'x-proxy-custom': '1' });
ok('自定义内网地址仍拒绝', r.status === 403, r.status + ' ' + r.body);
r = await call('https://example.com:8443/v1/chat/completions', { 'x-proxy-custom': '1' });
ok('自定义非图片路径仍拒绝', r.status === 403, r.status + ' ' + r.body);
r = await call('https://example.com/v1/images/generations', { 'x-proxy-custom': '1' }, false);
ok('无同源来源仍拒绝', r.status === 403, r.status + ' ' + r.body);
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
