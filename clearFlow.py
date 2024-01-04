import os
import glob
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
new_string = ROOT_DIR.replace("\\", "/")
mergedDataRoot = new_string + "/IDP-TUM/mergedData"

folder_path = mergedDataRoot

def get_detector_ids(folder_path):
    # Tüm dosyalardan araç ID'lerini al
    files = glob.glob(os.path.join(folder_path, '*.csv'))
    detector_ids = set()
    for file in files:
        df = pd.read_csv(file)
        detector_ids.update(df['detid'].unique())
    return list(detector_ids)


def remove_row(folder_path):
    detector_ids = get_detector_ids(folder_path)
    latest_file = max(glob.glob(os.path.join(folder_path, '*.csv')), key=os.path.getmtime)

    for detetor_id in detector_ids:
        df = pd.read_csv(latest_file)
        detector_rows = df[df['detid'] == detetor_id]
        if len(detector_rows) > 0:
            zero_speed_count = (detector_rows['flow'] == 0).sum()
            total_rows = len(detector_rows)

            if zero_speed_count / total_rows >= 0.8:
                df = df[
                    ~((df['detid'] == detetor_id) & (df['flow'] == 0))]
                df.to_csv(latest_file, index=False)



def clearFlow():
    remove_row(folder_path)

