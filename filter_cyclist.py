import numpy as np
import os
import csv

# compute IOU function
def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
 
    # compute the area of intersection rectangle
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
 
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
 
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)
 
    # return the intersection over union value
    return iou


def find_index_class(alist, classname):
    index_list = []
    for i in range(len(alist)):
        #print(alist[i][0])
        if alist[i][0] == classname:
            index_list.append(i)
            #print(1)

    return index_list


def filter_pedestrian(alist):
    new_list = []
    ped_list = find_index_class(alist, 'pedestrian')
    cyc_list = find_index_class(alist, 'cyclist')
    car_list = find_index_class(alist, 'car')
    #print(ped_list)
    #print(cyc_list)

    if len(ped_list) > 0 and len(cyc_list) > 0:
        for i in ped_list:
            flag = True
            for j in cyc_list:
                # IOU > 0.5
                boxA = np.array([float(alist[i][4]), float(alist[i][5]), float(alist[i][6]), float(alist[i][7])])
                boxB = np.array([float(alist[j][4]), float(alist[j][5]), float(alist[j][6]), float(alist[j][7])])
                # print(boxA)
                # print(boxB)

                if bb_intersection_over_union(boxA, boxB) > 0.5:
                    # abs(d_x)<2m, abs(d_y) < 2m
                    x_ped = float(alist[i][11])
                    x_cyc = float(alist[j][11])
                    z_ped = float(alist[i][13])
                    z_cyc = float(alist[j][13])
                    if abs(x_ped - x_cyc) < 2 and abs(z_ped - z_cyc) < 2:
                        # filter this pedestrian
                        flag = False
                        break

            if flag is True:
                new_list.append(alist[i])

        for j in cyc_list:
            new_list.append(alist[j]) 
        for k in car_list:
            new_list.append(alist[k]) 

        return new_list

    else:
        return alist

    


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


            # print(data[0])
            # print(alist[0])
            # print(alist)
            new_list = filter_pedestrian(alist)
            # print(new_list)

            if len(new_list) > 0:
            # class encoding
                for i in range(len(new_list)):
                    if new_list[i][0] == 'pedestrian':
                        new_list[i][0] = '0'
                    elif new_list[i][0] == 'car':
                        new_list[i][0] = '1'
                    elif new_list[i][0] == 'cyclist':
                        new_list[i][0] = '2'
                    else:
                        pass

                # print(new_list)
                # input()

                # write file
                with open(store_file_directory, 'w') as g:
                    csv_writer = csv.writer(g)
                    csv_writer.writerows(new_list)

                    # for item in new_list:
                    #     g.write("%s\n" % str(item))

                g.close()

            else:
                file = open(store_file_directory, 'w')

            print('finished '+subfolder+file_name)


if __name__ == "__main__":
    main()