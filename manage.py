#!/usr/bin/env python3

import argparse
import os
import json
import sys
import time
from datetime import datetime
import subprocess
import yaml

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(text: str, color:bcolors = bcolors.BOLD):
    """
    Utility method to print colored text to stdout.

    :param text:        The text to print
    :param color:       The bcolors to print text in (defaults to bold)
    :return:
    """
    print(f"{color}{text}{bcolors.ENDC}")

def run_shell(cmd: str):
    """
    Runs a shell command and prints command to stdout before
    running so user can see what was run

    :param cmd:     The shell command to run
    :return:
    """
    print_color(f"** RUNNING: {cmd}")
    os.system(cmd)

# Subcommand options

def start(args):
    """
    Start a GKE Cluster with Zebrium's demo environment deployed.
    """
    print_color(f"Starting GKE cluster in project {args.project} with name {args.name} in zone {args.zone}", bcolors.OKBLUE)

    # Ensure GCloud SDK is up to date
    run_shell("gcloud components update")

    # Set GCloud project
    run_shell(f"gcloud config set project \"{args.project}\"")

    # Spinup cluster
    run_shell(f"gcloud container clusters create {args.name} --zone {args.zone} --cluster-version 1.14.10-gke.17 --machine-type n1-standard-2 --no-enable-autoupgrade")

    # Get kubectl credentials
    run_shell(f"gcloud container clusters get-credentials {args.name} --zone {args.zone}")

    print_color("\nGKE Cluster Running with following nodes:\n")
    run_shell(f"kubectl get nodes")

    # Deploy Zebrium Collector using Helm
    ze_deployment_name = "zebrium-k8s-demo"
    ze_logs_url = "https://zapi03.zebrium.com"
    ze_stats_url = "https://zapi03.zebrium.com/stats/api/v1/zstats"
    run_shell("sleep 90") # Wait 1.5 mins for cluster to finish setting up fully
    run_shell("kubectl create namespace zebrium")
    run_shell(f"helm install zlog-collector --namespace zebrium --set zebrium.deployment={ze_deployment_name},zebrium.collectorUrl={ze_logs_url},zebrium.authToken={args.key} --repo https://raw.githubusercontent.com/zebrium/ze-kubernetes-collector/master/charts zlog-collector")
    # Install Prometheus collector (EXPERIMENTAL)
    run_shell(f"helm install zstats-collector --namespace zebrium --set zebrium.deployment={ze_deployment_name},zebrium.collectorUrl={ze_stats_url},zebrium.authToken={args.key} --repo https://raw.githubusercontent.com/zebrium/ze-stats/master/charts zstats")

    # Deploy all demo apps
    run_shell("kubectl create -f ./deploy/sock-shop.yaml")
    run_shell("kubectl create -f ./deploy/random-log-counter.yaml")

    # Deploy kafka demo app
    run_shell("kubectl create namespace kafka")
    run_shell("helm repo add confluentinc https://confluentinc.github.io/cp-helm-charts/")
    run_shell("helm repo update")
    run_shell("helm install kafka-cluster --set cp-schema-registry.enabled=false,cp-kafka-rest.enabled=false,cp-kafka-connect.enabled=false,cp-control-center.enabled=false,cp-ksql-server.enabled=false confluentinc/cp-helm-charts --namespace=kafka")
    run_shell('kubectl annotate sts/kafka-cluster-cp-kafka litmuschaos.io/chaos="true" -n kafka')

    # Deploy Litmus ChaosOperator to run Experiments that create incidents
    run_shell("kubectl apply -f https://litmuschaos.github.io/pages/litmus-operator-v1.1.0.yaml")

    # Install Litmus Experiments - TEMP Workaround to set experiment versions until Chaos Hub supports in URL
    run_shell("curl -sL https://github.com/litmuschaos/chaos-charts/archive/1.1.1.tar.gz -o litmus.tar.gz")
    run_shell("tar -zxvf litmus.tar.gz")
    run_shell("rm litmus.tar.gz")
    run_shell("find chaos-charts-1.1.1 -name experiments.yaml | grep generic | xargs kubectl apply -n sock-shop -f")
    run_shell("find chaos-charts-1.1.1 -name experiments.yaml | grep kafka | xargs kubectl apply -n kafka -f")
    #run_shell("kubectl create -f https://hub.litmuschaos.io/api/chaos?file=charts/generic/experiments.yaml -n sock-shop")
    #run_shell("kubectl create -f https://hub.litmuschaos.io/api/chaos?file=charts/kafka/experiments.yaml -n kafka")

    # Create the chaos serviceaccount with permissions needed to run the generic K8s experiments
    run_shell("kubectl create -f ./deploy/litmus-rbac.yaml")

    # Get ingress IP address
    run_shell("sleep 60")  # Wait 1 min for ingress to finish setting up
    print_color("\nIngress Details:\n", bcolors.UNDERLINE)
    run_shell("kubectl get ingress basic-ingress --namespace=sock-shop")

    try:
        ingress_ip = \
        json.loads(os.popen('kubectl get ingress basic-ingress --namespace=sock-shop -o json').read())["status"][
            "loadBalancer"]["ingress"][0]["ip"]
        print_color(f"\nYou can access the web application in a few minutes at: http://{ingress_ip}")
    except:
        print_color("Ingress still being setup. Use the following command to get the IP later:", bcolors.WARNING)
        print_color("\tkubectl get ingress basic-ingress --namespace=sock-shop", bcolors.WARNING)

    print_color("***************************************************************************************************", bcolors.WARNING)
    print_color(f"* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Finished creating cluster.", bcolors.WARNING)
    print_color("* Please wait at least 15 minutes for environment to become fully initalised.")
    print_color("* The ingress to access the web application from your browser can take at least 5 minutes to create.", bcolors.WARNING)
    print_color("*", bcolors.WARNING)
    print_color("*", bcolors.WARNING)
    print_color("* IMPORTANT: To reliably detect Chaos experiment incidents you must reduce the Refactoring Period For Your Account to 10 minutes.", bcolors.WARNING)
    print_color("* You can do this under your account settings at https://portal03.zebrium.com/settings.",bcolors.WARNING)
    print_color("*", bcolors.WARNING)
    print_color("***************************************************************************************************\n\n", bcolors.WARNING)

