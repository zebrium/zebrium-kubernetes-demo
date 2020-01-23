#!/usr/bin/env python3

import argparse
import os
import json
import sys
import time
from datetime import datetime
import subprocess

# Subcommand options

def start(args):
    """
    Start a GKE Cluster with Zebrium's demo environment deployed.
    """
    print(f"Starting GKE cluster in project {args.project} with name {args.name} in zone {args.zone}")

    # Ensure GCloud SDK is up to date
    os.system("gcloud components update")

    # Set GCloud project
    os.system(f"gcloud config set project \"{args.project}\"")

    # Spinup cluster
    os.system(f"gcloud container clusters create {args.name} --zone {args.zone}")

    # Get kubectl credentials
    os.system(f"gcloud container clusters get-credentials {args.name} --zone {args.zone}")

    print("\nGKE Cluster Running with following nodes:\n")
    os.system(f"kubectl get nodes")

    # Deploy Zebrium Collector
    os.system(f"kubectl create secret generic zlog-collector-config --from-literal=log-collector-url=https://zapi03.zebrium.com --from-literal=auth-token={args.key}")
    os.system("kubectl create -f ./deploy/zlog-collector.yaml")

    # Deploy all demo apps
    os.system("kubectl create -f ./deploy/sock-shop.yaml")
    os.system("kubectl create -f ./deploy/random-log-counter.yaml")

    # Deploy Litmus ChaosOperator to run Experiments that create incidents
    os.system("kubectl apply -f https://litmuschaos.github.io/pages/litmus-operator-v1.0.0.yaml")

    # Install the generic K8s experiments CR
    os.system("kubectl create -f https://hub.litmuschaos.io/api/chaos?file=charts/generic/experiments.yaml -n sock-shop")

    # Create the chaos serviceaccount with permissions needed to run the generic K8s experiments
    os.system("kubectl create -f ./deploy/litmus-rbac.yaml")

    # Get ingress IP address
    print("\nIngress Details:\n")
    os.system("kubectl get ingress basic-ingress --namespace=sock-shop")

    try:
        ingress_ip = \
        json.loads(os.popen('kubectl get ingress basic-ingress --namespace=sock-shop -o json').read())["status"][
            "loadBalancer"]["ingress"][0]["ip"]
        print(f"\nYou can access the web application in a few minutes at: http://{ingress_ip}")
    except:
        print("Ingress still being setup. Use the following command to get the IP later:")
        print("\tkubectl get ingress basic-ingress --namespace=sock-shop")

    print("\nFinished creating cluster. Please wait a few minutes for environment to become fully initalised.")
    print("The ingress to access the web application from your browser can take at least 5 minutes to create.")

def stop(args):
    """
    Shutdown the GKE Cluster with Zebrium's demo environment deployed.
    """
    print(f"Stopping GKE cluster in project {args.project} with name {args.name} in zone {args.zone}")

    # Set GCloud project
    os.system(f"gcloud config set project \"{args.project}\"")

    # Stop cluster
    os.system(f"gcloud container clusters delete {args.name} --zone {args.zone}")

class ExperimentResult(object):
    """
    Holds Experiment Result
    """

    def __init__(self, name:str, status:str, startTime:datetime):
        self.name = name
        self.status = status
        self.startTime = startTime

def run_experiment(experiment: str):
    """
    Run a specific experiment

    :param experiment:  The name of the experiment as defined in the YAML, i.e. container-kill
    :return:            ExperimentResult object with results of experiment
    """
    print("***************************************************************************************************")
    print(f"* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Experiment: {experiment}")
    print("***************************************************************************************************")

    experiment_file = experiment + ".yaml"
    print(f"Running Litmus ChaosEngine Experiment {experiment_file}")
    print(f"Deploying {experiment_file}...")
    os.system("kubectl delete chaosengine sock-chaos -n sock-shop")
    os.system(f"kubectl create -f ./litmus/{experiment_file}")

    # Check status of experiment execution
    startTime = datetime.now()
    print(f"{startTime.strftime('%Y-%m-%d %H:%M:%S')} Running experiment...")
    expStatusCmd = "kubectl get chaosengine sock-chaos -o jsonpath='{.status.experiments[0].status}' -n sock-shop"
    while subprocess.check_output(expStatusCmd, shell=True).decode('unicode-escape') != "Execution Successful":
        print(".")
        os.system("sleep 10")

    # View experiment results
    print(f"\nkubectl describe chaosresult sock-chaos-{experiment} -n sock-shop")
    os.system(f"kubectl describe chaosresult sock-chaos-{experiment} -n sock-shop")

    # Store Experiment Result
    status = subprocess.check_output("kubectl get chaosresult sock-chaos-" + experiment + " -n sock-shop -o jsonpath='{.spec.experimentstatus.verdict}'", shell=True).decode('unicode-escape')
    return ExperimentResult(experiment, status, startTime)

