# Appunti
I need to intercept the clusteroperator status to patch the registry:
```bash
oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch '{"spec":{"storage":{"emptyDir":{}}}}'
```

