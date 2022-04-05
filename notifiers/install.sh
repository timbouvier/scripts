#!/bin/bash

sudo cp ./poller.service /etc/systemd/system/poller.service
sudo systemctl enable poller.service
sudo systemctl start poller.service
