from stack.template import template
from stack.vpc import vpc
from stack.cluster.infrastructure import main_cluster
from stack.cluster.mongo import mongo_instance
#from stack.cluster.main import container_instance_configuration

print(template.to_json())