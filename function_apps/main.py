#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "MICHAL53Q"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import os
import urllib3
import requests
import argparse
import xmltodict
from azure.identity import ClientSecretCredential
from azure.mgmt.web import WebSiteManagementClient


def get_client(subscription: str, tenant: str, client_id: str, client_secret: str) -> WebSiteManagementClient:
    credential = ClientSecretCredential(tenant, client_id, client_secret)
    return WebSiteManagementClient(credential, subscription)


def get_deployment_publish_profile(client: WebSiteManagementClient, resource_group_name: str, function_app_name: str) -> dict:
    content = client.web_apps.list_publishing_profile_xml_with_secrets(resource_group_name, function_app_name, {"format": "WebDeploy"})
    full_xml = ''
    for f in content:
        full_xml += f.decode()

    profiles = xmltodict.parse(full_xml, xml_attribs=True)['publishData']['publishProfile']
    converted = []

    if not isinstance(profiles, list):
        profiles = [profiles]

    for profile in profiles:
        new = {}
        for key in profile:
            # strip the leading '@' xmltodict put in for attributes
            new[key.lstrip('@')] = profile[key]
        converted.append(new)

    return next((profile for profile in converted if profile['publishMethod'] == "ZipDeploy"), None)


def deploy_zip(publish_profile: dict, path: str) -> None:
    publish_url = publish_profile['publishUrl']
    publish_user_name = publish_profile['userName']
    publish_user_password = publish_profile['userPWD']

    deployment_url = "https://" + publish_url + '/api/zipdeploy'

    authorization = urllib3.util.make_headers(basic_auth=f'{publish_user_name}:{publish_user_password}')
    headers = authorization
    headers['Content-Type'] = "application/zip"

    if os.path.exists(path) is False:
        sys.exit(f'Path: "{path}" doesn\'t exist.')

    with open(os.path.realpath(path), 'rb') as fs:
        zip_content = fs.read()
        print(f'Deployment started | path: {path}')
        res = requests.post(deployment_url, data=zip_content, headers=headers)
        if res.status_code not in [200]:
            sys.exit(f'Deployment failed with status code: {res.status_code} | error: {res.content}')

        print(f'Deployment finished with status code: {res.status_code}')


def sync_function_app_triggers(client: WebSiteManagementClient, resource_group_name: str, function_app_name: str) -> None:
    print(f'Syncing triggers...')

    try:
        client.web_apps.sync_function_triggers(resource_group_name, function_app_name)
    except Exception as e:
        # Workaround...
        false_error = "Operation returned an invalid status 'OK'"
        if e.args[0] != false_error:
            sys.exit(f'Error during syncing triggers, exception: {e}')

    print(f'Triggers synced successfully')


def main(args):
    # Initialize args
    path = args.path
    function_app_name = args.function_app_name
    resource_group_name = args.resource_group_name
    subscription = args.subscription
    tenant = args.tenant
    client_id = args.client_id
    client_secret = args.client_secret

    # Init client
    client = get_client(subscription, tenant, client_id, client_secret)

    # Get deployment publish profile
    publish_profile = get_deployment_publish_profile(client, resource_group_name, function_app_name)

    # Deploy Function App
    deploy_zip(publish_profile, path)

    # Sync triggers
    sync_function_app_triggers(client, resource_group_name, function_app_name)


if __name__ == "__main__":
    #  This is executed when run from the command line
    parser = argparse.ArgumentParser()

    requiredNamed = parser.add_argument_group('required named arguments')

    requiredNamed.add_argument("-rg", "--resource_group_name", dest="resource_group_name", help="Resource Group name", required=True)
    requiredNamed.add_argument("-n", "--name", dest="function_app_name", help="Function App name", required=True)
    requiredNamed.add_argument("-p", "--path", dest="path", help="Path to directory or JSON template", required=True)

    # Azure Auth
    requiredNamed.add_argument("--subscription", dest="subscription", help="[Azure] Subscription ID", required=True)
    requiredNamed.add_argument("--tenant", dest="tenant", help="[Azure] Tenant ID", required=True)
    requiredNamed.add_argument("--client_id", dest="client_id", help="[Azure] Client ID", required=True)
    requiredNamed.add_argument("--client_secret", dest="client_secret", help="[Azure] Client Secret", required=True)

    args = parser.parse_args()
    main(args)
