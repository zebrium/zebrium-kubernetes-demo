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
positional arguments:
  cmd                   'start', 'test' or 'stop' the GKE cluster

optional arguments:
  -h, --help            show this help message and exit
  -p PROJECT, --project PROJECT
                        Set GCloud Project to spin GKE cluster up in
  -z ZONE, --zone ZONE  Set GCloud Zone to spin GKE cluster up in
  -n NAME, --name NAME  Set GKE cluster name
  -k KEY, --key KEY     Set Zebrium collector key for demo account
```

## Startup

To start the GKE cluster and deploy all the required components:

```bash
./manage.py start --project {GC_PROJECT} --key {ZE_KEY}
```

## Test

To run the Litmus ChaosEngine experiments:

```bash
./manage.py test
```

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
./manage.py stop
```
