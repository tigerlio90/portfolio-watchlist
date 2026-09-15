
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Portfolio Watchlist", page_icon="📈", layout="wide")

DATA = [
["AeroVironment","US0080731088","AVAV","Aktie",3274.02,24.9,131.50,12.70,"Defense / Drones"],
["BlackSky Technology","US09263B2079","BKSY","Aktie",None,None,18.03,None,"Space / Geospatial"],
["Vontobel Factor Long Gold","DE000VJ3Y389",None,"Index-Zertifikat",2175.67,186.11,11.69,8.44,"Gold"],
["Newmont","US6516391066","NEM","Aktie",2136.82,20.15,106.04,8.29,"Gold / Mining"],
["VanEck Bionic Engineering ETF","IE0005TF96I9",None,"ETF",1957.83,120.26,16.28,7.59,"Robotics / Bionics"],
["X-FAB Silicon Foundries","BE0974310428","XFAB.PA","Aktie",1832.21,316.99,5.78,7.10,"Semiconductors"],
["Kratos Defense & Security","US50077B2079","KTOS","Aktie",1726.88,41.8,41.31,6.70,"Defense / Drones"],
["ONWARD Medical","NL0015000HT4","ONWD.BR","Aktie",1669.90,611.68,2.73,6.48,"MedTech"],
["IREN","AU0000185993","IREN","Aktie",1614.16,43.56,37.06,6.26,"AI / Data Centers"],
["Celsius Holdings","US15118V2079","CELH","Aktie",1557.20,63.21,24.64,6.04,"Consumer / Beverages"],
["Redwire","US75776W1036","RDW","Aktie",1259.48,138.56,9.09,4.88,"Space"],
["T1 Energy","US35834F1049","TE","Aktie",1227.31,318.78,3.85,4.76,"Solar / Energy"],
["Denison Mines","CA2483561072","DNN","Aktie",1185.99,472.51,2.51,4.60,"Uranium"],
["AbCellera","CA00288U1066","ABCL","Aktie",1075.51,112.62,9.55,4.17,"Biotech / AI"],
["Tudor Gold","CA89901T1093","TUD.V","Aktie",786.81,1356.57,0.58,3.05,"Gold Exploration"],
["Neurotech International","AU000000NTI9","NTI.AX","Aktie",618.99,77147.41,0.00802,2.40,"Biotech"],
["Lotus Resources","AU0000058737","LOT.AX","Aktie",585.38,4181.27,0.14,2.27,"Uranium"],
["LOTUS RE","AU0000446957",None,"Aktie",571.69,494.64,1.16,2.22,"Uranium"],
["Diginex","KYG286871127","DGNX","Aktie",532.11,438.93,1.21,2.06,"RegTech / ESG"],
]
COLS=["Name","ISIN","Ticker","Assetklasse","Marktwert EUR","Stück","Referenzkurs","Gewicht %","Thema"]
base_df=pd.DataFrame(DATA,columns=COLS)

@st.cache_data(ttl=1800, show_spinner=False)
def market_data(tickers):
    rows=[]
    for t in tickers:
        if not t: 
            continue
        try:
            x=yf.Ticker(t)
            h=x.history(period="1y", auto_adjust=True)
            if h.empty:
                continue
            last=float(h["Close"].iloc[-1])
            d1=(last/float(h["Close"].iloc[-2])-1)*100 if len(h)>1 else None
            m1=(last/float(h["Close"].iloc[-22])-1)*100 if len(h)>22 else None
            ytd_h=h[h.index >= pd.Timestamp(datetime.now().year,1,1,tz=h.index.tz)]
            ytd=(last/float(ytd_h["Close"].iloc[0])-1)*100 if len(ytd_h)>0 else None
            y1=(last/float(h["Close"].iloc[0])-1)*100 if len(h)>1 else None
            vol=float(h["Close"].pct_change().dropna().std()*(252**0.5)*100) if len(h)>20 else None
            info=x.info or {}
            earnings=None
            try:
                cal=x.calendar
                if isinstance(cal,dict):
                    ed=cal.get("Earnings Date")
                    if isinstance(ed,list) and ed:
                        earnings=str(ed[0])[:10]
                    elif ed is not None:
                        earnings=str(ed)[:10]
            except:
                pass
            rows.append([t,last,d1,m1,ytd,y1,vol,info.get("currency"),earnings])
        except Exception:
            pass
    return pd.DataFrame(rows,columns=["Ticker","Kurs","1T %","1M %","YTD %","1J %","Volatilität %","Währung","Nächste Earnings"])

@st.cache_data(ttl=1800, show_spinner=False)
def news_for(query):
    url="https://news.google.com/rss/search?q="+query.replace(" ","%20")+"%20stock&hl=en-US&gl=US&ceid=US:en"
    try:
        feed=feedparser.parse(url)
        return [{"title":e.get("title",""),"link":e.get("link",""),"published":e.get("published","")} for e in feed.entries[:8]]
    except:
        return []

