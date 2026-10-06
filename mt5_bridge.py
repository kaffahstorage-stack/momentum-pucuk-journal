"""Read-only MT5 journal bridge. Windows + Python 3.11/3.12 64-bit."""
import json, os, secrets, sqlite3, threading, time, hmac, argparse
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('LOCALAPPDATA',str(ROOT)))/'MomentumPucukJournal'
DATA.mkdir(parents=True,exist_ok=True)
TOKEN_FILE=DATA/'pairing-key.txt'
if not TOKEN_FILE.exists(): TOKEN_FILE.write_text(secrets.token_urlsafe(32))
TOKEN=TOKEN_FILE.read_text().strip()
ORIGINS={'https://kaffahstorage-stack.github.io','http://127.0.0.1:8766','http://localhost:8766'}
LOCK=threading.Lock()
STATE={'connected':False,'message':'Menunggu MT5','last_sync':None,'account':None}

def connection():
    c=sqlite3.connect(DATA/'journal.sqlite',timeout=30)
    c.execute('CREATE TABLE IF NOT EXISTS snapshots (account TEXT PRIMARY KEY, data TEXT NOT NULL)')
    return c

def summarize(deals,positions):
    active={int(p.get('identifier',p['ticket'])) for p in positions}
    groups={}
    for d in deals:
        if d.get('position_id',0) and d.get('type') in (0,1): groups.setdefault(int(d['position_id']),[]).append(d)
    result=[]
    for pid,ds in groups.items():
        ds.sort(key=lambda d:(d.get('time_msc',d['time']*1000),d['ticket']))
        ins=[d for d in ds if d['entry']==0];outs=[d for d in ds if d['entry'] in (1,3)]
        reversed_trade=any(d['entry']==2 for d in ds)
        if not ins: continue
        iv=sum(d['volume'] for d in ins);ov=sum(d['volume'] for d in outs)
        entry=sum(d['price']*d['volume'] for d in ins)/iv
        exitprice=sum(d['price']*d['volume'] for d in outs)/ov if ov else None
        net=sum(d.get('profit',0)+d.get('commission',0)+d.get('swap',0)+d.get('fee',0) for d in ds)
        closed=pid not in active and ov>=iv-1e-8 and not reversed_trade
        status='REVIEW' if reversed_trade or (pid not in active and not closed) else 'CLOSED' if closed else 'OPEN'
        reason={4:'SL broker',5:'TP broker',6:'Stop out'}.get(outs[-1].get('reason'),'Close manual / lainnya') if outs else 'Posisi aktif'
        first=ins[0];side='BUY' if first['type']==0 else 'SELL'
        result.append({'id':str(pid),'symbol':first['symbol'],'side':side,'entry':entry,'exit':exitprice,'volume':iv,'net':net,'status':status,'reason':reason,'time':first['time'],'closed_time':outs[-1]['time'] if closed else None,'magic':first.get('magic',0),'comment':first.get('comment',''),'deals':len(ds)})
    return sorted(result,key=lambda t:t['time'],reverse=True)

def worker(args):
    import MetaTrader5 as mt5
    while True:
        try:
            kwargs={'path':args.terminal} if args.terminal else {}
            if not mt5.initialize(**kwargs): raise RuntimeError('MT5 belum tersambung. Buka terminal dan login, lalu tunggu sinkronisasi.')
            info=mt5.account_info();terminal=mt5.terminal_info()
            if info is None or terminal is None or not terminal.connected: raise RuntimeError('Terminal MT5 sedang offline.')
            key=str(info.login)+'@'+info.server
            positions=mt5.positions_get()
            history=mt5.history_deals_get(datetime(2000,1,1,tzinfo=timezone.utc),datetime.now(timezone.utc))
            if positions is None or history is None: raise RuntimeError('Riwayat/posisi belum berhasil dibaca dari MT5.')
            ps=[p._asdict() for p in positions];ds=[d._asdict() for d in history]
            snapshot={'trades':summarize(ds,ps),'positions':ps,'currency':info.currency,'balance':info.balance,'equity':info.equity,'last_sync':time.time(),'account_label':str(info.login)[-4:]+' · '+info.server}
            with connection() as c:c.execute('INSERT INTO snapshots(account,data) VALUES (?,?) ON CONFLICT(account) DO UPDATE SET data=excluded.data',(key,json.dumps(snapshot)))
            with LOCK:STATE.update(connected=True,message='MT5 terhubung',last_sync=snapshot['last_sync'],account=key)
        except Exception as e:
            with LOCK:STATE.update(connected=False,message=str(e))
        time.sleep(5)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def headers_for_origin(self):
        origin=self.headers.get('Origin')
        if origin in ORIGINS:
            self.send_header('Access-Control-Allow-Origin',origin)
            self.send_header('Vary','Origin')
        self.send_header('Access-Control-Allow-Methods','GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','X-Journal-Key')
        self.send_header('Access-Control-Allow-Private-Network','true')
        self.send_header('Cache-Control','no-store')
    def do_OPTIONS(self):
        if self.headers.get('Origin') not in ORIGINS:self.send_error(403);return
        self.send_response(204);self.headers_for_origin();self.end_headers()
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:8766','localhost:8766'):self.send_error(403);return
        path=urlparse(self.path).path
        if path in ('/','/index.html'):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write((ROOT/'index.html').read_bytes());return
        if path!='/api/journal':self.send_error(404);return
        origin=self.headers.get('Origin')
        if origin and origin not in ORIGINS:self.send_error(403);return
        if not hmac.compare_digest(self.headers.get('X-Journal-Key',''),TOKEN):
            self.send_response(401);self.headers_for_origin();self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"error":"Kode penghubung tidak cocok."}');return
        with LOCK: state=dict(STATE)
        snapshot=None
        with connection() as c:
            if state['account']:
                row=c.execute('SELECT data FROM snapshots WHERE account=?',(state['account'],)).fetchone()
                if row:snapshot=json.loads(row[0])
        self.send_response(200);self.headers_for_origin();self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps({'connection':{k:v for k,v in state.items() if k!='account'},'snapshot':snapshot}).encode())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--terminal',help='Path terminal64.exe jika ada lebih dari satu MT5');args=parser.parse_args()
    try:import MetaTrader5
    except ImportError:raise SystemExit('Pasang paket dulu: py -3 -m pip install -r requirements.txt')
    print('Momentum Pucuk — penghubung baca-saja MT5\nKode penghubung (masukkan pada website):\n'+TOKEN+'\n\nBuka: http://127.0.0.1:8766\nBiarkan jendela ini tetap terbuka. Ctrl+C untuk berhenti.')
    threading.Thread(target=worker,args=(args,),daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
