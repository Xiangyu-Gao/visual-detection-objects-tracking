import numpy as np
import os
import csv
import numpy as np
import glob
import itertools
from collections import deque
from sklearn.utils.linear_assignment_ import linear_assignment

import helpers
import tracker
from tracker import Tracker
from helpers import box_iou2



# Global variables to be used by funcitons of VideoFileClop
frame_count = 0 # frame counter
max_age = 5  # no.of consecutive unmatched detection before
             # a track is deleted
min_hits = 2  # no. of consecutive matches needed to establish a track
tracker_list = [] # list for trackers
# list for track ID
track_id_list = deque(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',\
    'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'])
debug = False


def get_z_box(alist):
    z_box = []
    # print(alist)
    for elem in alist:
        z_box.append([float(elem[5]), float(elem[4]), float(elem[7]), float(elem[6])])
    
    return z_box


def add_track_to_newlist(alist, matched_res, x_id):
    new_list = []
    for idx,elem in enumerate(alist):
        if(idx not in matched_res[:,1]):
            elem.append('-1')
            new_list.append(elem) 
        else:
            temp_idx = np.where(matched_res[:,1] == idx)
            temp_idx = temp_idx[0][0]
            tra_idx = x_id[matched_res[temp_idx,0]]
            # convert ABC... to 012...
            elem.append(str(ord(tra_idx)-65))
            new_list.append(elem) 

    # print(new_list)
    return new_list


def assign_detections_to_trackers(trackers, detections, iou_thrd = 0.3):
    '''
    From current list of trackers and new detections, output matched detections,
    unmatchted trackers, unmatched detections.
    '''    
    
    IOU_mat = np.zeros((len(trackers),len(detections)),dtype=np.float32)
    for t,trk in enumerate(trackers):
        #trk = convert_to_cv2bbox(trk) 
        for d,det in enumerate(detections):
         #   det = convert_to_cv2bbox(det)
            IOU_mat[t,d] = box_iou2(trk,det) 
    
    # Produces matches       
    # Solve the maximizing the sum of IOU assignment problem using the
    # Hungarian algorithm (also known as Munkres algorithm)
    
    matched_idx = linear_assignment(-IOU_mat)        

    unmatched_trackers, unmatched_detections = [], []
    for t,trk in enumerate(trackers):
        if(t not in matched_idx[:,0]):
            unmatched_trackers.append(t)

    for d, det in enumerate(detections):
        if(d not in matched_idx[:,1]):
            unmatched_detections.append(d)

    matches = []
   
    # For creating trackers we consider any detection with an 
    # overlap less than iou_thrd to signifiy the existence of 
    # an untracked object
    
    for m in matched_idx:
        if(IOU_mat[m[0],m[1]]<iou_thrd):
            unmatched_trackers.append(m[0])
            unmatched_detections.append(m[1])
        else:
            matches.append(m.reshape(1,2))
    
    if(len(matches)==0):
        matches = np.empty((0,2),dtype=int)
    else:
        matches = np.concatenate(matches,axis=0)
    
    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)


# utility function for cluster_traj_portions function 
def group_ranges(L):
    """
    Collapses a list of integers into a list of the start and end of
    consecutive runs of numbers. Returns a generator of generators.
    >>> [list(x) for x in group_ranges([1, 2, 3, 5, 6, 8])]
    [[1, 3], [5, 6], [8]]
    """
    for w, z in itertools.groupby(L, lambda x, y=itertools.count(): next(y)-x):
        grouped = list(z)
        yield (x for x in [grouped[0], grouped[-1]][:len(grouped)])


def cluster_traj_portions(traj_list):
    for column in traj_list.T:
        valid_idx = np.where(column != -1)
        print(valid_idx)
        for x in group_ranges(valid_idx):
            print(x)
        input()


