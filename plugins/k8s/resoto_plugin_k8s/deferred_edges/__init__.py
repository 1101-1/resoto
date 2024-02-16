import logging
from urllib.parse import urlparse
from typing import Optional
from resoto_plugin_k8s.deferred_edges.utils import rgetattr
from resoto_plugin_k8s.resources import KubernetesCluster
from resotolib.baseresources import BaseResource
from resotolib.graph import Graph
from resoto_plugin_k8s.deferred_edges.aws import link_all as link_all_aws
from resoto_plugin_k8s.deferred_edges.digitalocean import link_all as link_all_do
from resoto_plugin_k8s.deferred_edges.azure import link_all as link_all_azure

log = logging.getLogger("resoto.plugins.k8s")


def detect_cloud(graph: Graph) -> Optional[str]:
    if isinstance(graph.root, KubernetesCluster) and (
        server_url := rgetattr(graph.root, "cluster_info.server_url", None)
    ):
        cloud_urls = {"amazonaws.com": "AWS", "azmk8s.io": "Azure", "digitaloceanspaces.com": "DigitalOcean"}
        url_hostname = urlparse(server_url).hostname
        cloud_url = ".".join(url_hostname.split(".")[-2:])

        if cloud_url in cloud_urls:
            return cloud_urls[cloud_url]
        else:
            return None
    return None


def create_deferred_edges(graph: Graph) -> None:
    if not isinstance(graph, Graph):
        log.error(f"Expected type Graph, got {type(graph)}")
        return

    cloud = detect_cloud(graph)
    cloud_linking_functions = {"AWS": link_all_aws, "Azure": link_all_azure, "DigitalOcean": link_all_do}

    if (cloud is not None) and (cloud_link_all := cloud_linking_functions.get(cloud)):
        for node in graph.nodes:
            if not isinstance(node, BaseResource):
                log.warning(f"Node {node} is not a BaseResource")
                continue
            cloud_link_all(graph, node)
