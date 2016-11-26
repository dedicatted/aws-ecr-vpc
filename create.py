from stack.template import template
from stack.vpc import vpc_id
from stack.cluster.infrastructure import main_cluster
from stack.cluster.mongo import mongo_instance
from stack.cluster.main import bigid_task_definition

print(template.to_json())