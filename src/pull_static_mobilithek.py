import requests
from requests_pkcs12 import Pkcs12Adapter
import pandas as pd
import os
import time
import datetime
import sys
import pandas_read_xml as pdx

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# new_string = ROOT_DIR.replace("\\", "/")
# Root = new_string + "/static_data"
Root = os.path.join(ROOT_DIR, "static_data")
# URL for the DATEX II v2 SOAP endpoint
soap_url = 'https://mobilithek.info:8443/mobilithek/api/v1.0/subscription/soap/610481569602957312/clientPullService'

# Replace with the actual path to your .p12 certificate file and password
p12_certificate_path = r""+ROOT_DIR+r"\certificate\certificate.p12"
p12_certificate_password = 'S7YwrWhJP4Zd'

# Define the SOAP request XML payload with the specified 'SOAPAction'
soap_request_xml = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://datex2.eu/wsdl/clientPull/2_0">
   <soapenv:Header/>
   <soapenv:Body>
      <tns:getDatex2Data/>
   </soapenv:Body>
</soapenv:Envelope>
"""

# Define headers for the SOAP request
headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://datex2.eu/wsdl/clientPull/2_0/getDatex2Data'
}

# Define the CSV file path for storing the data
#xml_file_path = 'datex2_data.xml'

def pull_and_save_data(working_directory = os.getcwd()):
    try:
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_") + '_15min_static.csv'
        session = requests.Session()
        session.mount(soap_url, Pkcs12Adapter(
            pkcs12_filename=p12_certificate_path, pkcs12_password=p12_certificate_password))
        # Send the SOAP request
        response = session.post(soap_url, data=soap_request_xml, headers=headers)
        if response.status_code == 200:
            # Extract and process the DATEX II data from the response
            all_data = []
            for element in pdx.read_xml(response.text).iloc[0]['soapenv:Envelope']['soapenv:Body']['d2LogicalModel']['payloadPublication']['measurementSiteTable']['measurementSiteRecord']:
                temp_type = element['measurementEquipmentTypeUsed']['values']['value']
                temp_id = element['measurementSiteIdentification']
                temp_location = element['measurementSiteLocation']['pointAlongLinearElement']['linearElement']['roadName']['values']['value']
                temp_lat = None
                temp_lon = None
                if len(element['measurementSiteLocation'])==3:
                    temp_lat = element['measurementSiteLocation']['pointByCoordinates']['pointCoordinates']['latitude']
                    temp_lon = element['measurementSiteLocation']['pointByCoordinates']['pointCoordinates']['longitude']
                all_data.append([temp_id, temp_type, temp_location, temp_lat, temp_lon])
            all_data_df_to_csv = pd.DataFrame(all_data, columns=['detid', 'type','location_desc','lat','lon'])
            all_data_df_to_csv.to_csv(os.path.join(working_directory, filename))
            session.close()
        else:
            print(f"Request failed with status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def static_data():
    pull_and_save_data(Root)

if __name__ == '__main__':
    pull_and_save_data(Root)




