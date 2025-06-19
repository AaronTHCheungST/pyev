import streamlit as st

st.set_page_config(layout='wide')

st.markdown("""
<style>
    .stMultiSelect [data-baseweb=select] span{
        max-width: 500px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)  # reduce multiselect font size and increase element width

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)  # hide upper-right corner menu

st.header("📖 Introduction")
st.subheader("What is this")
st.write("""
         This tool is developed for Python developers who want to check the dependencies within a development environment (e.g., conda, venv) to check if the licenses of the installed packages are compatible to the intented license of their developed program.
         
         Python developers can select licenses which they have concern about and see how they affect the dependency graph of a development environment
         """)

st.subheader("How to use it")
st.write("Install [pipdeptree](https://pypi.org/project/pipdeptree/) in your environment. Then run the following command to generate the dependent packages in the file *my_dependency.json*")
st.code("pipdeptree --json > my_dependency.json", language="pipdeptree")
st.write("Then, navigate to **፨ Dependency Graph**, upload the file, and select what licenses you have concern about.")


st.subheader("Contact")
st.write("Aaron Cheung, aaronthcheung@gmail.com")

st.subheader("Disclaimer")
st.write("I am not a lawyer (IANAL). Any output provided by this software/tool/website is for general information only and should not be construed as legal advice. There is no guarantee that the information provided in this tool/software/website is complete or correct. Any reliance on the information provided by this software is at your own risk")
st.write("License: MIT")
