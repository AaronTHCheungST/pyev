import networkx as nx
import requests
import streamlit as st

def list_packages(deptree_json_package_list, add_root=True):
    # List all the packages (node)
    # Node has the format f"{package_name}=={installed_version}"
    result = []
    for package in deptree_json_package_list:
        match package:
            case {'package': {'package_name': package_name, 'installed_version': installed_version}}:
                result.append(f"{package_name}=={installed_version}")
    if add_root:
        result.append("ROOT")
    return result


def list_dependencies(deptree_json_package_list, add_root=True):
    # List all the dependencies edges (child, parent)
    result = []
    for package in deptree_json_package_list:
        match package:
            case {'package': {'package_name': package_name, 'installed_version': installed_version}, 
                  'dependencies': dependencies} if len(dependencies) > 0:
                child = f"{package_name}=={installed_version}"
                dependency_parents = list_packages([{'package': d} for d in dependencies], add_root=False)
                result.extend([(
                    # child depends on parent
                    child,  # Source/child
                    parent  # Target/parent
                ) for parent in dependency_parents])
                if add_root:
                    result.append((
                        "ROOT",
                        child
                    ))
    return result

@st.cache_data
def package_license(package_name, version=None, retries=3):
    # return the license of a package at a version
    # if version is None, just return the license of the latest version
    if package_name == 'ROOT': return None
    if retries >= 1:
        version_string = ""
        if version is not None:
            version_string = f"{version}/"
        url = f"https://pypi.org/pypi/{package_name}/{version_string}json"
        response = requests.get(url)

        if response.status_code == 200:
            licenses_set = set()
            response_json = response.json()
            package_info = response_json['info']
            
            # Check info.classifiers
            if 'classifiers' in package_info:
                license_classifiers = [x for x in package_info['classifiers'] if x.startswith('License')]
                if len(license_classifiers) > 0:
                    licenses = [x.split(' :: ')[-1] for x in license_classifiers]
                    licenses = [x for x in licenses if x!='OSI Approved']
                    licenses_set.update(licenses)
            
            # Check info.license
            if 'license' in package_info:
                license_text = package_info['license']
                if license_text and len(license_text) <=12:
                    license = license_text
                    licenses_set.add(license)

            # Check info.license_expression
            if 'license_expression' in package_info:
                license_expression = package_info['license_expression']
                if license_expression and len(license_expression) <= 12:
                    license = license_expression
                    licenses_set.add(license)

            if len(licenses_set) > 0:
                return licenses_set
            else:
                return None
        else:
            return package_license(package_name, version, retries-1)
    else:
        return None

def pipdeptree2nx(deptree_json_package_list):
    V = list_packages(deptree_json_package_list, add_root=True)
    E = list_dependencies(deptree_json_package_list, add_root=True)

    G = nx.DiGraph()
    G.add_nodes_from(V)
    G.add_edges_from(E)

    return G

def nx_fill_license(G):
    node_attributes = {}
    for n in G.nodes:
        if n == 'ROOT': continue
        license = package_license(*n.split("=="), retries=3)
        if license is not None:
            node_attributes[n] = {'license': license}
        else:
            node_attributes[n] = {'license': {"UNKNOWN"}}
    nx.set_node_attributes(G, node_attributes)

license_aliases = {
    'MIT License': ('MIT', 'MIT License'),
    'BSD License': ('BSD', 'BSD License')
}

def nx_unify_license(G):
    node_attributes = {}
    for n, licenses in G.nodes(data='license'):
        if n == 'ROOT': continue
        curr_unified_licenses = set()
        for license in licenses:
            alias = license
            for k, v in license_aliases.items():
                if alias in v:
                    alias = k
                    break
            curr_unified_licenses.add(alias)
        node_attributes[n] = {'license': curr_unified_licenses}
    nx.set_node_attributes(G, node_attributes)

def nx_license_set(G):
    license_set = set()
    for n, licenses in G.nodes(data='license'):
        if n == 'ROOT': continue
        license_set.update(licenses)
    return license_set

def nx_count_licenses(G):
    license2count = {
        license: 0 for license in nx_license_set(G)
    }
    for n, licenses in G.nodes(data='license'):
        if n == 'ROOT': continue
        for license in licenses:
            license2count[license] += 1
    return license2count