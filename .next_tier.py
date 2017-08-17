#!/usr/bin/env python
#
# A simple Python wrapper to execute multiple Ansible playbooks in succession.
#
# Accepts the following options:
#   -u <user>: remote user name
#   -s <testnames>: tests which should be skipped
#   -t <tags>: tags which should be skipped
#
# Results are stored in the local directory in the format:
#
#   <testname>_<timestamp in seconds>.log
#
# Failed test names are written out to a file named 'failed'
#
# Currently lacks support for:
#   - different options per test
#   - reset of system to original state in case of failure
#   - input validation, error handling
#
import argparse
import subprocess
import sys
import time

parser = argparse.ArgumentParser(description='Run the next tier tests')
parser.add_argument('-u', dest='user', default='',
                    help='Username to use on remote host')
parser.add_argument('-s', '--skip-tests', dest='skiptests', default='',
                    help='Comma separated list of tests to skip')
parser.add_argument('-t', '--skip-tags', dest='skiptags', default='',
                    help='Comma separated list of tags to skip')
parser.add_argument('inventory',
                    help='Path to inventory file')
args = parser.parse_args()

# we purposely omit some tests here because they have extra resource
# requirements
next_tests = ['admin-unlock', 'docker', 'docker-build-httpd',
              'docker-swarm', 'k8-cluster', 'pkg-layering',
              'rpm-ostree', 'system-containers']

skipped_tests = []
skipped_tags = ''

ansible_cmd_list = ["ansible-playbook", "-v", "-i", args.inventory]

if args.skiptests:
    skipped_tests = args.skiptests.split(',')

if args.user:
    ansible_cmd_list.append("-u")
    ansible_cmd_list.append(args.user)

if args.skiptags:
    ansible_cmd_list.append('--skip-tags')
    ansible_cmd_list.append(args.skiptags)

for test in next_tests:
    if test not in skipped_tests:
        now = str(int(time.time()))
        filename = "_".join((test, now)) + ".log"
        with open(filename, 'w') as logfile:
            test_path = 'tests/' + test + '/main.yml'
            ansible_cmd_list.append(test_path)

            print ansible_cmd_list
            # h/t https://stackoverflow.com/a/34604684
            p = subprocess.Popen(ansible_cmd_list, stdout=subprocess.PIPE, bufsize=1)
            with p.stdout:
                for line in iter(p.stdout.readline, b''):
                    print line,
                    logfile.write(line)
            p.wait()

            if p.returncode != 0:
                with open('failed', 'a') as failfile:
                    failfile.write(test + '\n')

            # pop the test name off the list to get ready for the next test
            ansible_cmd_list.pop()