def stop(args):
    """
    Shutdown the GKE Cluster with Zebrium's demo environment deployed.
    """
    print_color(f"Stopping GKE cluster in project {args.project} with name {args.name} in zone {args.zone}", bcolors.OKBLUE)

    # Set GCloud project
    run_shell(f"gcloud config set project \"{args.project}\"")

    # Stop cluster
    run_shell(f"gcloud container clusters delete {args.name} --zone {args.zone}")

class ExperimentResult(object):
    """
    Holds Experiment Result
    """

    def __init__(self, name:str, status:str, startTime:datetime):
        self.name = name
        self.status = status
        self.startTime = startTime

def run_experiment(experiment: str, delay: int = 0):
    """
    Run a specific experiment

    :param experiment:  The name of the experiment as defined in the YAML, i.e. container-kill
    :param ramp_time:   The number of seconds to delay experiment after setup to avoid confusing setup events with experiment events in Zebrium
    :return:            ExperimentResult object with results of experiment
    """
    print_color("***************************************************************************************************", bcolors.OKBLUE)
    print_color(f"* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Experiment: {experiment}", bcolors.OKBLUE)
    print_color("***************************************************************************************************", bcolors.OKBLUE)

    experiment_file = experiment + ".yaml"

    # Set namespace to check
    with open(f"./litmus/{experiment_file}") as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)
        result_name = spec['metadata']['name']
        namespace = spec['metadata']['namespace']

        # Create temp file with updated RAMP_TIME
        if (delay > 0):
            spec['spec']['experiments'][0]['spec']['components']['env'].append({'name': 'RAMP_TIME', 'value': str(delay)})
        with open(r"temp.yaml", 'w') as temp:
            yaml.dump(spec, temp)

    print_color(f"Running Litmus ChaosEngine Experiment {experiment_file} in namespace {namespace} with delay {delay} seconds...")
    print_color(f"Deploying {experiment_file}...")
    run_shell(f"kubectl delete chaosengine {result_name} -n {namespace}")
    run_shell(f"kubectl create -f temp.yaml -n {namespace}")

    # Check status of experiment execution
    startTime = datetime.now()
    print_color(f"{startTime.strftime('%Y-%m-%d %H:%M:%S')} Running experiment...")
    expStatusCmd = "kubectl get chaosengine " + result_name + " -o jsonpath='{.status.experiments[0].status}' -n " + namespace
    run_shell(expStatusCmd)
    logs_cmd = f"kubectl logs --since=10s -l name={experiment} -n {namespace}"
    print(f"\n{bcolors.OKGREEN}//** Experiment Logs ({logs_cmd}) **//\n\n")
    try:
        while subprocess.check_output(expStatusCmd, shell=True).decode('unicode-escape') != "Execution Successful":
            os.system(logs_cmd)
            os.system("sleep 10")

        print(f"\n\n//** End of Experiment Logs **//{bcolors.ENDC}\n")

        # View experiment results
        run_shell(f"kubectl describe chaosresult {result_name}-{experiment} -n {namespace}")

        # Delete temp file
        run_shell('rm temp.yaml')
    except:
        print_color("User has cancelled script execution.", bcolors.FAIL)
        sys.exit(2)

    # Store Experiment Result
    status = subprocess.check_output("kubectl get chaosresult " + result_name + "-" + experiment + " -n " + namespace + " -o jsonpath='{.spec.experimentstatus.verdict}'", shell=True).decode('unicode-escape')
    return ExperimentResult(experiment, status, startTime)

