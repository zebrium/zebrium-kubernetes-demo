#!/usr/bin/env python3

import argparse
import os
import json

if __name__ == "__main__":

    # Add command line arguments
    parser = argparse.ArgumentParser(description='Spin up Zebrium Demo Environment on Kubernetes.')

    parser.add_argument("cmd", help="'start', 'test' or 'stop' the GKE cluster")
    parser.add_argument("-p", "--project", type=str,
                        help="Set GCloud Project to spin GKE cluster up in")
    parser.add_argument("-z", "--zone", type=str, default="us-central1-a",
                        help="Set GCloud Zone to spin GKE cluster up in")
    parser.add_argument("-n", "--name", type=str, default="zebrium-demo-gke",
                        help="Set GKE cluster name")
    parser.add_argument("-k", "--key", type=str,
                        help="Set Zebrium collector key for demo account")
    args = parser.parse_args()


    if args.cmd == "start":

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
        #os.system("kubectl create -f ./deploy/random-log-counter.yaml")

        # Deploy Litmus ChaosEngine to run Experiments that create incidents
        os.system("kubectl apply -f https://litmuschaos.github.io/pages/litmus-operator-v1.0.0.yaml")
        os.system("kubectl create -f https://hub.litmuschaos.io/api/chaos?file=charts/generic/experiments.yaml")
        os.system("kubectl create -f ./litmus/rbac.yaml")

        # Get ingress IP address
        print("\nIngress Details:\n")
        os.system("kubectl get ingress basic-ingress --namespace=sock-shop")

        try:
            ingress_ip = json.loads(os.popen('kubectl get ingress basic-ingress --namespace=sock-shop -o json').read())["status"]["loadBalancer"]["ingress"][0]["ip"]
            print(f"\nYou can access the web application in a few minutes at: http://{ingress_ip}")
        except:
            print("Ingress still being setup. Use the following command to get the IP later:")
            print("\tkubectl get ingress basic-ingress --namespace=sock-shop")

        print("\nFinished creating cluster. Please wait a few minutes for environment to become fully initalised.")
        print("The ingress to access the web application from your browser can take at least 5 minutes to create.")

    elif args.cmd == "stop":

        print(f"Stopping GKE cluster in project {args.project} with name {args.name} in zone {args.zone}")

        # Set GCloud project
        os.system(f"gcloud config set project \"{args.project}\"")

        # Stop cluster
        os.system(f"gcloud container clusters delete {args.name} --zone {args.zone}")

    elif args.cmd == "test":

        print("Starting Litmus ChaosEngine Experiments...")
        # Deploy experiments
        os.system("kubectl create -f ./litmus/chaosengine.yaml")
        # View experiment results
        print("kubectl describe chaosresult sock-chaos-container-delete -n sock-shop")
        os.system("kubectl describe chaosresult sock-chaos-container-delete -n sock-shop")
    else:
        print(f"The commnad '{args.cmd}' is not recognised. Supported commands are 'start' and 'stop'.")
