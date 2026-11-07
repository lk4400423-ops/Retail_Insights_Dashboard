import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Retail Pulse | Analytics", page_icon="📈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.4rem;padding-bottom:2rem}
[data-testid="stMetric"]{background:#f3f6fb;border:1px solid #e2e8f0;padding:16px;border-radius:12px}
[data-testid="stSidebar"]{background:#f7f9fc}
h1{letter-spacing:-1px}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    data=pd.read_csv("retail_data.csv", parse_dates=["Order_Date"])
    return data

df=load_data()
st.title("📈 RETAIL PULSE")
st.caption("A fresh view of revenue, customer segments and product performance")

with st.sidebar:
    st.header("Dashboard Controls")
    regions=st.multiselect("Sales region", sorted(df.Region.unique()), default=sorted(df.Region.unique()))
    categories=st.multiselect("Product category", sorted(df.Category.unique()), default=sorted(df.Category.unique()))
    segments=st.multiselect("Customer segment", sorted(df.Customer_Segment.unique()), default=sorted(df.Customer_Segment.unique()))
    date_range=st.date_input("Order period", value=(df.Order_Date.min().date(),df.Order_Date.max().date()))
    st.divider()
    st.caption("All figures are based on the selected records.")

filtered=df[df.Region.isin(regions)&df.Category.isin(categories)&df.Customer_Segment.isin(segments)].copy()
if isinstance(date_range,tuple) and len(date_range)==2:
    filtered=filtered[filtered.Order_Date.between(pd.Timestamp(date_range[0]),pd.Timestamp(date_range[1])+pd.Timedelta(days=1)-pd.Timedelta(seconds=1))]
if filtered.empty:
    st.warning("No records match these filters. Select a wider range.")
    st.stop()

revenue=filtered.Revenue.sum(); profit=filtered.Profit.sum(); orders=filtered.Order_ID.nunique(); avg_order=revenue/orders if orders else 0
k1,k2,k3,k4=st.columns(4)
k1.metric("Total Revenue",f"₹{revenue:,.0f}")
k2.metric("Net Profit",f"₹{profit:,.0f}")
k3.metric("Orders",f"{orders:,}")
k4.metric("Average Order Value",f"₹{avg_order:,.0f}")
st.markdown("---")

left,right=st.columns([1.55,1])
with left:
    st.subheader("Revenue trend")
    trend=filtered.assign(Month=filtered.Order_Date.dt.to_period('M').dt.to_timestamp()).groupby('Month',as_index=False).agg(Revenue=('Revenue','sum'),Profit=('Profit','sum'))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=trend.Month,y=trend.Revenue,mode='lines+markers',name='Revenue',line=dict(width=3)))
    fig.add_trace(go.Scatter(x=trend.Month,y=trend.Profit,mode='lines',name='Profit',line=dict(width=2,dash='dot')))
    fig.update_layout(template='plotly_white',height=340,margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation='h',y=1.12))
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.subheader("Revenue mix")
    mix=filtered.groupby('Category',as_index=False).Revenue.sum()
    st.plotly_chart(px.pie(mix,names='Category',values='Revenue',hole=.62,color_discrete_sequence=px.colors.qualitative.Safe).update_layout(template='plotly_white',height=340,margin=dict(l=5,r=5,t=20,b=5)),use_container_width=True)

c1,c2=st.columns(2)
with c1:
    st.subheader("Top products by revenue")
    top=filtered.groupby('Product',as_index=False).Revenue.sum().nlargest(8,'Revenue').sort_values('Revenue')
    fig=px.bar(top,x='Revenue',y='Product',orientation='h',text_auto='.2s',color='Revenue',color_continuous_scale='Blues')
    fig.update_layout(template='plotly_white',height=360,margin=dict(l=5,r=5,t=15,b=5),coloraxis_showscale=False)
    st.plotly_chart(fig,use_container_width=True)
with c2:
    st.subheader("Profit by region")
    reg=filtered.groupby('Region',as_index=False).agg(Profit=('Profit','sum'),Revenue=('Revenue','sum'))
    fig=px.bar(reg,x='Region',y='Profit',color='Revenue',text_auto='.2s',color_continuous_scale='Teal')
    fig.update_layout(template='plotly_white',height=360,margin=dict(l=5,r=5,t=15,b=5),coloraxis_showscale=False)
    st.plotly_chart(fig,use_container_width=True)

c3,c4=st.columns(2)
with c3:
    st.subheader("Customer segment performance")
    seg=filtered.groupby('Customer_Segment',as_index=False).agg(Revenue=('Revenue','sum'),Orders=('Order_ID','nunique'))
    st.plotly_chart(px.bar(seg,x='Customer_Segment',y='Revenue',color='Customer_Segment',text_auto='.2s',color_discrete_sequence=px.colors.qualitative.Pastel).update_layout(template='plotly_white',height=320,showlegend=False,margin=dict(l=5,r=5,t=15,b=5)),use_container_width=True)
with c4:
    st.subheader("Discount vs profit")
    st.plotly_chart(px.scatter(filtered,x='Discount',y='Profit',size='Quantity',color='Category',hover_data=['Product','Region'],opacity=.7).update_layout(template='plotly_white',height=320,margin=dict(l=5,r=5,t=15,b=5)),use_container_width=True)

with st.expander("Explore filtered order records"):
    st.dataframe(filtered.sort_values('Order_Date',ascending=False),use_container_width=True,hide_index=True)
    st.download_button("Download filtered CSV",filtered.to_csv(index=False).encode('utf-8'),"retail_filtered.csv","text/csv")
st.caption(f"Showing {len(filtered):,} of {len(df):,} generated retail orders · Currency shown in INR")
