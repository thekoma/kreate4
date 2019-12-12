# Configure Registry Step

oc patch sc/thin --type merge --patch '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class": "false" }}}'

oc apply -f pv.yaml
oc apply -f pvc.yaml

oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch '{"spec":{"storage":{"pvc":{"claim": ""}}}'

oc patch sc/thin --type merge --patch '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class": "true" }}}'


