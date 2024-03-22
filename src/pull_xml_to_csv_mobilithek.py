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

            all_data = []
            for idx, row in mdm.iterrows():
                det_id = int(row.measurementSiteReference['@id'])
                date_time = row.measurementTimeDefault
                anyVehicle, car, lorry, lorryAndVehicleWithTrailer, articulatedVehicle, anyVehicle_unknown, carWithTrailer, van, bus, motorcycle = -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
                speed_carOrLightVehicle, speed_lorry = -1, -1
                if type(row.measuredValue) == dict:
                    anyVehicle = row.measuredValue['measuredValue']['basicData']['vehicleFlow']['vehicleFlowRate']
                else:
                    if not type(row.measuredValue) == list:
                        anyVehicle = math.nan
                    else:
                        for measurement in row.measuredValue:
                            if 'vehicleFlow' in measurement['measuredValue']['basicData'].keys():
                                cur_val = measurement['measuredValue']['basicData']['vehicleFlow']['vehicleFlowRate']
                                if int(measurement['@index']) == 10:
                                    anyVehicle = cur_val
                                elif int(measurement['@index']) == 11:
                                    car = cur_val
                                elif int(measurement['@index']) == 12:
                                    lorry = cur_val
                                elif int(measurement['@index']) == 13:
                                    lorryAndVehicleWithTrailer = cur_val
                                elif int(measurement['@index']) == 14:
                                    articulatedVehicle = cur_val
                                elif int(measurement['@index']) == 15:
                                    anyVehicle_unknown = cur_val
                                elif int(measurement['@index']) == 16:
                                    carWithTrailer = cur_val
                                elif int(measurement['@index']) == 17:
                                    van = cur_val
                                elif int(measurement['@index']) == 18:
                                    bus = cur_val
                                elif int(measurement['@index']) == 19:
                                    motorcycle = cur_val
                            else:
                                cur_val = measurement['measuredValue']['basicData']['averageVehicleSpeed']['speed']
                                if int(measurement['@index']) == 21:
                                    speed_carOrLightVehicle = cur_val
                                elif int(measurement['@index']) == 22:
                                    speed_lorry = cur_val
                all_data.append([det_id, date_time, anyVehicle, car, lorry, lorryAndVehicleWithTrailer, articulatedVehicle, anyVehicle_unknown, carWithTrailer, van, bus, motorcycle, speed_carOrLightVehicle, speed_lorry])
            all_data_df = pd.DataFrame(all_data, columns = ['detid','date_time', 'flow', 'car', 'lorry', 'lorryAndVehicleWithTrailer', 'articulatedVehicle', 'anyVehicle_unknown', 'carWithTrailer', 'van', 'bus', 'motorcycle', 'speed_carOrLightVehicle', 'speed_lorry'])
            all_data_df.to_csv(os.path.join(working_directory, filename))
            session.close()

        else:
            print(f"Request failed with status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def xml_to_csv():
    pull_and_save_data(Root)


if __name__ == '__main__':
    pull_and_save_data(Root)