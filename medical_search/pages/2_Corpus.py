import streamlit as st
import pandas as pd

st.write('Below are the documents uploaded to Enterprise Search')

df = pd.read_json("data/articles.json")[['title', 'download']]
st.dataframe(
    df,
    column_config={
        'title': 'Title',
        'download': st.column_config.LinkColumn("URL")})
