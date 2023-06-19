# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pandas as pd
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, ColumnsAutoSizeMode

from retrieval import generate_answer
import utils

st.set_page_config(
    page_title="Q&A over Biomedical Literature",
    page_icon='app/images/logo.png',
    layout="wide",
)

st.title("Q&A over Biomedical Literature")

questions = [
    "Select a question",
    "Does metformin interfere thyroxine absorption?",
    "Orteronel was developed for treatment of which cancer?",
    "Has Denosumab been approved by FDA?",
    "What are all classes of anti-arrhythmic drugs according to Vaughan-Williams classification?"
]

st.divider()

cols = st.columns([30, 10, 70])

answer = ''
sources = []

with cols[0]:
    question = st.selectbox("Question", questions)

if question != questions[0]:
    result = generate_answer(question)
    answer = result["answer"]
    sources = result["sources"]

with cols[2]:
    st.caption("Answer:")
    st.write(answer)

st.divider()

df = pd.DataFrame(sources, columns=['title', 'ncbi_ref', 'download'])
gb = GridOptionsBuilder.from_dataframe(df[['title']])
gb.configure_selection()
gb.configure_column('title', header_name="Sources")
gridOptions = gb.build()


if sources:
    data = AgGrid(
        df,
        height=150,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)

    selected_rows = data["selected_rows"]

    if len(selected_rows) != 0:
        st.markdown(f"*NCBI REF:* {selected_rows[0]['ncbi_ref']}")
        st.markdown(utils.show_pdf(selected_rows[0]['download']), unsafe_allow_html=True)

else:
    st.caption('No Sources')
