from add_layer import layer
from datetime import datetime
from time import sleep
from pull_xml_to_csv_mobilithek import xml_to_csv
from pull_static_mobilithek import static_data
from compare import output_data, compare_csv_files
from clear_flow import clear_flow
from visualise_network import plot


def run(condition: bool):
    """ For now: Entry point for the processing pipeline. Calls the different processing
    steps before sleeping for 15 minutes if ``condition`` is ``True``

    :param condition: specifies whether processing pipeline should run indefinitely
    """
    while datetime.now().minute not in {0, 15, 30, 45}:
        # Wait 1 second until we are synced up with the 'every 15 minutes' clock
        sleep(1)

    def task():
        xml_to_csv()
        static_data()
        output_data()
        compare_csv_files()
        clear_flow()
        layer()
        # plot() -> i think this suspends program until the plot instance is closed

    task()

    while condition:
        sleep(60 * 15)  # Wait for 15 minutes
        task()


if __name__ == '__main__':
    #run(True)
    xml_to_csv()
    static_data()
    output_data()
    compare_csv_files()
    clear_flow()
    layer()
    plot()
