import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
import utils

st.set_page_config(
    page_title="Q&A over Biomedical Literature",
    page_icon='app/images/logo.png',
)

st.markdown('### Select a document to preview')
col1, col2 = st.columns([1,3])
df = pd.read_json("data/articles.json")
gb = GridOptionsBuilder.from_dataframe(df[['title']])
gb.configure_selection(selection_mode="single")
gridOptions = gb.build()

with col1:
    data = AgGrid(df, gridOptions=gridOptions)

selected_rows = data["selected_rows"]

with col2:
    if len(selected_rows) != 0:
        st.markdown(f"*NCBI REF:* {selected_rows[0]['ncbi_ref']}")
        st.markdown(utils.show_pdf(selected_rows[0]['download']), unsafe_allow_html=True)