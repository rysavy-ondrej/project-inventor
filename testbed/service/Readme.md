# Running testbed as service

To run the testbes schedules as a service follow the steps:

## Create a systemd service to run the tests

Create /etc/systemd/system/capture-tap.service:

```bash
[Unit]
Description=Run the inventor tests specified in the run all script.
After=network.target

[Service]
ExecStartPre=/root/project-inventor/testbed/inventor-testbed.kill-all.sh
ExecStart=/root/project-inventor/testbed/inventor-testbed.run-all.sh
Restart=always
RestartSec=10
User=root
WorkingDirectory=/root/project-inventor/testbed
StandardOutput=append:/var/log/inventor-testbed.out
StandardError=append:/var/log/inventor-testbed.err

[Install]
WantedBy=multi-user.target
```

### Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable inventor-testbed.service
sudo systemctl start inventor-testbed.service
```

### Verify service status

```bash
sudo systemctl status inventor-testbed.service
```

## Enable updates from Git

Updates from Git are performed once a day at midnight. This is achieved by the cron service.
Use the command `crontab -e` to add the following line at the end of the configuration file:

```bash
0 0 * * * cd /root/project-inventor && git pull origin main.
```

## Enable uploading the results to Git

The results are uploaded to the GitHub project "inventor-analysis" every day. This is accomplished by regularly executing the git-upload.sh script using the GitHub upload service.


