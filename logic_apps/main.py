#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "MICHAL53Q"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import os
import time
import json
import argparse
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode, Deployment, DeploymentExtended
from azure.core.polling import LROPoller


def get_template(logic_app_name: str, logic_app_location: str, template_path: str) -> dict:
    with open(template_path, 'r', encoding='utf-8') as file:
        template = json.load(file)

    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {},
        "variables": {},
        "resources": [
            {
                "type": "Microsoft.Logic/workflows",
                "apiVersion": "2017-07-01",
                "name": logic_app_name,
                "location": logic_app_location,
                "properties": template
            }
        ]
    }


def get_client(subscription: str, tenant: str, client_id: str, client_secret: str) -> ResourceManagementClient:
    credential = ClientSecretCredential(tenant, client_id, client_secret)
    return ResourceManagementClient(credential, subscription)


def deploy(client: ResourceManagementClient, resource_group_name: str, logic_app_name: str, template_path: str) -> LROPoller[DeploymentExtended]:
    print(f'Deployment started | Name: {logic_app_name}')

    # Get Logic App
    list_logic_apps = list(client.resources.list_by_resource_group(resource_group_name, f'name eq \'{logic_app_name}\''))

    # Check if LogicApp exists
    if len(list_logic_apps) == 0:
        sys.exit(f'Logic App "{logic_app_name}" doesn\'t exists.')

    # Get LogicApp location for template
    logic_app_location = list_logic_apps[0].location

    # Start deploying
    return client.deployments.begin_create_or_update(
        resource_group_name,
        f'python_logic_apps_{__version__}',
        Deployment(
            properties={
                'mode': DeploymentMode.incremental,
                'template': get_template(logic_app_name, logic_app_location, template_path)
            }
        )
    )


def deploy_multiple(client: ResourceManagementClient, resource_group_name: str, logic_apps: list) -> None:
    # Start deploying Logic Apps
    deployments = []
    for logic_app in logic_apps:
        logic_app_name = logic_app['name']
        template_path = logic_app['template_path']

        deployments.append({'name': logic_app_name, 'deployment': deploy(client, resource_group_name, logic_app_name, template_path)})

    # Check deployment statuses
    total_deployments = len(deployments)
    while len(deployments) > 0:
        for index, deployment in enumerate(deployments):
            deployment_name = deployment["name"]
            deployment_status = deployment['deployment'].status()

            if deployment_status == "Succeeded":
                print(f'Deployment success | Name: {deployment_name}')
                deployments.pop(index)
            elif deployment_status == "Failed":
                sys.exit(f'Deployment failed | Name: {deployment_name}')

        print(f'Deployments still running | Status: [{total_deployments - len(deployments)}/{total_deployments}]')
        time.sleep(5)


def deploy_single(client: ResourceManagementClient, resource_group_name: str, logic_app_name: str, template_path: str) -> None:
    # Start deployment
    deployment = deploy(client, resource_group_name, logic_app_name, template_path)

    # Wait for finish
    deployment.wait()

    # Check status
    if deployment.status() == "Succeeded":
        print(f'Deployment success | Name: {logic_app_name}')
    elif deployment.status() == "Failed":
        sys.exit(f'Deployment failed | Name: {logic_app_name}')


def main(args):
    # Initialize args
    path = args.path
    resource_group_name = args.resource_group_name
    subscription = args.subscription
    tenant = args.tenant
    client_id = args.client_id
    client_secret = args.client_secret

    # Check if path exists
    if os.path.exists(path) is False:
        sys.exit(f'Path: "{path}" doesn\'t exist.')

    # Init client
    client = get_client(subscription, tenant, client_id, client_secret)

    # Check path type
    if os.path.isdir(path):
        logic_apps = []
        for root, _, files in os.walk(path):
            for name in files:
                if name.endswith((".json")):
                    logic_app_name = name[0:-5]
                    template_path = os.path.join(root, name)

                    logic_apps.append({
                        'name': logic_app_name,
                        'template_path': template_path
                    })

        deploy_multiple(client, resource_group_name, logic_apps)

    elif os.path.isfile(path):
        if not path.endswith(".json"):
            sys.exit(f'File: "{path}" has invalid type, only \'.json\' is supported.')

        logic_app_name = os.path.basename(path)[0:-5]
        template_path = path

        deploy_single(client, resource_group_name, logic_app_name, template_path)


if __name__ == "__main__":
    #  This is executed when run from the command line
    parser = argparse.ArgumentParser()

    requiredNamed = parser.add_argument_group('required named arguments')

    requiredNamed.add_argument("-p", "--path", dest="path", help="Path to directory or JSON template", required=True)
    requiredNamed.add_argument("-rg", "--resource_group_name", dest="resource_group_name", help="Resource Group name", required=True)

    # Azure Auth
    requiredNamed.add_argument("--subscription", dest="subscription", help="[Azure] Subscription ID", required=True)
    requiredNamed.add_argument("--tenant", dest="tenant", help="[Azure] Tenant ID", required=True)
    requiredNamed.add_argument("--client_id", dest="client_id", help="[Azure] Client ID", required=True)
    requiredNamed.add_argument("--client_secret", dest="client_secret", help="[Azure] Client Secret", required=True)

    args = parser.parse_args()
    main(args)
