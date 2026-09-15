import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Investment Cockpit", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ---------- DESIGN ----------
st.markdown("""
<style>
:root {--navy:#063b74;--blue:#0b78e3;--line:#e2e8f0;--muted:#64748b;--bg:#f7f9fc;}
.stApp {background:#f7f9fc;}
.block-container {padding:1.2rem 1.5rem 3rem 1.5rem; max-width:1600px;}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #e2e8f0;}
[data-testid="stSidebar"] .block-container {padding-top:1rem;}
.hero {background:linear-gradient(120deg,#073b70,#0a5b9e);color:white;border-radius:14px;padding:26px 30px;margin:8px 0 14px 0;}
.hero .small {font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.78;font-weight:700;}
.hero h1 {margin:4px 0 3px 0;font-size:32px;}
.hero p {margin:0;opacity:.86;}
div[data-testid="stMetric"] {background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
div[data-testid="stMetricLabel"] {color:#64748b;}
.panel-title {font-weight:700;font-size:18px;color:#0f2f57;margin:4px 0 10px 0;}
.soft {color:#64748b;font-size:13px;}
.signal-buy {color:#059669;font-weight:700}.signal-sell{color:#dc2626;font-weight:700}
.stTabs [data-baseweb="tab-list"] {gap:4px;background:white;border:1px solid #e2e8f0;border-radius:12px;padding:4px;}
.stTabs [data-baseweb="tab"] {border-radius:9px;padding:8px 15px;}
</style>
""", unsafe_allow_html=True)

