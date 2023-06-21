import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, ColumnsAutoSizeMode

from retrieval import get_corpus
import utils

st.set_page_config(
    page_title="Q&A over Biomedical Literature",
    page_icon='app/images/logo.png',
)

st.markdown('### Enterprise Search Corpus')
st.markdown('''-Below are all the papers uploaded to Enterprise Search for this demo.  
    -Given a query Enterprise Search will identify which text snippets are most relevant.''')
st.markdown('**Select a paper to browse**')
df = pd.DataFrame(get_corpus())
gb = GridOptionsBuilder.from_dataframe(df[['title']])
gb.configure_selection()
gb.configure_column('title', header_name="Paper Title")
gb.configure_pagination()
gridOptions = gb.build()

data = AgGrid(
    df,
    gridOptions=gridOptions,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)

selected_rows = data["selected_rows"]

if len(selected_rows) != 0:
    st.markdown(f"*NCBI REF:* {selected_rows[0]['ncbi_ref']}")
    st.markdown(utils.show_pdf(selected_rows[0]['gcs_uri']), unsafe_allow_html=True)