def score_row(r):
    score=5.0
    reasons=[]
    if pd.notna(r.get("1M %")):
        if r["1M %"] > 10:
            score += 1.0; reasons.append("starkes 1M-Momentum")
        elif r["1M %"] < -10:
            score -= 1.0; reasons.append("schwaches 1M-Momentum")
    if pd.notna(r.get("YTD %")):
        if r["YTD %"] > 25:
            score += 1.0; reasons.append("starkes YTD-Momentum")
        elif r["YTD %"] < -25:
            score -= 1.0; reasons.append("schwaches YTD-Momentum")
    if pd.notna(r.get("1J %")):
        if r["1J %"] > 40:
            score += 0.5
        elif r["1J %"] < -40:
            score -= 0.5
    if pd.notna(r.get("Volatilität %")):
        if r["Volatilität %"] > 80:
            score -= 0.75; reasons.append("sehr hohe Volatilität")
        elif r["Volatilität %"] < 35:
            score += 0.25
    if pd.notna(r.get("Nächste Earnings")):
        try:
            ed=pd.to_datetime(r["Nächste Earnings"]).date()
            days=(ed-datetime.now().date()).days
            if 0 <= days <= 7:
                score -= 0.25; reasons.append("Earnings in <=7 Tagen")
        except:
            pass
    score=max(1,min(10,round(score,1)))
    if score >= 8:
        signal="🟢 Buy"
    elif score >= 6:
        signal="🟢 Hold"
    elif score >= 4:
        signal="🟡 Watch"
    elif score >= 2.5:
        signal="🟠 Reduce"
    else:
        signal="🔴 Sell"
    return score,signal,", ".join(reasons[:3]) if reasons else "neutral"

mkt=market_data(base_df["Ticker"].dropna().tolist())
df=base_df.merge(mkt,on="Ticker",how="left")
scored=df.apply(score_row,axis=1,result_type="expand")
df["Score"]=scored[0]
df["Ampel"]=scored[1]
df["Score-Grund"]=scored[2]

st.title("Portfolio Watchlist")
st.caption("Live Investment Cockpit · Kurse & Performance via Yahoo Finance · News via Google News RSS")

with st.sidebar:
    st.header("Filter")
    public=st.toggle("Public Watchlist",False)
    assets=st.multiselect("Assetklasse",sorted(df.Assetklasse.unique()),default=sorted(df.Assetklasse.unique()))
    themes=st.multiselect("Investmentthema",sorted(df.Thema.unique()),default=sorted(df.Thema.unique()))
    min_score=st.slider("Mindest-Score",1.0,10.0,1.0,0.5)
    search=st.text_input("Name / ISIN / Ticker")
    st.divider()
    st.header("Alerts")
    drop_alert=st.number_input("Tagesverlust-Alert ab %",min_value=1.0,max_value=30.0,value=8.0,step=1.0)
    earnings_days=st.number_input("Earnings-Alert in Tagen",min_value=1,max_value=30,value=7,step=1)
    if st.button("Daten aktualisieren"):
        st.cache_data.clear()
        st.rerun()

view=df[df.Assetklasse.isin(assets)&df.Thema.isin(themes)&(df["Score"]>=min_score)].copy()
if search:
    s=search.lower()
    view=view[view.apply(lambda r:s in str(r["Name"]).lower() or s in str(r["ISIN"]).lower() or s in str(r["Ticker"]).lower(),axis=1)]

c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Werte",len(view))
c2.metric("Ø Score",f"{view['Score'].mean():.1f}" if len(view) else "n/a")
c3.metric("Buy/Hold",int(view["Ampel"].isin(["🟢 Buy","🟢 Hold"]).sum()))
c4.metric("Watch",int((view["Ampel"]=="🟡 Watch").sum()))
if not public:
    c5.metric("Marktwert Snapshot",f"€ {view['Marktwert EUR'].sum(skipna=True):,.0f}")
else:
    c5.metric("Public Mode","Aktiv")

tabs=st.tabs(["Cockpit","Watchlist","Performance","News & Earnings","Alerts","Detail"])

with tabs[0]:
    left,right=st.columns([1.35,1])
    with left:
        st.subheader("Score & Signal")
        cols=["Name","Ticker","Score","Ampel","1T %","1M %","YTD %","Volatilität %","Nächste Earnings"]
        st.dataframe(view[cols].sort_values("Score",ascending=False),use_container_width=True,hide_index=True,
            column_config={
                "Score":st.column_config.ProgressColumn(min_value=1,max_value=10,format="%.1f"),
                "1T %":st.column_config.NumberColumn(format="%.2f%%"),
                "1M %":st.column_config.NumberColumn(format="%.2f%%"),
                "YTD %":st.column_config.NumberColumn(format="%.2f%%"),
                "Volatilität %":st.column_config.NumberColumn(format="%.1f%%")
            })
    with right:
        st.subheader("Signal-Verteilung")
        sig=view.groupby("Ampel",as_index=False).size()
        if len(sig):
            fig=px.pie(sig,names="Ampel",values="size",hole=.55)
            fig.update_layout(height=380,margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig,use_container_width=True)

