import os
import glob
import pandas as pd
from config import ROOT_DIR

rootPath = ROOT_DIR.replace("\\", "/")
mergedDataRoot = rootPath + "/merged_data"


def get_detector_ids(folder_path: str):
    """
    :param folder_path: Path to folder containing the merged data
    :return: A list containing unique detector ids
    """

    files = glob.glob(os.path.join(folder_path, '*.csv'))
    detector_ids = set()
    for file in files:
        df = pd.read_csv(file)
        detector_ids.update(df['detid'].unique())
    return list(detector_ids)


def remove_row(folder_path: str):
    """ Remove rows where the flow measured by a detector is 0

    :param folder_path: Path to folder containing the merged data
    """

    detector_ids = get_detector_ids(folder_path)
    latest_file = max(glob.glob(os.path.join(folder_path, '*.csv')), key=os.path.getmtime)

    for detector_id in detector_ids:
        df = pd.read_csv(latest_file)
        detector_rows = df[df['detid'] == detector_id]
        if len(detector_rows) > 0:
            zero_speed_count = (detector_rows['flow'] == 0).sum()
            total_rows = len(detector_rows)

            if zero_speed_count / total_rows >= 0.8:
                df = df[
                    ~((df['detid'] == detector_id) & (df['flow'] == 0))]
                df.to_csv(latest_file, index=False)



def clear_flow():
    remove_row(mergedDataRoot)

