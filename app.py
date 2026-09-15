from flask import Flask,render_template,jsonify,request
import yfinance as yf,feedparser,json,os
from urllib.parse import quote_plus
from datetime import datetime

app=Flask(__name__)
FILE="portfolio.json"
DEFAULT=[
{"name":"AeroVironment","isin":"US0080731088","ticker":"AVAV","theme":"Defense / Drones"},
{"name":"BlackSky","isin":"US09263B2079","ticker":"BKSY","theme":"Space"},
{"name":"Newmont","isin":"US6516391066","ticker":"NEM","theme":"Gold"},
{"name":"Kratos Defense","isin":"US50077B2079","ticker":"KTOS","theme":"Defense"},
{"name":"IREN","isin":"AU0000185993","ticker":"IREN","theme":"AI / Data Centers"},
{"name":"Celsius Holdings","isin":"US15118V2079","ticker":"CELH","theme":"Consumer"},
{"name":"Redwire","isin":"US75776W1036","ticker":"RDW","theme":"Space"},
{"name":"Denison Mines","isin":"CA2483561072","ticker":"DNN","theme":"Uranium"},
{"name":"AbCellera","isin":"CA00288U1066","ticker":"ABCL","theme":"Biotech / AI"},
{"name":"Diginex","isin":"KYG286871127","ticker":"DGNX","theme":"RegTech / ESG"}]
MARKETS={"S&P 500":"^GSPC","DAX":"^GDAXI","ATX":"^ATX","Gold":"GC=F","Bitcoin":"BTC-USD","VIX":"^VIX"}

def loadp():
    if not os.path.exists(FILE):savep(DEFAULT)
    try:
        with open(FILE,encoding="utf-8") as f:return json.load(f)
    except:return DEFAULT
def savep(x):
    with open(FILE,"w",encoding="utf-8") as f:json.dump(x,f,ensure_ascii=False,indent=2)
def q(t):
    try:
        h=yf.Ticker(t).history(period="1y",auto_adjust=True)
        c=h["Close"].dropna()
        if c.empty:return {}
        last=float(c.iloc[-1]); d1=(last/c.iloc[-2]-1)*100 if len(c)>1 else None
        m1=(last/c.iloc[-22]-1)*100 if len(c)>22 else None
        yc=c[c.index.year==datetime.now().year]; ytd=(last/yc.iloc[0]-1)*100 if len(yc) else None
        spark=[round(float(v),2) for v in c.tail(18)]
        return {"price":last,"d1":d1,"m1":m1,"ytd":ytd,"spark":spark}
    except:return {}
def rss(query,n=10):
    try:
        f=feedparser.parse(f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en")
        return [{"title":e.get("title",""),"link":e.get("link",""),"published":e.get("published","")} for e in f.entries[:n]]
    except:return []

@app.route("/")
def home():return render_template("index.html")
@app.route("/api/markets")
def markets():return jsonify([{"name":n,**q(t)} for n,t in MARKETS.items()])
@app.route("/api/portfolio")
def portfolio():
    out=[]
    for x in loadp():
        z=q(x["ticker"]);s=5
        if z.get("m1") is not None:s+=1 if z["m1"]>10 else -1 if z["m1"]<-10 else 0
        if z.get("ytd") is not None:s+=1 if z["ytd"]>25 else -1 if z["ytd"]<-25 else 0
        s=max(1,min(10,s));sig="Buy" if s>=8 else "Hold" if s>=6 else "Watch" if s>=4 else "Reduce"
        out.append({**x,**z,"score":s,"signal":sig})
    return jsonify(out)
@app.route("/api/news")
def news():
    c=request.args.get("category","markets")
    qs={"markets":"stock market Federal Reserve earnings","economy":"economy inflation rates growth","companies":"corporate earnings stocks","centralbanks":"Federal Reserve ECB central banks","geopolitics":"geopolitics trade tariffs markets","commodities":"oil gold commodities"}
    return jsonify(rss(qs.get(c,qs["markets"]),12))
@app.route("/api/kobeissi")
def kobeissi():return jsonify(rss('"The Kobeissi Letter" OR @KobeissiLetter markets Fed bonds stocks',12))
@app.route("/api/security",methods=["POST"])
def add():
    x=request.get_json(force=True);p=loadp()
    if not x.get("name") or not x.get("ticker"):return jsonify({"error":"required"}),400
    p.append({"name":x["name"],"isin":x.get("isin",""),"ticker":x["ticker"].upper(),"theme":x.get("theme","Other")});savep(p);return jsonify({"ok":1})
@app.route("/api/security/<ticker>",methods=["DELETE"])
def delete(ticker):
    savep([x for x in loadp() if x["ticker"].upper()!=ticker.upper()]);return jsonify({"ok":1})
@app.route("/health")
def health():return "ok"