DEFAULT = [
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

if "portfolio" not in st.session_state:
    st.session_state.portfolio=pd.DataFrame(DEFAULT,columns=COLS)
if "live" not in st.session_state:
    st.session_state.live=None

@st.cache_data(ttl=1800, show_spinner=False)
def prices(tickers):
    if not tickers: return pd.DataFrame()
    try:
        h=yf.download(tickers,period="1y",auto_adjust=True,group_by="ticker",threads=True,progress=False,timeout=12)
    except Exception:
        return pd.DataFrame()
    rows=[]
    for t in tickers:
        try:
            c=(h["Close"] if len(tickers)==1 else h[t]["Close"]).dropna()
            last=float(c.iloc[-1])
            d1=(last/c.iloc[-2]-1)*100 if len(c)>1 else None
            m1=(last/c.iloc[-22]-1)*100 if len(c)>22 else None
            idx=pd.to_datetime(c.index); yc=c[idx.year==datetime.now().year]
            ytd=(last/yc.iloc[0]-1)*100 if len(yc) else None
            y1=(last/c.iloc[0]-1)*100 if len(c)>1 else None
            vol=float(c.pct_change().dropna().std()*(252**.5)*100) if len(c)>20 else None
            rows.append([t,last,d1,m1,ytd,y1,vol])
        except Exception: pass
    return pd.DataFrame(rows,columns=["Ticker","Kurs","1T %","1M %","YTD %","1J %","Vol %"])

@st.cache_data(ttl=21600,show_spinner=False)
def earnings(ticker):
    try:
        cal=yf.Ticker(ticker).calendar
        e=cal.get("Earnings Date") if isinstance(cal,dict) else None
        if isinstance(e,list) and e:return str(e[0])[:10]
        return str(e)[:10] if e is not None else None
    except Exception:return None

@st.cache_data(ttl=1800,show_spinner=False)
def news(name):
    try:
        q=name.replace(" ","%20")
        f=feedparser.parse(f"https://news.google.com/rss/search?q={q}%20stock&hl=en-US&gl=US&ceid=US:en")
        return [(e.get("title",""),e.get("link",""),e.get("published","")) for e in f.entries[:7]]
    except Exception:return []

def scoring(r):
    s=5.0
    if pd.notna(r.get("1M %")): s += 1 if r["1M %"]>10 else -1 if r["1M %"]<-10 else 0
    if pd.notna(r.get("YTD %")): s += 1 if r["YTD %"]>25 else -1 if r["YTD %"]<-25 else 0
    if pd.notna(r.get("Vol %")) and r["Vol %"]>80:s-=.75
    s=max(1,min(10,round(s,1)))
    sig="Buy" if s>=8 else "Hold" if s>=6 else "Watch" if s>=4 else "Reduce" if s>=2.5 else "Sell"
    return pd.Series([s,sig])

# ---------- SIDEBAR / PORTFOLIO MANAGEMENT ----------
with st.sidebar:
    st.markdown("## Investment Cockpit")
    st.caption("Markets · Ideas · Your Watchlist")
    st.divider()
    st.markdown("### Portfolio Management")
    with st.expander("＋ Neuen Titel hinzufügen",expanded=False):
        with st.form("add",clear_on_submit=True):
            nm=st.text_input("Name",placeholder="z. B. Microsoft")
            isin=st.text_input("ISIN",placeholder="US5949181045")
            ticker=st.text_input("Ticker (Yahoo)",placeholder="MSFT")
            theme=st.text_input("Investmentthema",placeholder="AI / Software")
            val=st.number_input("Marktwert (optional, EUR)",min_value=0.0,value=0.0,step=100.0)
            ok=st.form_submit_button("Titel hinzufügen",use_container_width=True)
            if ok and nm and ticker:
                row=pd.DataFrame([[nm,isin,ticker.upper(),theme,val if val else None]],columns=COLS)
                st.session_state.portfolio=pd.concat([st.session_state.portfolio,row],ignore_index=True)
                st.session_state.live=None
                st.success(f"{nm} hinzugefügt.")
    st.markdown("#### Titel verwalten")
    if len(st.session_state.portfolio):
        rem=st.selectbox("Titel auswählen",st.session_state.portfolio.Name.tolist(),label_visibility="collapsed")
        if st.button("🗑 Titel löschen",use_container_width=True):
            st.session_state.portfolio=st.session_state.portfolio[st.session_state.portfolio.Name!=rem].reset_index(drop=True)
            st.session_state.live=None
            st.rerun()
    st.divider()
    if st.button("↻ Ausgangsliste wiederherstellen",use_container_width=True):
        st.session_state.portfolio=pd.DataFrame(DEFAULT,columns=COLS);st.session_state.live=None;st.rerun()
    st.caption("Hinweis: Änderungen sind in V6 sitzungsbezogen. Persistente Speicherung folgt als Datenbank-Upgrade.")

base=st.session_state.portfolio.copy()

# ---------- HEADER ----------
st.markdown("""<div class="hero">
<div class="small">Portfolio Intelligence</div>
<h1>Investment Cockpit</h1>
<p>Watchlist, Momentum, Risiken und Unternehmensereignisse auf einen Blick.</p>
</div>""",unsafe_allow_html=True)

a,b=st.columns([1.25,5])
with a:
    if st.button("↻ Daten aktualisieren",type="primary",use_container_width=True):
        with st.spinner("Marktdaten werden geladen …"):
            p=prices(base.Ticker.dropna().tolist())
            st.session_state.live=base.merge(p,on="Ticker",how="left") if not p.empty else base.copy()
        st.rerun()
with b:
    st.caption("Kurse und Performance werden auf Anforderung aktualisiert. Earnings und News werden in der Company View geladen.")

df=st.session_state.live.copy() if st.session_state.live is not None else base.copy()
for c in ["Kurs","1T %","1M %","YTD %","1J %","Vol %"]:
    if c not in df:df[c]=None
df[["Score","Signal"]]=df.apply(scoring,axis=1)

# ---------- KPI ----------
k1,k2,k3,k4=st.columns(4)
k1.metric("Anzahl Titel",len(df))
k2.metric("Gesamtwert (Snapshot)",f"€ {df['Marktwert EUR'].sum(skipna=True):,.0f}")
avg_ytd=pd.to_numeric(df["YTD %"],errors="coerce").mean()
k3.metric("Ø Performance YTD",f"{avg_ytd:+.1f}%" if pd.notna(avg_ytd) else "Live-Daten laden")
k4.metric("Ø Watchlist Score",f"{df.Score.mean():.1f} / 10")

tabs=st.tabs(["Overview","Watchlist","Performance","Risiken","Company View"])

with tabs[0]:
    left,right=st.columns([1.55,1])
    with left:
        st.markdown('<div class="panel-title">Meine Watchlist</div>',unsafe_allow_html=True)
        st.dataframe(df[["Name","ISIN","Ticker","Kurs","1T %","1M %","YTD %","Score","Signal"]],
            use_container_width=True,hide_index=True,
            column_config={
                "Kurs":st.column_config.NumberColumn(format="%.2f"),
                "1T %":st.column_config.NumberColumn("1T",format="%.2f%%"),
                "1M %":st.column_config.NumberColumn("1M",format="%.2f%%"),
                "YTD %":st.column_config.NumberColumn("YTD",format="%.2f%%"),
                "Score":st.column_config.ProgressColumn(min_value=1,max_value=10,format="%.1f")
            },height=510)
    with right:
        st.markdown('<div class="panel-title">Allokation nach Investmentthemen</div>',unsafe_allow_html=True)
        alloc=df.groupby("Thema",dropna=False).size().reset_index(name="Titel")
        if len(alloc):
            fig=px.pie(alloc,names="Thema",values="Titel",hole=.58)
            fig.update_layout(height=330,margin=dict(l=5,r=5,t=5,b=5),legend=dict(orientation="h"))
            st.plotly_chart(fig,use_container_width=True)
        st.markdown('<div class="panel-title">Signal Summary</div>',unsafe_allow_html=True)
        sig=df.groupby("Signal").size().reset_index(name="Titel")
        st.dataframe(sig,use_container_width=True,hide_index=True)

    if st.session_state.live is not None:
        p=df.dropna(subset=["1M %"]).sort_values("1M %")
        c1,c2=st.columns(2)
        with c1:
            st.markdown('<div class="panel-title">Top Performer (1M)</div>',unsafe_allow_html=True)
            st.dataframe(p.tail(5)[["Name","1M %","Score","Signal"]].sort_values("1M %",ascending=False),use_container_width=True,hide_index=True)
        with c2:
            st.markdown('<div class="panel-title">Flop Performer (1M)</div>',unsafe_allow_html=True)
            st.dataframe(p.head(5)[["Name","1M %","Score","Signal"]],use_container_width=True,hide_index=True)

with tabs[1]:
    st.markdown('<div class="panel-title">Portfolio Watchlist</div>',unsafe_allow_html=True)
    st.dataframe(df[["Name","ISIN","Ticker","Thema","Kurs","1T %","1M %","YTD %","1J %","Vol %","Score","Signal","Marktwert EUR"]],
                 use_container_width=True,hide_index=True,height=650)
    st.download_button("Export CSV",df.to_csv(index=False).encode("utf-8"),"portfolio_watchlist.csv","text/csv")

with tabs[2]:
    if st.session_state.live is None:
        st.info("Bitte zuerst oben auf „Daten aktualisieren“ klicken.")
    else:
        period=st.radio("Zeitraum",["1T %","1M %","YTD %","1J %"],index=2,horizontal=True)
        p=df.dropna(subset=[period]).sort_values(period)
        if len(p):
            fig=px.bar(p,x=period,y="Name",orientation="h",text=period)
            fig.update_traces(texttemplate="%{text:.1f}%")
            fig.update_layout(height=max(480,len(p)*31),margin=dict(l=0,r=20,t=10,b=0))
            st.plotly_chart(fig,use_container_width=True)

with tabs[3]:
    if st.session_state.live is None:
        st.info("Risikoanalyse wird nach dem Laden der Live-Daten verfügbar.")
    else:
        risk=df[(pd.to_numeric(df["1T %"],errors="coerce")<=-8)|(pd.to_numeric(df["Vol %"],errors="coerce")>=80)]
        r1,r2,r3=st.columns(3)
        r1.metric("Tagesverlust >8%",int((pd.to_numeric(df["1T %"],errors="coerce")<=-8).sum()))
        r2.metric("Volatilität >80%",int((pd.to_numeric(df["Vol %"],errors="coerce")>=80).sum()))
        r3.metric("Reduce / Sell",int(df.Signal.isin(["Reduce","Sell"]).sum()))
        if len(risk):
            st.dataframe(risk[["Name","Ticker","1T %","1M %","Vol %","Score","Signal"]],use_container_width=True,hide_index=True)
        else:st.success("Aktuell keine Titel oberhalb der definierten Risikoschwellen.")

with tabs[4]:
    selected=st.selectbox("Unternehmen auswählen",df.Name.tolist())
    row=df[df.Name==selected].iloc[0]
    st.markdown(f"## {row.Name}")
    st.caption(f"{row.ISIN} · {row.Ticker} · {row.Thema}")
    q1,q2,q3,q4=st.columns(4)
    q1.metric("Kurs",f"{row.Kurs:.2f}" if pd.notna(row.Kurs) else "n/a")
    q2.metric("1M",f"{row['1M %']:+.2f}%" if pd.notna(row["1M %"]) else "n/a")
    q3.metric("Score",f"{row.Score:.1f}/10")
    q4.metric("Signal",row.Signal)
    if st.button("Earnings & News laden",type="primary"):
        with st.spinner("Unternehmensdaten werden geladen …"):
            ed=earnings(row.Ticker); ns=news(row.Name)
        st.markdown(f"### Nächste Earnings: {ed or 'nicht verfügbar'}")
        st.markdown("### Aktuelle News")
        if ns:
            for title,link,published in ns:
                st.markdown(f"**[{title}]({link})**")
                if published:st.caption(published)
        else:st.write("Keine News verfügbar.")

st.divider()
st.caption("Marktdaten können verzögert oder unvollständig sein. Der Watchlist-Score ist ein technischer Indikator und keine Anlageempfehlung.")
