import json
from package_utils import pipdeptree2nx, nx_fill_license, nx_unify_license
import pickle

deptreejson_filepath = 'example_deptree.json'
targetpickle_filepath = 'example_nx.pickle'

with open(deptreejson_filepath) as f:
    data = json.load(f)
G = pipdeptree2nx(data)
nx_fill_license(G)
nx_unify_license(G)
pickle.dump(G, open(targetpickle_filepath,'wb'))