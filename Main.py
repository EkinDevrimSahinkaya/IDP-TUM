from addLayer import layer
from datetime import datetime
from time import sleep
from pull_xml_to_csv_mobilithek import xml_to_csv
from pull_static_mobilithek import static_data
from compare import output_data
from compareLRZandMobilet import compareCsvFile
def run(condition):
    while datetime.now().minute not in {0, 15, 30,
                                        45}:  # Wait 1 second until we are synced up with the 'every 15 minutes' clock

        sleep(1)

    def task():
        xml_to_csv()
        static_data()
        output_data()
        compareCsvFile()
        layer()

    task()


    while condition == True:
        sleep(60 * 15)  # Wait for 15 minutes
        task()

if __name__ == '__main__':
    # run(True)
    xml_to_csv()
    static_data()
    output_data()
    compareCsvFile()
    layer()