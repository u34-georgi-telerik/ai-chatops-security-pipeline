# custom_policies/k8s_resource_limits.py
from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check

class ResourceLimitsCheck(BaseK8Check):
    def __init__(self):
        name = "Ensure Resource Limits are set"
        id = "CKV_K8S_CUSTOM_1"
        supported_kind = ['Deployment', 'StatefulSet']
        categories = [CheckCategories.KUBERNETES]
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def get_resource_spec(self, conf):
        if conf['kind'] in self.supported_kind:
            if "spec" in conf:
                if "template" in conf["spec"]:
                    if "spec" in conf["spec"]["template"]:
                        return conf["spec"]["template"]["spec"]
        return None

    def scan_spec_conf(self, conf):
        spec = self.get_resource_spec(conf)
        
        if spec and "containers" in spec:
            for container in spec["containers"]:
                if "resources" not in container or \
                   "limits" not in container["resources"]:
                    return CheckResult.FAILED
                
        return CheckResult.PASSED