with tabs[1]:
    cols=["Name","ISIN","Ticker","Assetklasse","Thema","Kurs","Währung","1T %","YTD %","Score","Ampel"]
    if not public:
        cols += ["Marktwert EUR","Stück","Gewicht %"]
    st.dataframe(view[cols],use_container_width=True,hide_index=True)

with tabs[2]:
    metric=st.radio("Zeitraum",["1T %","1M %","YTD %","1J %"],horizontal=True)
    p=view.dropna(subset=[metric]).sort_values(metric)
    if len(p):
        fig=px.bar(p,x=metric,y="Name",orientation="h",text=metric)
        fig.update_traces(texttemplate="%{text:.1f}%")
        fig.update_layout(height=max(450,len(p)*32),margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig,use_container_width=True)

with tabs[3]:
    left,right=st.columns([1,1.25])
    with left:
        st.subheader("Nächste Earnings")
        earn=view.dropna(subset=["Nächste Earnings"])[["Name","Ticker","Nächste Earnings","Score","Ampel"]].sort_values("Nächste Earnings")
        st.dataframe(earn,use_container_width=True,hide_index=True)
    with right:
        st.subheader("News")
        names=view["Name"].tolist()
        if names:
            nsel=st.selectbox("News zu",names)
            for n in news_for(nsel):
                st.markdown(f"**[{n['title']}]({n['link']})**")
                if n["published"]:
                    st.caption(n["published"])

with tabs[4]:
    st.subheader("Aktuelle Alerts")
    alerts=[]
    for _,r in view.iterrows():
        if pd.notna(r["1T %"]) and r["1T %"] <= -abs(drop_alert):
            alerts.append(("Kurs","🔴",r["Name"],f"{r['1T %']:.2f}% heute"))
        if pd.notna(r["Nächste Earnings"]):
            try:
                ed=pd.to_datetime(r["Nächste Earnings"]).date()
                days=(ed-datetime.now().date()).days
                if 0 <= days <= earnings_days:
                    alerts.append(("Earnings","🟠",r["Name"],f"in {days} Tagen ({ed})"))
            except:
                pass
        if r["Score"] <= 3:
            alerts.append(("Score","🔴",r["Name"],f"Score {r['Score']:.1f} / {r['Ampel']}"))
    if alerts:
        alert_df=pd.DataFrame(alerts,columns=["Typ","Level","Wert","Meldung"])
        st.dataframe(alert_df,use_container_width=True,hide_index=True)
    else:
        st.success("Aktuell keine Alerts nach deinen Schwellenwerten.")

    st.caption("Die Alerts werden in dieser Version beim Öffnen/Refresh der App geprüft. Für automatische E-Mail-/Push-Benachrichtigungen braucht es zusätzlich einen Scheduler oder externen Dienst.")

with tabs[5]:
    if len(view):
        selected=st.selectbox("Wert auswählen",view["Name"].tolist())
        r=view[view.Name==selected].iloc[0]
        st.header(selected)
        a,b,c,d,e=st.columns(5)
        a.metric("Kurs",f"{r['Kurs']:.2f} {r['Währung']}" if pd.notna(r["Kurs"]) else "n/a")
        b.metric("Heute",f"{r['1T %']:.2f}%" if pd.notna(r["1T %"]) else "n/a")
        c.metric("YTD",f"{r['YTD %']:.2f}%" if pd.notna(r["YTD %"]) else "n/a")
        d.metric("Score",f"{r['Score']:.1f}/10")
        e.metric("Signal",r["Ampel"])
        st.caption(f"Score-Treiber: {r['Score-Grund']}")
        if r["Ticker"]:
            try:
                hist=yf.Ticker(r["Ticker"]).history(period="1y",auto_adjust=True).reset_index()
                if len(hist):
                    fig=px.line(hist,x="Date",y="Close",title="1 Jahr")
                    st.plotly_chart(fig,use_container_width=True)
            except:
                pass
        st.markdown("### Investment Journal")
        st.text_area("Investment Case")
        st.text_area("Risiken / Red Flags")
        st.text_input("Nächster Trigger")
        st.selectbox("Eigene Einschätzung",["Watch","Buy","Hold","Reduce","Sell"])
        st.info("Journal-Eingaben werden in dieser Version noch nicht persistent gespeichert.")

st.divider()
st.caption("Der Score ist ein technischer Watchlist-Score, keine Anlageempfehlung. Marktdaten können verzögert oder unvollständig sein.")
