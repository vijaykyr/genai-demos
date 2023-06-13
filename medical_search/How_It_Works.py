import streamlit as st

st.set_page_config(
    page_title="Q&A over Biomedical Literature",
    page_icon='app/images/logo.png',
)

cols = st.columns([13, 87])
with cols[0]:
    st.image('app/images/logo.png')
with cols[1]:
    st.title('Q&A over Biomedical Literature')

st.write('''Demo using BioASQ dataset''')

st.image('app/images/architecture.png')


st.subheader('How it Works')
st.write('Description here...')
