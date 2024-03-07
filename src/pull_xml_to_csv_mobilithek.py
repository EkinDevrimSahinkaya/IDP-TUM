import requests
from requests_pkcs12 import Pkcs12Adapter
import pandas as pd
import os
import time
import datetime
import sys
import pandas_read_xml as pdx
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# rootPath = ROOT_DIR.replace("\\", "/")
# Root = rootPath + "/xml_data"
Root = os.path.join(ROOT_DIR, "data/xml_data")

# URL for the DATEX II v2 SOAP endpoint
soap_url = 'https://mobilithek.info:8443/mobilithek/api/v1.0/subscription/soap/610484276019744768/clientPullService'

# Replace with the actual path to your .p12 certificate file and password
p12_certificate_path =r""+ROOT_DIR+r"\certificate\certificate.p12"
p12_certificate_password = 'S7YwrWhJP4Zd'

# Define the SOAP request XML payload with the specified 'SOAPAction'
soap_request_xml = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="https://datex2.eu/schema/2/2_0">
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
# xml_file_path = 'datex2_data.xml'

def pull_and_save_data(working_directory=os.getcwd()):
    try:
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_") + '_15min.csv'
        session = requests.Session()
        session.mount(soap_url,
                      Pkcs12Adapter(pkcs12_filename=p12_certificate_path, pkcs12_password=p12_certificate_password))

        # Send the SOAP request
        response = session.post(soap_url, data=soap_request_xml, headers=headers)

        if response.status_code == 200:
            # Extract and process the DATEX II data from the response
            mdm = pdx.read_xml(response.text,
                               ['soapenv:Envelope', 'soapenv:Body', 'd2LogicalModel', 'payloadPublication',
                                'siteMeasurements'], root_is_rows=False)
            # print(mdm)

            all_entries = []

            for idx, row in mdm.iterrows():
                temp_index = int(row.measurementSiteReference['@id'])
                temp_time = row.measurementTimeDefault

                if len(row.measuredValue) == 3:

                    # checkStr purpose is if a row really contain var we are looking for
                    checkStr = str(row.measuredValue[0])
                    if("vehicleFlowRate" in checkStr):
                        temp_Flow = row.measuredValue[0]['measuredValue']['basicData']['vehicleFlow']['vehicleFlowRate']
                    if("vehicleType" in checkStr):
                        temp_veh_type_flow = row.measuredValue[0]['measuredValue']['basicData']['forVehiclesWithCharacteristicsOf']['vehicleType']
                    checkStr = row.measuredValue[1]
                    if ("vehicleFlowRate" in checkStr):
                        temp_speed = float(row.measuredValue[1]['measuredValue']['basicData']['averageVehicleSpeed']['speed'])
                    if ("vehicleType" in checkStr):
                        temp_veh_type_speed = row.measuredValue[1]['measuredValue']['basicData']['forVehiclesWithCharacteristicsOf']['vehicleType']
                    checkStr = row.measuredValue[2]
                    if ("percentage" in checkStr):
                        temp_occ = float(row.measuredValue[2]['measuredValue']['basicData']['occupancy']['percentage'])

                else:
                    checkLength = str(row.measuredValue)
                    # checkLength purpose is if a row really smaller than 1 because there are some cases even size is 1 len funvtion gives 2
                    if len(row.measuredValue) <2 or checkLength[0] == '{' :
                        temp_Flow = row.measuredValue['measuredValue']['basicData']['vehicleFlow']['vehicleFlowRate']
                        temp_veh_type_flow =row.measuredValue['measuredValue']['basicData']['forVehiclesWithCharacteristicsOf'][
                                'vehicleType']
                    else:
                        temp_Flow = row.measuredValue[0]['measuredValue']['basicData']['vehicleFlow']['vehicleFlowRate']
                        temp_veh_type_flow = \
                        row.measuredValue[0]['measuredValue']['basicData']['forVehiclesWithCharacteristicsOf'][
                            'vehicleType']
                    temp_speed = 0
                    temp_veh_type_speed = None
                    temp_occ = 0
                all_entries.append([temp_index,temp_time,temp_Flow,temp_veh_type_flow,temp_speed,temp_veh_type_speed,temp_occ])
            temp_df = pd.DataFrame(all_entries, columns = ["detid","timestamp","flow","vehicleTypeFlow","speed","vehicleTypeSpeed","occupancy_percentage"])

            # temp_df.to_pickle(os.path.join(sd, filename))

            temp_df.to_csv(os.path.join(working_directory, filename))
            session.close()
        else:
            print(f"Request failed with status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def xml_to_csv():
    pull_and_save_data(Root)


if __name__ == '__main__':
    pull_and_save_data(Root)




