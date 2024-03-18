#!/usr/bin/env python3

"""
In Jamf Pro, sites are not available to use as search criteria for smart groups or advanced searches.
To get this information we use Custom Extension Attributes.

This script gets all the JSS IDs from the entire JSS, then iterates through the list, gathering each ID's site name.
After it has the site name, it only updates each Computer ID's record and updates the Extension Attribute with the site name if
the site name has changed or is blank.

This is expected to be run in a CI environment (GitHub Actions) so certain secret values can be passed from the CI
This requires the installation of the JPS-API-Wrapper: https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper

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
JSS_URL = os.environ.get("JAMF_URL")
CLIENT_ID = os.environ.get("JAMF_CLIENT_ID")
CLIENT_SECRET = os.environ.get("JAMF_CLIENT_SECRET")
# Specify our unique Jamf Pro port, default is 443
port="8443"

# Set the Extension Attribute Name and ID
xEA_name = os.environ.get("JAMF_xEA_NAME")
xEA_id = os.environ.get("JAMF_xEA_ID")

def main():
    classic = Classic(JSS_URL, CLIENT_ID, CLIENT_SECRET, client=True)
    pro = Pro(JSS_URL, CLIENT_ID, CLIENT_SECRET, client=True)

    # Retrieves all the computer ids and computer names
    all_computers = classic.get_computers()["computers"]
    # For every computer ID found do the following
    for computer in all_computers:
        # Get the JSS ID and Computer Name
        device_id = computer["id"]
        computer_name = computer["name"]
        # Get details from the General subset about the Computer ID
        current = pro.get_computer_inventory(id=device_id,section=["GENERAL"])
        # Get the Jamf Site Name for this computer 
        site_name = current["general"]["site"]["name"]     
            
        # Get the current value of xEA - Jamf Site for this computer
        # Since its a list of dictionary values, we have to look for the right extension attribute to get its value
        for extensionAttributes in current["general"]["extensionAttributes"]:
            if xEA_id in extensionAttributes["definitionId"]:
                current_xEA_site_name = str(extensionAttributes["values"])
                # Do some text formatting to get rid of extra brackets and quotes
                current_xEA_site_name = current_xEA_site_name[2:-2]
            
        # Only update xEA - Jamf Site Name if the site name has changed
        if site_name != current_xEA_site_name:
            # Set the JSON payload to be uploaded to Jamf, e.g. set the xEA - Jamf Site value
            try:
                message = f"{site_name}"
                pro.update_computer_inventory(
                    { 
                        "extensionAttributes": [
                            {
                                "definitionId": xEA_id, 
                                "values": [message],
                            }
                        ]
                    }, device_id)
                # Format a text string of the results
                site_output=f"JSS ID: {device_id}, Computer Name: {computer_name}, Extension Attribute: {xEA_name}, Value: {site_name}, {xEA_name} Previous Value: {current_xEA_site_name}"
                # Export the results to GitHub environment so it can be added to the summary page
                print(f"{site_output}")
            # Jamf Pro API may throw an exception or error, try to handle it here
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for ID: {device_id}")
                print(err.args[0])

if __name__ == '__main__':
    main()
