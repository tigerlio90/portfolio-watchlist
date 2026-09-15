import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Investment Cockpit",page_icon="📈",layout="wide")

DATA=[
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
BASE=pd.DataFrame(DATA,columns=["Name","ISIN","Ticker","Thema","Marktwert EUR"])

@st.cache_data(ttl=1800,show_spinner=False)
def prices():
    ts=BASE.Ticker.tolist()
    try:
        h=yf.download(ts,period="1y",auto_adjust=True,group_by="ticker",threads=True,progress=False,timeout=10)
    except Exception:
        return pd.DataFrame()
    out=[]
    for t in ts:
        try:
            c=h[t]["Close"].dropna()
            last=float(c.iloc[-1])
            d1=(last/c.iloc[-2]-1)*100 if len(c)>1 else None
            m1=(last/c.iloc[-22]-1)*100 if len(c)>22 else None
            idx=pd.to_datetime(c.index)
            yc=c[idx.year==datetime.now().year]
            ytd=(last/yc.iloc[0]-1)*100 if len(yc) else None
            y1=(last/c.iloc[0]-1)*100 if len(c)>1 else None
            vol=c.pct_change().dropna().std()*(252**.5)*100 if len(c)>20 else None
            out.append([t,last,d1,m1,ytd,y1,vol])
        except Exception: pass
    return pd.DataFrame(out,columns=["Ticker","Kurs","1T %","1M %","YTD %","1J %","Vol %"])

@st.cache_data(ttl=21600,show_spinner=False)
def earnings(t):
    try:
        cal=yf.Ticker(t).calendar
        e=cal.get("Earnings Date") if isinstance(cal,dict) else None
        if isinstance(e,list) and e:return str(e[0])[:10]
        return str(e)[:10] if e is not None else None
    except:return None

@st.cache_data(ttl=1800,show_spinner=False)
def news(name):
    try:
        q=name.replace(" ","%20")
        f=feedparser.parse(f"https://news.google.com/rss/search?q={q}%20stock&hl=en-US&gl=US&ceid=US:en")
        return [(e.get("title",""),e.get("link","")) for e in f.entries[:6]]
    except:return []

def score(r):
    s=5
    if pd.notna(r.get("1M %")): s+=1 if r["1M %"]>10 else -1 if r["1M %"]<-10 else 0
    if pd.notna(r.get("YTD %")): s+=1 if r["YTD %"]>25 else -1 if r["YTD %"]<-25 else 0
    if pd.notna(r.get("Vol %")) and r["Vol %"]>80:s-=.75
    s=max(1,min(10,round(s,1)))
    sig="🟢 Buy" if s>=8 else "🟢 Hold" if s>=6 else "🟡 Watch" if s>=4 else "🟠 Reduce" if s>=2.5 else "🔴 Sell"
    return pd.Series([s,sig])

if "df" not in st.session_state: st.session_state.df=BASE.copy()
if "live" not in st.session_state: st.session_state.live=False

st.title("Portfolio Watchlist")
st.caption("Fast Start Investment Cockpit – externe Daten werden erst auf Knopfdruck geladen.")

if st.button("🔄 Live-Kurse laden",type="primary"):
    with st.spinner("Lade Marktdaten …"):
        p=prices()
        st.session_state.df=BASE.merge(p,on="Ticker",how="left") if not p.empty else BASE.copy()
        st.session_state.live=True
    st.rerun()

df=st.session_state.df.copy()
for c in ["Kurs","1T %","1M %","YTD %","1J %","Vol %"]:
    if c not in df:df[c]=None
df[["Score","Ampel"]]=df.apply(score,axis=1)

a,b,c,d=st.columns(4)
a.metric("Werte",len(df)); b.metric("Live-Daten","geladen" if st.session_state.live else "noch nicht geladen")
c.metric("Ø Score",f"{df.Score.mean():.1f}"); d.metric("Marktwert Snapshot",f"€ {df['Marktwert EUR'].sum(skipna=True):,.0f}")

t1,t2,t3,t4=st.tabs(["Cockpit","Performance","Alerts","Detail & News"])
with t1:
    st.dataframe(df[["Name","Ticker","Kurs","1T %","1M %","YTD %","Score","Ampel"]],use_container_width=True,hide_index=True,
        column_config={"Score":st.column_config.ProgressColumn(min_value=1,max_value=10,format="%.1f")})
with t2:
    if not st.session_state.live:st.info("Zuerst Live-Kurse laden.")
    else:
        m=st.radio("Zeitraum",["1T %","1M %","YTD %","1J %"],horizontal=True)
        p=df.dropna(subset=[m]).sort_values(m)
        if len(p):st.plotly_chart(px.bar(p,x=m,y="Name",orientation="h"),use_container_width=True)
with t3:
    if st.session_state.live:
        al=df[pd.to_numeric(df["1T %"],errors="coerce")<=-8]
        st.dataframe(al[["Name","1T %","Score","Ampel"]],use_container_width=True,hide_index=True) if len(al) else st.success("Keine Tagesverlust-Alerts > 8%.")
    else:st.info("Alerts werden nach dem Laden der Kurse geprüft.")
with t4:
    n=st.selectbox("Wert auswählen",df.Name)
    r=df[df.Name==n].iloc[0]
    x,y,z=st.columns(3); x.metric("Kurs",f"{r['Kurs']:.2f}" if pd.notna(r["Kurs"]) else "n/a"); y.metric("Score",f"{r.Score:.1f}/10"); z.metric("Signal",r.Ampel)
    if st.button("📅 Earnings & News laden"):
        with st.spinner("Lade Unternehmensdaten …"):
            st.write("**Nächste Earnings:**",earnings(r.Ticker) or "nicht verfügbar")
            ns=news(n)
            st.subheader("News")
            for title,link in ns:st.markdown(f"**[{title}]({link})**")

st.caption("Score ist ein technischer Watchlist-Indikator, keine Anlageempfehlung.")
