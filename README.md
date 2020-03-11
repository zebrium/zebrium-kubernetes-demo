# Zebrium Kubernetes Demo Environment

The purpose of this repository is to make it easy to spin up a fully deployed [GKE](https://cloud.google.com/kubernetes-engine/) cluster with a microservice application 
[Sock Shop](https://github.com/microservices-demo/microservices-demo), Kafka and 
[Litmus Chaos Engine](https://litmuschaos.io/) to create incident scenarios for testing [Zebrium's](https://www.zebrium?utm_campaign=Sign-up&utm_source=github) 
[Autonomous Monitoring Tool](https://www.zebrium.com/blog/the-future-of-monitoring-is-autonomous?utm_campaign=Sign-up&utm_source=github).

For more background, please read [Using Autonomous Monitoring with Litmus Chaos Engine on Kubernetes](https://www.zebrium.com/blog/using-autonomous-monitoring-with-litmus-chaos-engine-on-kubernetes?utm_campaign=Chaos&utm_source=chaos&utm_medium=github).

![Deployed Services](https://www.zebrium.com/hs-fs/hubfs/Zebrium%20and%20Litmus%20Chaos%20Engine%20components.png?width=1461&name=Zebrium%20and%20Litmus%20Chaos%20Engine%20components.png)

After cloning this repository, installing the requirements listed below, and using the `start` command to create the fully deployed cluster, you will be able to run Litmus Chaos experiments using the 
`test` command in the cluster and get more insight into the failures using Zebrium's unsupervised Machine Learning which will detect incidents 
and their root cause created by the Litmus experiments.

This repositry is also a reference for configuring and running Litmus Chaos Engine experiments, and you can find all the experiment configuration
under the `/litmus` directory of this repository and the script to deploy and run them in `manage.py`.

It currently only works with GKE so you will need a Google Cloud account to run this environment, but support for Amazon and Azure is planned in future.

## Requirements

1. Python 3.7 or above
1. Python Dependencies: `pip install -r requirements.txt`
1. Free Zebrium account to collect logs: [https://www.zebrium.com](https://www.zebrium.com/sign-up?utm_campaign=Chaos&utm_source=chaos&utm_medium=github)
1. Google Cloud Login: https://console.cloud.google.com/
1. GCloud CLI installed locally and logged in: https://cloud.google.com/sdk/docs/quickstarts
1. Kubectl installed locally: https://kubernetes.io/docs/tasks/tools/install-kubectl/
1. Helm installed locally: https://helm.sh/docs/intro/install/

**_IMPORTANT: Before running the Chaos Experiments you will also need to adjust the Refactory Period in your Advanced Account Settings
to 10 minutes. This is because the experiments run close together in succession which is not how real world incidents occur and stops multiple experiments
being grouped into one incident in Zebrium. You can adjust it at [https://portal03.zebrium.com/Settings/advanced](https://portal03.zebrium.com/Settings/advanced)._**

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
  {start,test,list,stop}
    start               Start a GKE Cluster with Zebrium's demo environment
                        deployed.
    test                Run Litmus ChaosEngine Experiments inside Zebrium's
                        demo environment.
    list                List all available Litmus ChaosEngine Experiments
                        available to run.
    stop                Shutdown the GKE Cluster with Zebrium's demo
                        environment deployed.
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
1. **disk-fill**: https://docs.litmuschaos.io/docs/disk-fill
1. **kafka-broker-pod-failure**: https://docs.litmuschaos.io/docs/kafka-broker-pod-failure/
1. **pod_delete**: https://docs.litmuschaos.io/docs/pod-delete
1. **pod-network-corruption**: https://docs.litmuschaos.io/docs/pod-network-corruption

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

## List

Lists all the available Litmus Chaos Experiments in this repo under the `./litmus` directory:

```bash
./manage.py list
```

## Shutdown

To shutdown and destroy the GKE cluster when you're finished:

```bash
./manage.py stop --project {GC_PROJECT}
```
