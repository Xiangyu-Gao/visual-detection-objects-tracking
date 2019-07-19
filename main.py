import numpy as np
import os
#import csv

import numpy as np
#import matplotlib.pyplot as plt
import glob
from collections import deque
from sklearn.utils.linear_assignment_ import linear_assignment

import helpers
import tracker
from tracker import Tracker
from helpers import box_iou2

# Global variables to be used by funcitons of VideoFileClop
frame_count = 0 # frame counter

max_age = 4  # no.of consecutive unmatched detection before 
             # a track is deleted

min_hits =1  # no. of consecutive matches needed to establish a track

tracker_list =[] # list for trackers
# list for track ID
track_id_list= deque(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'])

debug = True

def get_z_box(alist):
    z_box = []
    # print(alist)
    for elem in alist:
        z_box.append([float(elem[5]), float(elem[4]), float(elem[7]), float(elem[6])])
    
    return z_box

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
    
    # img_dim = (img.shape[1], img.shape[0])

    # z_box = det.get_localization(img) # measurement
    # if debug:
    #    print('Frame:', frame_count)
       
    x_box =[]
    # if debug: 
    #     for i in range(len(z_box)):
    #        img1= helpers.draw_box_label(img, z_box[i], box_color=(255, 0, 0))
    #        plt.imshow(img1)
    #     plt.show()
    
    if len(tracker_list) > 0:
        for trk in tracker_list:
            x_box.append(trk.box)
    
    
    matched, unmatched_dets, unmatched_trks \
    = assign_detections_to_trackers(x_box, z_box, iou_thrd = 0.3)  
    if debug:
         print('Detection: ', z_box)
         print('x_box: ', x_box)
         print('matched:', matched)
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
    good_tracker_list =[]
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
    
       
    return tracker_list


def main():

    base_directory = 'D:/RawData/3D_loc_labels/2019_05_09/'
    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/dets_3d_filtered/'
        # if not os.path.exists(store_directory):
        #     os.makedirs(store_directory)

        for file_name in os.listdir(sub_directory):
            file_directory = sub_directory + file_name
            # store_file_directory = store_directory + file_name

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

            # print(alist[0][3])
            # print(alist[0])
            # input()
            z_box = get_z_box(alist)
            #print(z_box)

            tracker_list = pipeline(z_box) 
            print(tracker_list)
            input()

            



if __name__ == "__main__":
    main()

    # det = detector.CarDetector()
    
    # if debug: # test on a sequence of images
    #     images = [plt.imread(file) for file in glob.glob('./test_images/*.jpg')]
        
    #     for i in range(len(images))[0:7]:
    #          image = images[i]
    #          image_box = pipeline(image)   
    #          plt.imshow(image_box)
    #          plt.show()
           
    # else: # test on a video file.
        
    #     start=time.time()
    #     output = 'test_v7.mp4'
    #     clip1 = VideoFileClip("project_video.mp4")#.subclip(4,49) # The first 8 seconds doesn't have any cars...
    #     clip = clip1.fl_image(pipeline)
    #     clip.write_videofile(output, audio=False)
    #     end  = time.time()
        
    #     print(round(end-start, 2), 'Seconds to finish')