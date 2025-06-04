# Running testbed as service

To run the testbes schedules as a service follow the steps:

## Create the systemd service

Create /etc/systemd/system/capture-tap.service:

```
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

## Enable and start the service

```
sudo systemctl daemon-reload
sudo systemctl enable inventor-testbed.service
sudo systemctl start inventor-testbed.service
```

## Verify service status

```
sudo systemctl status capture-tap.service
```
