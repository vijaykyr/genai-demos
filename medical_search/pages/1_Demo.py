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

import streamlit as st

from retrieval import generate_answer, create_retrieval_chain

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

if 'chain' not in st.session_state:
    st.session_state.chain = create_retrieval_chain()

st.divider()

cols = st.columns([30, 10, 70])

answer = ''
sources = []

with cols[0]:
    question = st.selectbox("Question", questions)

if question != questions[0]:
    result = generate_answer(st.session_state.chain, question)
    answer = result["answer"]
    sources = result["sources"]

with cols[2]:
    st.caption("Answer:")
    st.write(answer)

st.divider()

if sources:
    st.caption("Sources:")
    for source in sources:
        st.markdown(source)