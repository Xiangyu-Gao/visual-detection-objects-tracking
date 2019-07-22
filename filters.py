import itertools
import os
import csv
import numpy as np
from operator import itemgetter
from itertools import groupby

# utility function for cluster_traj_portions function 
def group_ranges(data):
    """
    Collapses a list of integers into a list of the start and end of
    consecutive runs of numbers. Returns a generator of generators.
    >>> [list(x) for x in group_ranges([1, 2, 3, 5, 6, 8])]
    [[1, 3], [5, 6], [8]]
    """
    ranges =[]
    for k,g in groupby(enumerate(data),lambda x:x[0]-x[1]):
        group = list(map(itemgetter(1),g))
        ranges.append([group[0],group[-1]])
    return ranges


def cluster_traj_portions(traj_list):
    traj_group_list = []
    for column in traj_list.T:
        valid_idx = list(np.where(column != -1))[0]
        # print(valid_idx)
        group_idx = group_ranges(valid_idx)
        # print(group_idx)
        # concatenate group_idx
        new_group_idx = []
        for g,group in enumerate(group_idx):
            if g == 0:
                new_group_idx.append(group)
            elif int(group[0]) - int(new_group_idx[-1][1]) <= 3:
                new_group_idx[-1][1] = group[1]
            else:
                new_group_idx.append(group)

        # print(new_group_idx)
        # delete the trajectory with very few occurence
        new_new_group_idx = []
        for group in new_group_idx:
            if group[1] - group[0] <=3:
                pass
            else:
                new_new_group_idx.append(group)

        # print(new_new_group_idx)
        # input()
        traj_group_list.append(new_new_group_idx)
    return traj_group_list


def smooth_detection_class(traj_group_list, traj_list):
    dims = traj_list.shape
    new_traj_list = -1*np.ones(dims)

    for t, traj in enumerate(traj_group_list):
        for s, sub_traj in enumerate(traj):
            # print(t)
            # list is empty
            if not sub_traj:
                pass
            else:
                start_frame = sub_traj[0]
                end_frame = sub_traj[1]
                new_traj_list[start_frame:end_frame+1, t] = traj_list[start_frame:end_frame+1, t] 
                # print(start_frame)
                # print(end_frame)
                # smoothee the expection peak
                # print(traj_list[start_frame:end_frame+1, t])
                
                if end_frame - start_frame + 1 <= 10:
                    counter_ay = traj_list[start_frame:end_frame+1, t]
                    num_1 = (counter_ay == 0).sum()
                    num_2 = (counter_ay == 1).sum()
                    num_3 = (counter_ay == 2).sum()
                    class_max = max([num_1, num_2, num_3])

                    if class_max == num_1:
                        new_traj_list[start_frame:end_frame+1, t] = 0
                    elif class_max == num_2:
                        new_traj_list[start_frame:end_frame+1, t] = 1
                    elif class_max == num_3:
                        new_traj_list[start_frame:end_frame+1, t] = 2
                    else:
                        pass

                else:
                    for i in range(start_frame, end_frame+1):
                        counter_ay_start = max([start_frame, i-10])
                        counter_ay_end = min([end_frame, i+10])
                        counter_ay = traj_list[counter_ay_start:counter_ay_end+1, t]
                        # check if all class are same
                        if np.all(counter_ay == new_traj_list[i,t]):
                            pass

                        else:
                            num_1 = (counter_ay == 0).sum()
                            num_2 = (counter_ay == 1).sum()
                            num_3 = (counter_ay == 2).sum()
                            class_max = max([num_1, num_2, num_3])

                            if class_max == num_1:
                                new_traj_list[i, t] = 0
                            elif class_max == num_2:
                                new_traj_list[i, t] = 1
                            elif class_max == num_3:
                                new_traj_list[i, t] = 2
                            else:
                                pass

                # print(new_traj_list[start_frame:end_frame+1, t])

                # input()
        # print(111)
    return new_traj_list


