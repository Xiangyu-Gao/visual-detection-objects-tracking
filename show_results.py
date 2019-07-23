import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def show_image(base_directory):
    
    for subfolder in os.listdir(base_directory):
        sub_directory = base_directory + '/' + subfolder + '/viz_3d_loc/'
        result_directory = base_directory + '/' + subfolder + '/dets_3d_track_filtered/'
        
        for file_name in os.listdir(sub_directory):
                img_directory = sub_directory + file_name
                res_directory = result_directory + file_name[0:10] + '.txt'
                im = np.array(Image.open(img_directory), dtype=np.uint8)
                print(im.shape)
                # Create figure and axes
                fig,ax = plt.subplots(1)

                # Display the imageshow
                ax.imshow(im)

                # read the boudning box
                # input()
                with open(res_directory) as f:
                    data = f.read().splitlines()
                    alist = []
                    for line in data:
                        if line == '':
                            pass
                        else:
                            alist.append(line.split(','))
                f.close()

                for elem in alist:
                    pos_le = int(elem[7]) + 250
                    pos_bo = int(elem[4]) + 500
                    wid = abs(int(elem[4])-int(elem[6]))
                    hei = abs(int(elem[5])-int(elem[7]))

                    obj_class = int(elem[0])
                    # Create a Rectangle patch
                    if obj_class == 0:
                        rect = patches.Rectangle((pos_bo,pos_le), wid, hei, linewidth=2, edgecolor='r', facecolor='none')
                    elif obj_class == 1:
                        rect = patches.Rectangle((pos_bo, pos_le), wid, hei, linewidth=2, edgecolor='g',facecolor='none')
                    elif obj_class == 2:
                        rect = patches.Rectangle((pos_bo, pos_le), wid, hei, linewidth=2, edgecolor='b',facecolor='none')
                    else:
                        pass

                    # Add the patch to the Axes
                    ax.add_patch(rect)

                plt.show()
                plt.pause(.1)
                # plt.close(ax)






if __name__ == "__main__":
    base_directory = 'D:/RawData/3D_loc_labels/2019_05_09/'
    show_image(base_directory)