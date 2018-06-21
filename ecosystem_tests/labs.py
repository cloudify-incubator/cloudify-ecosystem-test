from datetime import datetime, timedelta
import json
import os
import requests
from time import sleep
from urlparse import urlparse


def create_lab_as_sales(description,
                        application_blueprint_name,
                        application_blueprint_id,
                        application_name,
                        timezone,
                        date,
                        duration,
                        endpoint,
                        auth_username,
                        auth_password):

    sales_lab_data = {
        "provider_selection": "cloudify",
        "description": description,
        "timezone_selection": timezone,
        "lab_date_picker": date,
        "application_blueprint_name": application_blueprint_name,
        "application_blueprint_id": application_blueprint_id,
        "duration_in_hours": duration,
        "application_name": application_name,
    }

    print 'Sending create lab request.'

    post_response = requests.post(
        endpoint + '/api-rest/lab_sales/',
        data=json.dumps(sales_lab_data),
        headers={'Content-type': 'application/json'},
        auth=(auth_username, auth_password))

    if post_response.status_code != 201:
        print 'Error'
        print post_response.text
        quit()

    while True:
        sleep(5)
        try:
            get_response = requests.get(
                post_response.json()['lab_url'],
                headers={'Content-type': 'application/json'},
                allow_redirects=True)
        except (ValueError, KeyError):
            raise
        if get_response.status_code in [200, 201]:
            break

    return json.loads(post_response.text)['lab_access_token']


def run_operation(endpoint, access_token, operation):

    print 'Executing operation {0}'.format(operation)

    response = requests.put(endpoint +
                            '/api-rest/lab_states/{}/'.format(access_token),
                            data='operation={}'.format(operation),
                            headers={'Content-type':
                                     'application/x-www-form-urlencoded'})
    if response.status_code != 200:
        print 'Error'
        print response.text
        quit()


def get_status(endpoint, access_token):

    print 'Polling status.'

    response = requests.get(endpoint +
                            '/api-rest/lab_states/{}/'.format(access_token))
    if response.status_code != 200:
        print response.text
        print 'Error'
        quit()
    return json.loads(response.text)


def run_workflow(endpoint, access_token, operations=['deploy']):

    print 'Executing workflow.'

    for operation in operations:
        run_operation(endpoint, access_token, operation)

    if 'delete' in operations:
        while True:
            print 'Checking if status is deleted.'
            sleep(5)
            status = get_status(endpoint, access_token)
            if status["status"] == "deleted":
                break
        return

    if 'deploy' in operations:
        while True:
            print 'Checking if lab has started.'
            sleep(5)
            status = get_status(endpoint, access_token)
            if status["status"] == "started":
                try:
                    lab_ui_outputs = \
                        status['outputs']['lab_ui_outputs'][0]['items']
                    for lab_ui_output in lab_ui_outputs:
                        if lab_ui_output['name'] == 'Cloudify Manager Link':
                            manager_url = lab_ui_output['value']
                    parsed_url = urlparse(manager_url)
                    if parsed_url.netloc != 'None':
                        break
                except (NameError, KeyError):
                    raise

        return parsed_url.netloc


def wait_for_manager_ready(ip_address, max_wait_seconds=300):
    start_time = datetime.now()
    finish_time = start_time + timedelta(seconds=max_wait_seconds)
    while True:
        print 'Checking if manager is ready.'
        sleep(5)
        try:
            get_response = requests.get(
                'http://{0}/'.format(ip_address), timeout=0.1)
        except requests.exceptions.Timeout:
            continue

        if get_response.status_code == 200:
            break
        elif datetime.now() > finish_time:
            raise Exception(
                'Timed out waiting for manager URL to respond.')

    print 'Manager IP ready.'


def get_datetime_string():
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M')


def create_lab():

    try:
        lab_auth_user = os.environ['LAB_USERNAME']
        lab_auth_pass = os.environ['LAB_PASSWORD']
    except KeyError:
        raise

    application_prefix = \
        os.environ.get('TEST_APPLICATION_PREFIX', 'prefix')
    test_blueprint = \
        os.environ.get(
            'TEST_BLUEPRINT',
            'Testing_CFY432_Vanilla_v15_LabCertified')
    lab_server = 'http://{0}'.format(
        os.environ.get('LAB_SERVER', 'localhost:8000'))

    lab_access_token = create_lab_as_sales(
        application_prefix,
        test_blueprint,
        test_blueprint,
        application_prefix,
        os.environ.get('LAB_TIMEZONE', 'Asia/Jerusalem'),
        os.environ.get('LAB_DATETIME', get_datetime_string()),
        os.environ.get('LAB_DURATION', '1'),
        lab_server,
        lab_auth_user,
        lab_auth_pass)

    os.environ['LAB_ACCESS_TOKEN'] = lab_access_token

    manager_ip = run_workflow(lab_server, lab_access_token)
    wait_for_manager_ready(manager_ip)
    return manager_ip


def delete_lab():
    lab_server = os.environ.get('LAB_SERVER', 'http://localhost:8000')
    lab_access_token = os.environ.get('LAB_ACCESS_TOKEN')
    if not lab_access_token:
        raise Exception('Failed to call delete.')
    run_workflow(lab_server, lab_access_token, ['undeploy', 'delete'])