def pipeline(z_box):
    '''
    Pipeline function for tracking
    '''
    global frame_count
    global tracker_list
    global max_age
    global min_hits
    global track_id_list
    global debug
    
    frame_count += 1
    
    x_box = []
    x_id = []
    
    if len(tracker_list) > 0:
        for trk in tracker_list:
            x_box.append(trk.box)
            x_id.append(trk.id)
    
    print(track_id_list)
    matched, unmatched_dets, unmatched_trks \
    = assign_detections_to_trackers(x_box, z_box, iou_thrd = 0.3)  
    if debug:
         print('Detection: ', z_box)
         print('x_box: ', x_box)
         print('matched:', matched)
         # input()
         print('unmatched_det:', unmatched_dets)
         print('unmatched_trks:', unmatched_trks)
    
         
    # Deal with matched detections     
    if matched.size > 0:
        for trk_idx, det_idx in matched:
            z = z_box[det_idx]
            z = np.expand_dims(z, axis=0).T
            tmp_trk = tracker_list[trk_idx]
            tmp_trk.kalman_filter(z)
            xx = tmp_trk.x_state.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            x_box[trk_idx] = xx
            tmp_trk.box = xx
            tmp_trk.hits += 1
            tmp_trk.no_losses = 0
    
    # Deal with unmatched detections      
    if len(unmatched_dets) > 0:
        for idx in unmatched_dets:
            z = z_box[idx]
            z = np.expand_dims(z, axis=0).T
            tmp_trk = Tracker() # Create a new tracker
            x = np.array([[z[0], 0, z[1], 0, z[2], 0, z[3], 0]]).T
            tmp_trk.x_state = x
            tmp_trk.predict_only()
            xx = tmp_trk.x_state
            xx = xx.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            tmp_trk.box = xx
            tmp_trk.id = track_id_list.popleft() # assign an ID for the tracker
            tracker_list.append(tmp_trk)
            x_box.append(xx)
    
    # Deal with unmatched tracks       
    if len(unmatched_trks)>0:
        for trk_idx in unmatched_trks:
            tmp_trk = tracker_list[trk_idx]
            tmp_trk.no_losses += 1
            tmp_trk.predict_only()
            xx = tmp_trk.x_state
            xx = xx.T[0].tolist()
            xx = [xx[0], xx[2], xx[4], xx[6]]
            tmp_trk.box = xx
            x_box[trk_idx] = xx
                   
       
    # The list of tracks to be annotated  
    good_tracker_list = []
    for trk in tracker_list:
        if ((trk.hits >= min_hits) and (trk.no_losses <=max_age)):
             good_tracker_list.append(trk)
             x_cv2 = trk.box
             if debug:
                 print('updated box: ', x_cv2)
                 print()
             # img= helpers.draw_box_label(img, x_cv2) # Draw the bounding boxes on the 
                                             # images
    # Book keeping
    deleted_tracks = filter(lambda x: x.no_losses > max_age, tracker_list)  
    
    for trk in deleted_tracks:
            track_id_list.append(trk.id)
    
    tracker_list = [x for x in tracker_list if x.no_losses<=max_age]
    
    if debug:
       print('Ending tracker_list: ',len(tracker_list))
       print('Ending good tracker_list: ',len(good_tracker_list))
       
    return matched, x_id


def KF_Tracking(base_directory):

    global frame_count
    global tracker_list
    global max_age
    global min_hits
    global track_id_list
    global debug

    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/dets_3d_filtered/'
        store_directory = base_directory + '/' + subfolder + '/dets_3d_track/'
        if not os.path.exists(store_directory):
            os.makedirs(store_directory)

        # re-initialize
        frame_count = 0
        tracker_list = [] # list for trackers
        # list for track ID
        track_id_list = deque(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',\
        'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'])
        # print(track_id_list)
        # print(len(tracker_list))
        # input()

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


            z_box = get_z_box(alist)
            #print(z_box)
            matched_res, x_id = pipeline(z_box) 
            new_list = add_track_to_newlist(alist, matched_res, x_id)
            # print(matched_res)
            # print(x_id)
            # input()

            if len(new_list) > 0:

                # write file
                with open(store_file_directory, 'w') as g:
                    csv_writer = csv.writer(g)
                    csv_writer.writerows(new_list)

                g.close()

            else:
                file = open(store_file_directory, 'w')

        print('finished '+subfolder+file_name)
       
            
def filter_tracking(base_directory):

    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/dets_3d_track/'
        store_directory = base_directory + '/' + subfolder + '/dets_3d_track_filtered/'
        if not os.path.exists(store_directory):
            os.makedirs(store_directory)

        frame_idx = 0
        traj_list = []
        traj_pre_idx = []


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
        # print(np.where(traj_list[:,5] != -1))

        # clustering small trajectory portions
        cluster_traj_portions(traj_list)


if __name__ == "__main__":
    base_directory = 'D:/RawData/3D_loc_labels/2019_05_09/'
    # KF_Tracking(base_directory)
    filter_tracking(base_directory)


