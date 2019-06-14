import torch
from .abstract_datasets import DetectionDataset 
from PIL import Image
import os
import numpy as np
import json

class ImageNetVID(DetectionDataset):
    def __init__(self, *args, **kwargs):
        super(ImageNetVID, self).__init__(*args, **kwargs)

        lab_file = open('/z/home/erichof/datasets/ILSVRC2015/labels_number_keys.json', 'r')
        self.labels_dict = json.load(lab_file)
        lab_file.close()
        self.label_values = list(self.labels_dict.values())
        self.label_values.sort()


        # Maximum number of annotated object present in a single frame in entire dataset
        # Dictates the return size of annotations in __getitem__
        self.max_objects = 22

    def __getitem__(self, idx):
        vid_info = self.samples[idx]
        
        base_path = vid_info['base_path']
        vid_size  = vid_info['frame_size']

        vid_data   = np.zeros((self.clip_length, self.final_shape[0], self.final_shape[1], 3))-1
        bbox_data  = np.zeros((self.clip_length, self.max_objects, 4))-1
        labels     = np.zeros((self.clip_length, self.max_objects))-1
        occlusions = np.zeros((self.clip_length, self.max_objects))-1




        for frame_ind in range(len(vid_info['frames'])):
            frame      = vid_info['frames'][frame_ind]
            frame_path = frame['img_path']
            
            # Extract bbox and label data from video info
            for obj in frame['objs']:
                trackid   = obj['trackid']
                label     = obj['c']
                occlusion = obj['occ']
                obj_bbox  = obj['bbox'] # [xmin, ymin, xmax, ymax]

                label_name = self.labels_dict[label]
                label      = self.label_values.index(label_name)


                bbox_data[frame_ind, trackid, :] = obj_bbox
                labels[frame_ind, trackid]       = label 
                occlusions[frame_ind, trackid]   = occlusion

            # Load frame image data, preprocess image, and augment bounding boxes accordingly
            # TODO: Augment bounding boxes according to frame augmentations 
            vid_data[frame_ind], bbox_data[frame_ind] = self._preprocFrame(os.path.join(base_path, frame_path), bbox_data[frame_ind])


        bbox_data = bbox_data.astype(int)

        xmin_data  = torch.from_numpy(bbox_data[:,:,0])
        ymin_data  = torch.from_numpy(bbox_data[:,:,1])
        xmax_data  = torch.from_numpy(bbox_data[:,:,2])
        ymax_data  = torch.from_numpy(bbox_data[:,:,3])
        vid_data   = torch.from_numpy(vid_data)
        labels     = torch.from_numpy(labels)
        occlusions = torch.from_numpy(occlusions)

        # Permute the PIL dimensions (Frame, Height, Width, Chan) to pytorch (Chan, frame, height, width) 
        vid_data = vid_data.permute(3, 0, 1, 2)


        ret_dict = dict() 
        ret_dict['data']       = vid_data 
        ret_dict['xmin']       = xmin_data
        ret_dict['ymin']       = ymin_data
        ret_dict['xmax']       = xmax_data
        ret_dict['ymax']       = ymax_data
        ret_dict['labels']     = labels
        ret_dict['occlusions'] = occlusions

        return ret_dict

    # TODO Move to VideoDataset._preprocFrame
    def resize_bbox(self, xmin, xmax, ymin, ymax, img_shape, resize_shape):
        # Resize a bounding box within a frame relative to the amount that the frame was resized

        img_h = img_shape[0]
        img_w = img_shape[1]

        res_h = resize_shape[0]
        res_w = resize_shape[1]

        frac_h = res_h/float(img_h)
        frac_w = res_w/float(img_w)

        xmin_new = int(xmin * frac_w)
        xmax_new = int(xmax * frac_w)

        ymin_new = int(ymin * frac_h)
        ymax_new = int(ymax * frac_h)

        return xmin_new, xmax_new, ymin_new, ymax_new 


#dataset = ImageNetVID(json_path='/z/home/erichof/datasets/ILSVRC2015', dataset_type='train')
#dat = dataset.__getitem__(0)
#import pdb; pdb.set_trace()
