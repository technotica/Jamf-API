#!/usr/bin/env python3

"""
Retrieves the latest supported macOS for each computer in Jamf

This script gets all the JSS IDs from the entire JSS, then iterates through the list, gathering each ID's Model Identifier.
After it has the Model Identifier, it only updates each Computer ID's record and updates the Extension Attribute with the 
Latest supported macOS if the latest supported macOS has changed or is blank.

This is expected to be run in a CI environment (GitHub Actions) so certain secret values can be passed from the CI
This requires the installation of the JPS-API-Wrapper: https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper

Version 0.5
Jennifer Johnson 
09/10/24
"""

from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro
import logging
import os
import requests
import re

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

# Set the Extension Attribute Name and ID
xEA_name = os.environ.get("JSS_xEA_NAME")
xEA_id = os.environ.get("JSS_xEA_ID")

def macOSCompatibility(model):
    # Get the latest supported version of macOS based on Regex query. 
    macOS_compatible = ""
    while not macOS_compatible:
        # Jamf reports modelIdentifier as "null" if it is blank
        if model is None:
            macOS_compatible = "Model Identifier Not Found"
            return macOS_compatible
        
        # Does Mac Model Identifier support macOS Sequoia?
        macOS_Sequoia_Regex = re.compile(r'(^(Mac(1[3-9]|BookPro1[5-8]|BookAir(9|10)|Pro[7-9])|iMac(Pro\d+|(19|[2-9]\d))|Macmini[89]),\d+$)')
        macOS_Sequoia = macOS_Sequoia_Regex.search(model)
        if macOS_Sequoia:
            macOS_compatible = "macOS 15 Sequoia"
            return macOS_compatible
        
        macOS_Sonoma_Regex = re.compile(r'(^(Mac(1[345]|BookPro1[5-8]|BookAir([89]|10)|Pro7)|iMac(Pro1|(19|2[01]))|Macmini[89]),\d+$)')
        macOS_Sonoma = macOS_Sonoma_Regex.search(model)
        if macOS_Sonoma:
            macOS_compatible = "macOS 14 Sonoma"
            return macOS_compatible
        
        macOS_Ventura_Regex = re.compile(r'(^(Mac(1[34]|BookPro1[4-8]|BookAir([89]|10)|Pro7|Book10)|iMac(Pro1|(1[89]|2[01]))|Macmini[89]),\d+$)')
        macOS_Ventura = macOS_Ventura_Regex.search(model)
        if macOS_Ventura:
            macOS_compatible = "macOS 13 Ventura"
            return macOS_compatible 
        
        macOS_Monterey_Regex = re.compile(r'(^Mac1[34]|MacBook(10|9)|MacBookAir(10|[7-9])|Macmini[7-9]|MacPro[6-7]|iMacPro1|iMac(1[6-9]|2[0-2])),\d|MacBookPro1(1,[45]|[2-8],\d)')
        macOS_Monterey = macOS_Monterey_Regex.search(model)
        if macOS_Monterey:
            macOS_compatible = "macOS 12 Monterey"
            return macOS_compatible 
        
        macOS_BigSur_Regex = re.compile(r'(MacBook(10|9|8)|MacBookAir(10|[6-9])|MacBookPro1[1-7]|Macmini[7-9]|MacPro[6-7]|iMacPro1),\d|iMac(14,4|1[5-9],\d|2[01],\d)')
        macOS_BigSur = macOS_BigSur_Regex.search(model)
        if macOS_BigSur:
            macOS_compatible = "macOS 11 Big Sur"
            return macOS_compatible
        
        macOS_Virtual_Regex = re.compile(r'(VirtualMac2,1|Parallels1[3-5],1|VMware\d{1,2},\d{1})')
        macOS_Virtual = macOS_Virtual_Regex.search(model)
        if macOS_Virtual:
            macOS_compatible = "Virtual Mac"
            return macOS_compatible
                
        if not all((macOS_Sequoia, macOS_Sonoma, macOS_Ventura, macOS_Monterey, macOS_BigSur, macOS_Virtual)):
            macOS_compatible = "macOS 10.15 Catalina or older"
            return macOS_compatible 

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
        current = pro.get_computer_inventory_detail(id=device_id)
        # Get the Model Identifier for this computer 
        model_identifier = current["hardware"]["modelIdentifier"]  
             
        # Get the current value of xEA - macOS Latest Supported for this computer
        # Since its a list of dictionary values, we have to look for the right extension attribute to get its value
        for extensionAttributes in current["operatingSystem"]["extensionAttributes"]:
            if xEA_id in extensionAttributes["definitionId"]:
                current_xEA_macOS_compatible = str(extensionAttributes["values"])
                # Do some text formatting to get rid of extra brackets and quotes
                current_xEA_macOS_compatible = current_xEA_macOS_compatible[2:-2]
        
        macOS_compatible_status = macOSCompatibility(model_identifier)

        # Only update xEA - macOS Latest Supported if the the latest supported macOS has changed
        # If for some reason the Jamf Computer ID exists but the record is inaccessible, don't try to update
        if macOS_compatible_status != current_xEA_macOS_compatible and current is not None:
            # Set the JSON payload to be uploaded to Jamf, e.g. set the xEA - macOS Latest Supported value
            try:
                message = f"{macOS_compatible_status}"
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
                macOS_latest=f"JSS ID: {device_id}, Computer Name: {computer_name}, Extension Attribute: {xEA_name}, Value: {macOS_compatible_status}, {xEA_name} Previous Value: {current_xEA_macOS_compatible}"
                # Export the results to GitHub environment so it can be added to the summary page
                print(f"{macOS_latest}")
            # Jamf Pro API may throw an exception or error, try to handle it here
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for ID: {device_id}")
                print(err.args[0])

if __name__ == '__main__':
    main()