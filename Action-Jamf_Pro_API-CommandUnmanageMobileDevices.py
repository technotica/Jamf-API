#!/usr/bin/env python3

"""
This script will take the JSS ID from a static group of Mobile Devices, grab the ID of each device and store it in a Python list. 
Then it will iterate through that list, then issue an MDM command to the devices to unmanage themselves.

This is different from Action-Jamf_Pro_API-UnmanageMobileDevices.py
It will not set the Managed: field in Jamf to Unmanaged
The device must process the MDM Unmanage command to report as Unmanaged
Until it gets and processes the Unmanage command, it will still report as Managed

More details about the Unmanage Device MDM command
https://learn.jamf.com/en-US/bundle/jamf-pro-documentation-current/page/Remote_Commands_for_Mobile_Devices.html

You must provide the ID of the advanced mobile device search, "Static_Group_ID"

This is expected to be run in a CI environment (GitHub Actions) so certain secret values can be passed from the CI
This requires the installation of the JPS-API-Wrapper: https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper

Version 0.5
Jennifer Johnson 
04/05/24
"""

from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro
import logging
import os
import requests

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

# file log handler
file = logging.FileHandler("output.log",mode='w')
file.setFormatter(logformat)

# console log handler
console = logging.StreamHandler()
console.setFormatter(logformat)

# add handlers
logger.addHandler(file)
logger.addHandler(console)

# Get the Jamf URL and crendentials
JSS_URL = os.environ.get("JSS_URL")
CLIENT_ID = os.environ.get("JSS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("JSS_CLIENT_SECRET")
# Specify our unique Jamf Pro port, default is 443
port="8443"

# Set the Static Group ID we're going to be updating
Static_Group_ID = os.environ.get("JSS_MOBILE_STATIC_GROUP_ID")

def main():
    classic = Classic(JSS_URL, CLIENT_ID, CLIENT_SECRET, client=True)

    # Retrieves all the mobile device ids from the static group
    mobile_devices = classic.get_mobile_device_group(id=Static_Group_ID)
    mobile_device_ids = [ 
        mobile_device["id"]
        for mobile_device in mobile_devices["mobile_device_group"]["mobile_devices"]
    ]

    try:
        print(f"Unmanaged JSS IDs: {mobile_device_ids}")
        classic.create_mobile_device_command("UnmanageDevice", mobile_device_ids)

        # Jamf Pro API may throw an exception or error, try to handle it here
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error for ID: {mobile_device_ids}")
        print(err.args[0])

if __name__ == '__main__':
    main()
