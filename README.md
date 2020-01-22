# Zebrium Kubernetes Demo Environment

This repository contains all the scripts required to spin up a GKE cluster with a microservice application 
[Sock Shop](https://github.com/microservices-demo/microservices-demo) running in the cluster with 
[Litmus](https://litmuschaos.io/) to create incident scenarios for testing [Zebrium's](https://www.zebrium) 
Autonomous Log Monitoring Tool.

It currently only works with [GKE](https://cloud.google.com/kubernetes-engine/) so you will need a Google Cloud
account to run this environment, but support for Amazon and Azure is planned in future.

## Requirements

1. Python 3.7 or above
1. Google Cloud Login: https://console.cloud.google.com/
1. GCloud CLI installed locally and logged in: https://cloud.google.com/sdk/docs/quickstarts
1. Kubectl installed locally: https://kubernetes.io/docs/tasks/tools/install-kubectl/

## Usage

To see full command line options use the `-h` flag:

```bash
./manage.py -h
```

This will output the following:

```bash
usage: manage.py [-h] {start,test,stop} ...

Spin up Zebrium Demo Environment on Kubernetes.

positional arguments:
  {start,test,stop}
    start            Start a GKE Cluster with Zebrium's demo environment
                     deployed.
    test             Run Litmus ChaosEngine Experiments inside Zebrium's demo
                     environment.
    stop             Shutdown the GKE Cluster with Zebrium's demo environment
                     deployed.
```

## Startup

To start the GKE cluster and deploy all the required components:

```bash
./manage.py start --project {GC_PROJECT} --key {ZE_KEY}
```

## Test

To run all the Litmus ChaosEngine experiments:

```bash
./manage.py test
```
You can optionaly add the `--wait=` argument to change the wait time between experiments in minutes. By default
it is 20 minutes to ensure Zebrium doesn't cluster incidents together into a single incident.

To run a specific experiment (found under the ./litmus directory):

```bash
./manage.py test --test=container-kill
```

### Available Experiments

1. **container-kill**: https://docs.litmuschaos.io/docs/container-kill
1. **cpu-hog**: https://docs.litmuschaos.io/docs/cpu-hog
1. **disk-fill**: https://docs.litmuschaos.io/docs/disk-fill
1. **pod-cpu-hog**: https://docs.litmuschaos.io/docs/pod-cpu-hog
1. **pod_delete**: https://docs.litmuschaos.io/docs/pod-delete
1. **pod-network-corruption**: https://docs.litmuschaos.io/docs/pod-network-corruption
1. **pod-network-latency**: https://docs.litmuschaos.io/docs/pod-network-latency
1. **pod-network-loss**: https://docs.litmuschaos.io/docs/pod-network-loss

### Notes

- To view application deployment picked, success/failure of reconcile operations (i.e., creation of chaos-runner pod or lack thereof), check
the chaos operator logs. Ex:

```bash
kubectl logs -f chaos-operator-ce-6899bbdb9-jz6jv -n litmus  
```

- To view the parameters with which the experiment job is created, status of experiment, success of chaosengine patch operation and cleanup of 
the experiment pod, check the logs of the chaos-runner pod. Ex:

```bash
kubectl logs sock-chaos-runner -n sock-shop
```

- To view the logs of the chaos experiment itself, use the value `retain` in `.spec.jobCleanupPolicy` of the chaosengine CR

```bash
kubectl logs container-kill-1oo8wv-85lsl -n sock-shop
```

- To re-run the chaosexperiment, cleanup and re-create the chaosengine CR

```bash
kubectl delete chaosengine sock-chaos -n sock-shop
kubectl apply -f litmus/chaosengine.yaml 
```

## Shutdown

To shutdown and destroy the GKE cluster when you're finished:

```bash
./manage.py stop --project {GC_PROJECT}
```