def test(args):
    """
    Run Litmus ChaosEngine Experiments inside Zebrium's demo environment.
    Each experiment is defined under its own yaml file under the /litmus directory. You can run
    a specific experiment by specifying a test name that matches one of the yaml file names in the directory
    but by default all '*' experiments will be run with 20 minute wait period between each experiment
    to ensure Zebrium doesn't cluster the incidents together into one incident
    """
    experiments = sorted(os.listdir('./litmus'))
    experiment_results = []

    if args.test == '*':
        # Run all experiments in /litmus directory with wait time between them
        print_color(f"Running all Litmus ChaosEngine Experiments with {args.wait} mins wait time between each one...")
        lstindex = len(experiments)
        for experiment_file in experiments:
            result = run_experiment(experiment_file.replace('.yaml', ''), args.delay)
            experiment_results.append(result)
            print_color(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Waiting {args.wait} mins before running next experiment...", bcolors.WARNING)
            lstindex -= 1
            if lstindex != 0:
                time.sleep(args.wait * 60)
    else:
        # Check experiment exists
        experiment_file = args.test + ".yaml"
        if experiment_file in experiments:
            result = run_experiment(args.test, args.delay)
            experiment_results.append(result)
        else:
            print_color(f"ERROR: {experiment_file} not found in ./litmus directory. Please check the name and try again.", bcolors.FAIL)
            sys.exit(2)

    # Print out experiment result summary
    print_color("***************************************************************************************************", bcolors.OKBLUE)
    print_color("* Experiments Result Summary", bcolors.OKBLUE)
    print_color("***************************************************************************************************\n", bcolors.OKBLUE)
    headers = ["#", "Start Time", "Experiment", "Status"]
    row_format = "{:>25}" * (len(headers) + 1)
    print_color(row_format.format("", *headers), bcolors.OKBLUE)
    i = 1
    for result in experiment_results:
        print_color(row_format.format("", str(i), result.startTime.strftime('%Y-%m-%d %H:%M:%S'), result.name, result.status), bcolors.OKBLUE)
        i += 1
    print("\n")

def list(args):
    """
    List all available Litmus Chaos Experiments available in this repository
    """
    experiments = sorted(os.listdir('./litmus'))
    print_color("Available Litmus Chaos Experiments:\n\n")
    i = 1
    for experiment_file in experiments:
        print_color(f"\t{i}. {experiment_file.replace('.yaml', '')}")
        i += 1

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
    parser_start.add_argument("-n", "--name", type=str, default="zebrium-k8s-demo",
                        help="Set GKE cluster name")
    parser_start.add_argument("-k", "--key", type=str,
                        help="Set Zebrium collector key for demo account")
    parser_start.set_defaults(func=start)

    # Test command
    parser_test = subparsers.add_parser("test", help="Run Litmus ChaosEngine Experiments inside Zebrium's demo environment.")
    parser_test.add_argument("-t", "--test", type=str, default="*",
                             help="Name of test to run based on yaml file name under /litmus folder. '*' runs all of them with wait time between each experiement.")
    parser_test.add_argument("-w", "--wait", type=int, default=11,
                             help="Number of minutes to wait between experiments. Defaults to 11 mins to avoid Zebrium clustering incidents together.")
    parser_test.add_argument("-d", "--delay", type=int, default=660,
                             help="Delay time in seconds between setting up experiment and running it. Defaults to 660 seconds.")
    parser_test.set_defaults(func=test)

    # List Tests Command
    parser_list = subparsers.add_parser("list", help="List all available Litmus ChaosEngine Experiments available to run.")
    parser_list.set_defaults(func=list)

    # Stop command
    parser_stop = subparsers.add_parser("stop", help="Shutdown the GKE Cluster with Zebrium's demo environment deployed.")
    parser_stop.add_argument("-p", "--project", type=str,
                        help="Set GCloud Project to spin GKE cluster up in")
    parser_stop.add_argument("-z", "--zone", type=str, default="us-central1-a",
                        help="Set GCloud Zone to spin GKE cluster up in")
    parser_stop.add_argument("-n", "--name", type=str, default="zebrium-k8s-demo",
                        help="Set GKE cluster name")
    parser_stop.set_defaults(func=stop)

    args = parser.parse_args()
    args.func(args)
