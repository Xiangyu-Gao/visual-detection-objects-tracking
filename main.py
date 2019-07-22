from filters import filter_tracking
from remover import remove_overlap
from run_kf import KF_Tracking


if __name__ == "__main__":
    base_directory = 'D:/RawData/3D_loc_labels/2019_05_29/'
    # remove overlap
    remove_overlap(base_directory)
    print('#######################'+'FINISHED REMOVING OVERLAPPING!!!!!!'+'#######################')
    # KF filtering for tracking
    KF_Tracking(base_directory)
    print('#######################'+'FINISHED KALMAN FILTERING TRACKING!!!!!!'+'#######################')
    # smooth the tracking result
    filter_tracking(base_directory)
    print('#######################'+'FINISHED SMOOTHING TRACKING!!!!!!'+'#######################')