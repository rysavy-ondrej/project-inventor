# Continuous test execution environment

The testbed will be deployed using Docker Compose with shell scripting as the simplest and most efficient option. This will allow for easy management of test execution, logging, and data collection.

The provided reference Docker environment will contain scripts for:

* Executing the tests by running script run_monitor.sh to be provided by the test's author. Each batch of tests will be specified using run_monitor.sh and the folder containing the individual input JSON file to configure the test.
* The Docker container will be deployed, and these scripts will be regularly executed.
* The output will be regularly copied to a mapped folder.