def test(args):
    """
    Run Litmus ChaosEngine Experiments inside Zebrium's demo environment.
    Each experiment is defined under its own yaml file under the /litmus directory. You can run
    a specific experiment by specifying a test name that matches one of the yaml file names in the directory
    but by default all '*' experiments will be run with 20 minute wait period between each experiment
    to ensure Zebrium doesn't cluster the incidents together into one incident
    """
    experiments = os.listdir('./litmus')
    experiment_results = []

    if args.test == '*':
        # Run all experiments in /litmus directory with wait time between them
        print(f"Running all Litmus ChaosEngine Experiments with {args.wait} mins wait time between each one...")
        for experiment_file in experiments:
            result = run_experiment(experiment_file.replace('.yaml', ''))
            experiment_results.append(result)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Waiting {args.wait} mins before running next experiment...")
            time.sleep(args.wait * 60)
    else:
        # Check experiment exists
        experiment_file = args.test + ".yaml"
        if experiment_file in experiments:
            result = run_experiment(args.test)
            experiment_results.append(result)
        else:
            print(f"ERROR: {experiment_file} not found in ./litmus directory. Please check the name and try again.")
            sys.exit(2)

    # Print out experiment result summary
    print("***************************************************************************************************")
    print(f"* Experiments Result Summary")
    print("***************************************************************************************************\n")
    headers = ["#", "Start Time", "Experiment", "Status"]
    row_format = "{:>25}" * (len(headers) + 1)
    print(row_format.format("", *headers))
    i = 1
    for result in experiment_results:
        print(row_format.format("", str(i), result.startTime.strftime('%Y-%m-%d %H:%M:%S'), result.name, result.status))
        i += 1
    print("\n")

if __name__ == "__main__":

    # Add command line arguments
    parser = argparse.ArgumentParser(description='Spin up Zebrium Demo Environment on Kubernetes.')
    subparsers = parser.add_subparsers()

    # Start command
    parser_start = subparsers.add_parser("start", help="Start a GKE Cluster with Zebrium's demo environment deployed.")
    parser_start.add_argument("-p", "--project", type=str,
                        help="Set GCloud Project to spin GKE cluster up in")
    parser_start.add_argument("-z", "--zone", type=str, default="us-central1-a",
                        help="Set GCloud Zone to spin GKE cluster up in")
    parser_start.add_argument("-n", "--name", type=str, default="zebrium-demo-gke",
                        help="Set GKE cluster name")
    parser_start.add_argument("-k", "--key", type=str,
                        help="Set Zebrium collector key for demo account")
    parser_start.set_defaults(func=start)

    # Test command
    parser_test = subparsers.add_parser("test", help="Run Litmus ChaosEngine Experiments inside Zebrium's demo environment.")
    parser_test.add_argument("-t", "--test", type=str, default="*",
                             help="Name of test to run based on yaml file name under /litmus folder. '*' runs all of them with wait time between each experiement.")
    parser_test.add_argument("-w", "--wait", type=int, default=15,
                             help="Number of minutes to wait between experiments. Defaults to 20 mins to avoid Zebrium clustering incidents together.")
    parser_test.set_defaults(func=test)

    # Stop command
    parser_stop = subparsers.add_parser("stop", help="Shutdown the GKE Cluster with Zebrium's demo environment deployed.")
    parser_stop.add_argument("-p", "--project", type=str,
                        help="Set GCloud Project to spin GKE cluster up in")
    parser_stop.add_argument("-z", "--zone", type=str, default="us-central1-a",
                        help="Set GCloud Zone to spin GKE cluster up in")
    parser_stop.add_argument("-n", "--name", type=str, default="zebrium-demo-gke",
                        help="Set GKE cluster name")
    parser_stop.set_defaults(func=stop)

    args = parser.parse_args()
    args.func(args)
