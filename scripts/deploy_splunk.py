#!/usr/bin/env python3
"""deploy_splunk.py — Deploy SIGMA rules to Splunk via REST API"""
import os
import glob
import requests
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
from urllib.parse import quote

requests.packages.urllib3.disable_warnings()

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', 'https://159.89.92.178:8089')
SPLUNK_TOKEN = os.environ['SPLUNK_TOKEN']
RULES_DIR = 'splunk_rules'
HEADERS = {'Authorization': f'Bearer {SPLUNK_TOKEN}'}

backend = SplunkBackend()
