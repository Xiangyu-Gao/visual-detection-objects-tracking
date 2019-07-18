import numpy as np
import os
import csv

def main():

    base_directory = 'D:/RawData/3D_loc_labels/2019_05_09/'
    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/dets_3d/'
        store_directory = base_directory + '/' + subfolder + '/dets_3d_filtered/'
        if not os.path.exists(store_directory):
            os.makedirs(store_directory)

        for file_name in os.listdir(sub_directory):
            file_directory = sub_directory + file_name
            store_file_directory = store_directory + file_name

            # input()
            # file_name = 'D:/RawData/3D_loc_labels/2019_04_09_3d_loc_labels/2019_04_09_bms1000/dets_3d/0000000184.txt'
            with open(file_directory) as f:
                data = f.read().splitlines()
                alist = []
                for line in data:
                    alist.append(line.split())

            f.close()

        print(alist)
        input()



if __name__ == "__main__":
    main()