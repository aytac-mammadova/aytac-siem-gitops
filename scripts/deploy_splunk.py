#!/usr/bin/env python3
"""deploy_splunk.py — Deploy SIGMA rules to Splunk via REST API"""
import os
import glob
import sys
import requests
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend

requests.packages.urllib3.disable_warnings()

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', 'https://159.89.92.178:8089')
SPLUNK_TOKEN = os.environ['SPLUNK_TOKEN']
RULES_DIR = 'splunk_rules'
HEADERS = {'Authorization': f'Bearer {SPLUNK_TOKEN}'}
BASE_URL = f'{SPLUNK_HOST}/servicesNS/admin/search/saved/searches'

backend = SplunkBackend()


def deploy_rule(yaml_path):
    name = os.path.basename(yaml_path).replace('.yml', '')
    try:
        with open(yaml_path) as f:
            yaml_content = f.read()
        collection = SigmaCollection.from_yaml(yaml_content)
        spl_queries = backend.convert(collection)
        if not spl_queries:
            print(f'⚠️  {name}: no SPL output')
            return False
        spl = spl_queries[0]
        data = {
            'name': name,
            'search': spl,
            'is_scheduled': '1',
            'cron_schedule': '*/5 * * * *',
            'dispatch.earliest_time': '-5m',
            'dispatch.latest_time': 'now',
            'description': f'SIGMA-derived alert: {name}',
        }
        r = requests.post(BASE_URL, headers=HEADERS, data=data, verify=False, timeout=30)
        if r.status_code in (200, 201):
            print(f'✅ {name} created')
            return True
        if r.status_code == 409:
            update_data = {k: v for k, v in data.items() if k != 'name'}
            ur = requests.post(f'{BASE_URL}/{name}', headers=HEADERS, data=update_data, verify=False, timeout=30)
            if ur.status_code in (200, 201):
                print(f'✅ {name} updated')
                return True
            print(f'❌ {name} update failed: {ur.status_code} {ur.text[:200]}')
            return False
        print(f'❌ {name} failed: {r.status_code} {r.text[:200]}')
        return False
    except Exception as e:
        print(f'❌ {name} exception: {e}')
        return False


def main():
    rules = sorted(glob.glob(f'{RULES_DIR}/*.yml'))
    print(f'📦 Deploying {len(rules)} rules to {SPLUNK_HOST}')
    if not rules:
        print(f'⚠️  No rules found in {RULES_DIR}/')
        sys.exit(0)
    success = 0
    for rule in rules:
        if deploy_rule(rule):
            success += 1
    print(f'\n✅ Done: {success}/{len(rules)} success')
    sys.exit(0 if success == len(rules) else 1)


if __name__ == '__main__':
    main()
