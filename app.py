import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.express as px
from datetime import datetime
from urllib.parse import quote_plus

st.set_page_config(page_title="Investment Cockpit", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root{--navy:#052e5d;--blue:#0878ed;--line:#dfe7f1;--muted:#64748b;--bg:#f4f7fb;}
.stApp{background:var(--bg);}
.block-container{padding:0.9rem 1.2rem 2rem;max-width:1650px;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#042c58,#063b72);border-right:0;}
[data-testid="stSidebar"] *{color:white;}
[data-testid="stSidebar"] input{color:#0f172a!important;}
.hero{background:linear-gradient(90deg,rgba(3,43,84,.98),rgba(7,87,150,.88));border-radius:14px;padding:20px 26px;color:white;margin-bottom:12px;}
.hero h1{font-size:30px;margin:2px 0}.hero p{margin:0;opacity:.85}
.eyebrow{text-transform:uppercase;font-size:11px;letter-spacing:.14em;font-weight:700;opacity:.75}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:0 1px 3px rgba(15,23,42,.04);}
.stTabs [data-baseweb="tab-list"]{background:white;border:1px solid var(--line);border-radius:11px;padding:4px;gap:3px}
.stTabs [data-baseweb="tab"]{border-radius:8px;padding:7px 13px}
.section{font-size:18px;font-weight:750;color:#0a3262;margin:8px 0 10px}
.news-card{background:white;border:1px solid var(--line);border-radius:11px;padding:12px 14px;margin-bottom:8px}
.news-meta{font-size:11px;color:#64748b;margin-bottom:3px}
.news-title{font-size:14px;font-weight:700;color:#0b2f5b}
.badge{display:inline-block;background:#eaf3ff;color:#0869cf;border-radius:6px;padding:2px 7px;font-size:10px;margin-left:5px}
</style>
""",unsafe_allow_html=True)

DEFAULT=[
["AeroVironment","US0080731088","AVAV","Defense / Drones",3274.02],
["BlackSky Technology","US09263B2079","BKSY","Space / Geospatial",None],
["Newmont","US6516391066","NEM","Gold / Mining",2136.82],
["X-FAB Silicon Foundries","BE0974310428","XFAB.PA","Semiconductors",1832.21],
["Kratos Defense & Security","US50077B2079","KTOS","Defense / Drones",1726.88],
["ONWARD Medical","NL0015000HT4","ONWD.BR","MedTech",1669.90],
["IREN","AU0000185993","IREN","AI / Data Centers",1614.16],
["Celsius Holdings","US15118V2079","CELH","Consumer / Beverages",1557.20],
["Redwire","US75776W1036","RDW","Space",1259.48],
["T1 Energy","US35834F1049","TE","Solar / Energy",1227.31],
["Denison Mines","CA2483561072","DNN","Uranium",1185.99],
["AbCellera","CA00288U1066","ABCL","Biotech / AI",1075.51],
["Tudor Gold","CA89901T1093","TUD.V","Gold Exploration",786.81],
["Neurotech International","AU000000NTI9","NTI.AX","Biotech",618.99],
["Lotus Resources","AU0000058737","LOT.AX","Uranium",585.38],
["Diginex","KYG286871127","DGNX","RegTech / ESG",532.11],
]
COLS=["Name","ISIN","Ticker","Thema","Marktwert EUR"]
MARKETS={"S&P 500":"^GSPC","Nasdaq 100":"^NDX","DAX":"^GDAXI","ATX":"^ATX","Gold":"GC=F","Bitcoin":"BTC-USD","US 10Y":"^TNX","VIX":"^VIX"}

if "portfolio" not in st.session_state: st.session_state.portfolio=pd.DataFrame(DEFAULT,columns=COLS)
if "live" not in st.session_state: st.session_state.live=None

@st.cache_data(ttl=1200,show_spinner=False)
def batch_prices(tickers,period="1y"):
    if not tickers:return pd.DataFrame()
    try:h=yf.download(tickers,period=period,auto_adjust=True,group_by="ticker",threads=True,progress=False,timeout=12)
    except:return pd.DataFrame()
    rows=[]
    for t in tickers:
        try:
            c=(h["Close"] if len(tickers)==1 else h[t]["Close"]).dropna()
            last=float(c.iloc[-1]); d1=(last/c.iloc[-2]-1)*100 if len(c)>1 else None
            m1=(last/c.iloc[-22]-1)*100 if len(c)>22 else None
            idx=pd.to_datetime(c.index); yc=c[idx.year==datetime.now().year]
            ytd=(last/yc.iloc[0]-1)*100 if len(yc) else None
            y1=(last/c.iloc[0]-1)*100 if len(c)>1 else None
            vol=float(c.pct_change().dropna().std()*(252**.5)*100) if len(c)>20 else None
            rows.append([t,last,d1,m1,ytd,y1,vol])
        except:pass
    return pd.DataFrame(rows,columns=["Ticker","Kurs","1T %","1M %","YTD %","1J %","Vol %"])

@st.cache_data(ttl=1200,show_spinner=False)
def rss_news(query,limit=8):
    url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        f=feedparser.parse(url)
        return [(e.get("title",""),e.get("link",""),e.get("published","")) for e in f.entries[:limit]]
    except:return []

@st.cache_data(ttl=21600,show_spinner=False)
def earnings(ticker):
    try:
        cal=yf.Ticker(ticker).calendar;e=cal.get("Earnings Date") if isinstance(cal,dict) else None
        if isinstance(e,list) and e:return str(e[0])[:10]
        return str(e)[:10] if e is not None else None
    except:return None

def score(r):
    s=5.
    if pd.notna(r.get("1M %")):s+=1 if r["1M %"]>10 else -1 if r["1M %"]<-10 else 0
    if pd.notna(r.get("YTD %")):s+=1 if r["YTD %"]>25 else -1 if r["YTD %"]<-25 else 0
    if pd.notna(r.get("Vol %")) and r["Vol %"]>80:s-=.75
    s=max(1,min(10,round(s,1)))
    sig="Buy" if s>=8 else "Hold" if s>=6 else "Watch" if s>=4 else "Reduce" if s>=2.5 else "Sell"
    return pd.Series([s,sig])

with st.sidebar:
    st.markdown("## Investment Cockpit")
    st.caption("Markets · Ideas · Your Watchlist")
    st.markdown("### MARKETS")
    st.markdown("Overview  \nMarket News  \nKobeissi / X  \nMacro & Rates")
    st.markdown("### PORTFOLIO")
    st.markdown("My Watchlist  \nPerformance  \nRisk Monitor  \nCompany View")
    st.markdown("### MANAGEMENT")
    with st.expander("＋ Add Security"):
        with st.form("add",clear_on_submit=True):
            n=st.text_input("Name");i=st.text_input("ISIN");t=st.text_input("Yahoo Ticker");th=st.text_input("Investment Theme")
            v=st.number_input("Market Value EUR (optional)",0.0,value=0.0,step=100.0)
            if st.form_submit_button("Add",use_container_width=True) and n and t:
                st.session_state.portfolio=pd.concat([st.session_state.portfolio,pd.DataFrame([[n,i,t.upper(),th,v or None]],columns=COLS)],ignore_index=True)
                st.session_state.live=None;st.rerun()
    if len(st.session_state.portfolio):
        rem=st.selectbox("Manage Portfolio",st.session_state.portfolio.Name.tolist())
        if st.button("Delete selected security",use_container_width=True):
            st.session_state.portfolio=st.session_state.portfolio[st.session_state.portfolio.Name!=rem].reset_index(drop=True);st.session_state.live=None;st.rerun()

base=st.session_state.portfolio.copy()
st.markdown("""<div class="hero"><div class="eyebrow">Portfolio Intelligence</div><h1>Investment Cockpit</h1>
<p>Ihre Märkte. Ihre Watchlist. Ihre Insights.</p></div>""",unsafe_allow_html=True)

b1,b2=st.columns([1,5])
with b1:
    if st.button("↻ Live-Daten aktualisieren",type="primary",use_container_width=True):
        with st.spinner("Marktdaten werden aktualisiert …"):
            p=batch_prices(base.Ticker.dropna().tolist())
            st.session_state.live=base.merge(p,on="Ticker",how="left") if not p.empty else base.copy()
        st.rerun()
with b2: st.caption("Market Pulse, Portfolio-Kurse, Performance und News werden gecacht und auf Anforderung aktualisiert.")

# Market pulse loads as one small batch
mp=batch_prices(list(MARKETS.values()),period="1mo")
market_cards=[]
for name,ticker in MARKETS.items():
    r=mp[mp.Ticker==ticker]
    if len(r):market_cards.append((name,float(r.iloc[0].Kurs),r.iloc[0]["1T %"]))
    else:market_cards.append((name,None,None))
cols=st.columns(8)
for c,(name,val,ch) in zip(cols,market_cards):
    c.metric(name,f"{val:,.2f}" if val is not None else "n/a",f"{ch:+.2f}%" if pd.notna(ch) else None)

df=st.session_state.live.copy() if st.session_state.live is not None else base.copy()
for c in ["Kurs","1T %","1M %","YTD %","1J %","Vol %"]:
    if c not in df:df[c]=None
df[["Score","Signal"]]=df.apply(score,axis=1)

tabs=st.tabs(["Overview","Market News","Kobeissi / X","My Watchlist","Performance","Risk Monitor","Company View"])

with tabs[0]:
    left,mid,right=st.columns([1.35,1,1])
    with left:
        st.markdown('<div class="section">Top Market News</div>',unsafe_allow_html=True)
        for title,link,pub in rss_news("stock market OR Federal Reserve OR inflation OR bonds OR earnings",6):
            st.markdown(f'<div class="news-card"><div class="news-meta">{pub}</div><div class="news-title"><a href="{link}" target="_blank">{title}</a></div></div>',unsafe_allow_html=True)
    with mid:
        st.markdown('<div class="section">My Portfolio – What changed?</div>',unsafe_allow_html=True)
        st.dataframe(df[["Name","Kurs","1T %","YTD %","Score","Signal"]].sort_values("1T %",ascending=False,na_position="last"),
                     use_container_width=True,hide_index=True,height=430)
    with right:
        st.markdown('<div class="section">The Kobeissi Letter – X Radar</div>',unsafe_allow_html=True)
        st.caption("Public web/news mentions and indexed X posts. Direct X API can be added later.")
        for title,link,pub in rss_news('"The Kobeissi Letter" OR @KobeissiLetter',6):
            st.markdown(f'<div class="news-card"><div class="news-meta">{pub}</div><div class="news-title"><a href="{link}" target="_blank">{title}</a></div></div>',unsafe_allow_html=True)
    st.divider()
    c1,c2=st.columns([1.4,1])
    with c1:
        st.markdown('<div class="section">Portfolio Performance</div>',unsafe_allow_html=True)
        if st.session_state.live is None:st.info("Live-Daten laden, um die Performance zu sehen.")
        else:
            p=df.dropna(subset=["YTD %"]).sort_values("YTD %")
            if len(p):st.plotly_chart(px.bar(p,x="YTD %",y="Name",orientation="h"),use_container_width=True)
    with c2:
        st.markdown('<div class="section">Allokation nach Investmentthemen</div>',unsafe_allow_html=True)
        a=df.groupby("Thema").size().reset_index(name="Titel")
        if len(a):
            fig=px.pie(a,names="Thema",values="Titel",hole=.62);fig.update_layout(height=350,margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig,use_container_width=True)

with tabs[1]:
    st.markdown("## Market News")
    category=st.segmented_control("Kategorie",["Markets","Economy","Companies","Central Banks","Geopolitics","Commodities"],default="Markets")
    qs={"Markets":"global stock market","Economy":"economy inflation growth","Companies":"corporate earnings stocks","Central Banks":"Federal Reserve ECB central banks","Geopolitics":"geopolitics markets trade tariffs","Commodities":"oil gold commodities"}[category]
    for title,link,pub in rss_news(qs,15):
        st.markdown(f'<div class="news-card"><div class="news-meta">{pub} <span class="badge">{category}</span></div><div class="news-title"><a href="{link}" target="_blank">{title}</a></div></div>',unsafe_allow_html=True)

with tabs[2]:
    st.markdown("## The Kobeissi Letter – Update")
    st.caption("Diese Version nutzt öffentlich indexierte News/Web-Ergebnisse zu The Kobeissi Letter. Ein echter X-Feed benötigt eine X-API bzw. einen geeigneten Connector.")
    for title,link,pub in rss_news('"Kobeissi Letter" markets OR stocks OR bonds OR Fed',15):
        st.markdown(f'<div class="news-card"><div class="news-meta">{pub}</div><div class="news-title"><a href="{link}" target="_blank">{title}</a></div></div>',unsafe_allow_html=True)

with tabs[3]:
    st.dataframe(df[["Name","ISIN","Ticker","Thema","Kurs","1T %","1M %","YTD %","1J %","Vol %","Score","Signal","Marktwert EUR"]],
                 use_container_width=True,hide_index=True,height=650)
    st.download_button("Export CSV",df.to_csv(index=False).encode(),"portfolio_watchlist.csv","text/csv")

with tabs[4]:
    if st.session_state.live is None:st.info("Bitte zuerst Live-Daten aktualisieren.")
    else:
        period=st.segmented_control("Zeitraum",["1T %","1M %","YTD %","1J %"],default="YTD %")
        p=df.dropna(subset=[period]).sort_values(period)
        if len(p):st.plotly_chart(px.bar(p,x=period,y="Name",orientation="h",text=period),use_container_width=True)

with tabs[5]:
    if st.session_state.live is None:st.info("Live-Daten laden, um Risiken zu berechnen.")
    else:
        risk=df[(pd.to_numeric(df["1T %"],errors="coerce")<=-8)|(pd.to_numeric(df["Vol %"],errors="coerce")>=80)]
        st.dataframe(risk[["Name","Ticker","1T %","1M %","Vol %","Score","Signal"]],use_container_width=True,hide_index=True)

with tabs[6]:
    selected=st.selectbox("Unternehmen",df.Name.tolist());r=df[df.Name==selected].iloc[0]
    q1,q2,q3,q4=st.columns(4)
    q1.metric("Kurs",f"{r.Kurs:.2f}" if pd.notna(r.Kurs) else "n/a");q2.metric("1M",f"{r['1M %']:+.2f}%" if pd.notna(r["1M %"]) else "n/a")
    q3.metric("Score",f"{r.Score:.1f}/10");q4.metric("Signal",r.Signal)
    if st.button("Earnings & News laden",type="primary"):
        st.markdown(f"### Nächste Earnings: {earnings(r.Ticker) or 'nicht verfügbar'}")
        for title,link,pub in rss_news(f'"{r.Name}" stock',8):
            st.markdown(f'<div class="news-card"><div class="news-meta">{pub}</div><div class="news-title"><a href="{link}" target="_blank">{title}</a></div></div>',unsafe_allow_html=True)

st.divider()
st.caption("Daten: Yahoo Finance & Google News RSS. Kobeissi-Bereich ist kein direkter X-API-Feed. Marktdaten können verzögert sein. Keine Anlageberatung.")
