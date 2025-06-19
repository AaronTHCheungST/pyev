import streamlit as st
from package_utils import pipdeptree2nx, package_license, nx_count_licenses, nx_fill_license, nx_unify_license
import json
import networkx as nx
import pickle
from pyvis.network import Network
import streamlit.components.v1 as components
import functools

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

st.header("፨ Dependency graph")

# Initialization with an example pipdeptree dependency tree
if 'G' not in st.session_state:
    st.write("It is an example dependency graph. Upload a pipdeptree dependency json to view your own.")
    st.session_state['G'] = pickle.load(open('example_nx.pickle', 'rb'))
    st.session_state['filename'] = 'example'
    
with st.sidebar:
    uploaded_file = st.file_uploader("Upload pipdeptree dependency json here", type='json')
    if uploaded_file is not None and uploaded_file.name != st.session_state['filename']:
        data = json.load(uploaded_file)
        G = pipdeptree2nx(data)
        license_bar = st.progress(0, text="Fetch license")
        node_attributes = {}
        for i, n in enumerate(G.nodes):
            node_attributes[n] = {
                'license': package_license(*n.split("=="), retries=3)
            }
            license_bar.progress(int((i+1) / len(G.nodes) * 100), text="Fetch license")
        nx.set_node_attributes(G, node_attributes)
        nx_fill_license(G)
        nx_unify_license(G)
        st.session_state['G'] = G
        st.session_state['filename'] = uploaded_file.name
        st.success(f"{uploaded_file.name} is successfully uploaded")

    license_count = nx_count_licenses(st.session_state['G'])

    blacklisted_licenses = st.multiselect(
        "Blacklist licenses",
        options = license_count.keys(),
        format_func = lambda k: f"{k} (count: {license_count[k]})",
        default = ['BSD License']
    )

    show_blacklist = st.toggle(
        label = 'Show packages having blacklisted license(s)',
        value = True
    )

    show_blacklist_dependants = st.toggle(
        label = 'Show packages with ancestors having blacklisted license(s)',
        value=True
    )

blacklisted_nodes = set()
for n, licenses in st.session_state['G'].nodes(data='license'):
    if n == 'ROOT': 
        continue
    if len(set(licenses).intersection(blacklisted_licenses)) > 0:
        blacklisted_nodes.add(n)

# Get blacklist dependents (any path node between ROOT and a blacklist node)
blacklist_dependent_nodes = set()
for b in blacklisted_nodes:
    for path in nx.all_simple_edge_paths(st.session_state['G'], 'ROOT', b):
        inbetween_edges = path[1:-1]
        inbetween_nodes = functools.reduce(set.union, inbetween_edges, set())
        for n in inbetween_nodes:
            if n not in blacklisted_nodes:
                blacklist_dependent_nodes.add(n)

sub_G_nodes = set(st.session_state['G'].nodes)
if not show_blacklist:
    sub_G_nodes -= blacklisted_nodes
if not show_blacklist_dependants:
    sub_G_nodes -= blacklist_dependent_nodes
sub_G = st.session_state['G'].subgraph(sub_G_nodes)

# Make the license node attribute as a list, so that it is JSON serializable
# Only when it is JSON serializable, it can be saved as a HTML
sub_G_node_attributes = {}
for n, licenses in sub_G.nodes(data='license'):
    if n != 'ROOT':
        sub_G_node_attributes[n] = {'license': list(licenses)}
    else:
        sub_G_node_attributes['ROOT'] = {'license': []}
nx.set_node_attributes(sub_G, sub_G_node_attributes)

g = Network(
    height='700px',
    directed=True,
    heading=''
)
g.from_nx(sub_G)

for n in g.nodes:
    nid = n['id']
    n["size"] = 100
    if nid == 'ROOT':
        n["size"] = 500
        n["label"] = "Conda environment"
        n['color'] = 'grey'
        continue
    n["font"] = {"size": 100}

    if nid in blacklist_dependent_nodes:
        n['color'] = 'orange'
        
    elif nid in blacklisted_nodes:
        n['color'] = 'red'
    

    n["title"] = sub_G.nodes(data='license')[nid]
    
for e in g.edges:
    e["width"] = 20
    e["color"] = 'black'
    e["arrowStrikethrough"] = False
    # e["label"] = 'requires'
    # e["font"] = {"size": 30}
    u, v = e['from'], e['to']
    if v in blacklist_dependent_nodes:
        e['color'] = 'orange'
    if v in blacklisted_nodes:
        e['color'] = 'red'

g.barnes_hut()
g.save_graph("graph_vis.html")
html_file = open(f'graph_vis.html', 'r', encoding='utf-8')

license_count_md = f"**{sum(license_count.values())} packages in total**. "
if show_blacklist:
    license_count_md += f'**:red[{len(blacklisted_nodes)} have blacklisted licenses.]** '
if show_blacklist_dependants:
    license_count_md += f'**:orange[{len(blacklist_dependent_nodes)} have ancestors with blacklisted licenses.]**'
st.markdown(license_count_md)
components.html(html_file.read(), height=750)