def write_3d_loc(new_traj_list, traj_list, traj_pre_idx, sub_directory, store_directory):

    frameid = 0
    for file_name in os.listdir(sub_directory):
        file_directory = sub_directory + file_name
        store_file_directory = store_directory + file_name

        # input()
        with open(file_directory) as f:
            data = f.read().splitlines()
            alist = []
            for line in data:
                if line == '':
                    pass
                else:
                    alist.append(line.split(','))
        f.close()

        # print(type(alist[0][0]))
        # print(traj_list.shape[0])
        # print(new_traj_list.shape[1])
        # input()
        new_alist = []

        if frameid == 0:
            new_alist = alist

        else:
            for j in range(traj_list.shape[1]):
                index = int(traj_pre_idx[frameid][j])
                old_class = int(traj_list[frameid][j])
                new_class = int(new_traj_list[frameid][j])
                # print(index)

                if  old_class == new_class and old_class != -1:
                    new_alist.append(alist[index])
                    # print(1)
                elif old_class != -1 and new_class != -1:
                    list_elem = alist[index]
                    list_elem[0] = str(new_class)
                    new_alist.append(list_elem)
                    # print(2)
                elif old_class != -1 and new_class == -1:
                    # print(3)
                    pass
                elif old_class == -1 and new_class != -1:
                    # print(4)
                    pre_index = int(traj_pre_idx[frameid-1][j])
                    nex_index = int(traj_pre_idx[frameid+1][j])
                    if pre_index != -1:
                        # open previous file
                        # input()
                        pre_file_directory = sub_directory + os.listdir(sub_directory)[frameid-1]
                        with open(pre_file_directory) as pf:
                            data = pf.read().splitlines()
                            pre_alist = []
                            for line in data:
                                if line == '':
                                    pass
                                else:
                                    pre_alist.append(line.split(','))
                        pf.close()

                        list_elem = pre_alist[pre_index]
                        new_alist.append(list_elem)
                    
                    elif nex_index != -1:
                        # open next file
                        # input()
                        nex_file_directory = sub_directory + os.listdir(sub_directory)[frameid+1]
                        with open(nex_file_directory) as nf:
                            data = nf.read().splitlines()
                            nex_alist = []
                            for line in data:
                                if line == '':
                                    pass
                                else:
                                    nex_alist.append(line.split(','))
                        nf.close()

                        list_elem = nex_alist[nex_index]
                        new_alist.append(list_elem)
                    
                    else:
                        pass

                else:
                    pass

        frameid += 1
        # print(alist)
        # print(new_alist)
        # input()
        
        # write to new storage directory
        if len(new_alist) > 0:
            # write file
            with open(store_file_directory, 'w') as g:
                csv_writer = csv.writer(g)
                csv_writer.writerows(new_alist)
            g.close()

        else:
            file = open(store_file_directory, 'w')

        print('finished '+ file_name)


def filter_tracking(base_directory):

    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/dets_3d_track/'
        store_directory = base_directory + '/' + subfolder + '/dets_3d_track_filtered/'
        if not os.path.exists(store_directory):
            os.makedirs(store_directory)

        frame_idx = 0
        traj_list = []
        traj_pre_idx = []
        traj_pre_posx = []
        traj_pre_posy = []


        # get the number of trajectories
        tra_max = 20

        for file_name in os.listdir(sub_directory):
            file_directory = sub_directory + file_name
            store_file_directory = store_directory + file_name

            # input()
            with open(file_directory) as f:
                data = f.read().splitlines()
                alist = []
                for line in data:
                    if line == '':
                        pass
                    else:
                        alist.append(line.split(','))
            f.close()

            temp_traj_elem = np.ones(tra_max)
            temp_traj_elem = -1*temp_traj_elem
            temp_traj_idx = np.ones(tra_max)
            temp_traj_idx = -1*temp_traj_idx
            for e,elem in enumerate(alist):
                ix = int(elem[-1])
                i_class = int(elem[0])
                if ix is not -1:
                    temp_traj_elem[ix] = i_class
                    temp_traj_idx[ix] = e
                else:
                    pass
            
            traj_list.append(temp_traj_elem)
            traj_pre_idx.append(temp_traj_idx)
            frame_idx += 1
            # print(file_name)
            # print(temp_traj_elem)
            # print(temp_traj_idx)
            # input()
        
        # print(traj_list)
        traj_list = np.asarray(traj_list)
        traj_pre_idx = np.asarray(traj_pre_idx)

        # clustering small trajectory portions
        traj_group_list = cluster_traj_portions(traj_list)
        # print(traj_group_list)

        # smoothe the detection result
        new_traj_list = smooth_detection_class(traj_group_list, traj_list)
        # rewrite the 3d localization file
        write_3d_loc(new_traj_list, traj_list, traj_pre_idx, sub_directory, store_directory)
