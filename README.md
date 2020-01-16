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

## Shutdown

To shutdown and destroy the GKE cluster when you're finished:

```bash
./manage.py stop
```