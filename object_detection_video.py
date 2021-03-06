import argparse
import os
import sys

import cv2
import numpy as np
import tensorflow as tf

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

_PATH_TO_CKPT = 'export/export_20190214_125701/frozen_inference_graph.pb'
_PATH_TO_LABELS = 'object_detection/data/gyoza_20190208_label_map.pbtxt'
_NUM_CLASSES = 7
# _PATH_TO_CKPT = './ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb'
# _PATH_TO_LABELS = 'object_detection/data/mscoco_label_map.pbtxt'
# _NUM_CLASSES = 90

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(_PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        print(od_graph_def.ParseFromString(serialized_graph))
        tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(_PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(
    label_map,
    max_num_classes=_NUM_CLASSES,
)
category_index = label_map_util.create_category_index(categories)


def main(start_offset, video_file):

    width = 1920
    height = 1080

    # 20190907
    # threshold = int(400 / 2)  # default (224 / 2)
    # margin = 10  # not to capture bounding box

    # center_width = int(width / 2) - 300
    # center_height = int(height / 2) + 150

    # apartment
    threshold = int(300 / 2)  # default (224 / 2)
    margin = 10  # not to capture bounding box

    center_width = int(width / 2)
    center_height = int(height / 2) + 50

    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:

            cap = cv2.VideoCapture(video_file)

            # camera propety(1920x1080)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, 30)

            number_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            print('number_of_frames', number_of_frames)
            print('fps', fps)

            count = start_offset
            # start_pos = fps * start_offset
            start_pos = start_offset
            print('start_pos', start_pos)

            classes_log = np.empty((0, 100), int)
            scores_log = np.empty((0, 100), float)

            # while (True):
            for i in range(start_pos, number_of_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                frame = cv2.resize(frame, dsize=(1920, 1080))
                cv2.rectangle(frame, ((center_width - threshold - margin),
                                      (center_height - threshold - margin)),
                              ((center_width + threshold + margin),
                               (center_height + threshold + margin)),
                              (0, 0, 255), 3)

                # ROI
                bbox = frame[center_height - threshold:center_height +
                             threshold, center_width - threshold:center_width +
                             threshold]
                # _bbox = cv2.resize(bbox,(224,224))
                bbox = bbox[:, :, ::-1]
                # _bbox = bbox / 128 - 1 # normalization
                _bbox = np.expand_dims(bbox, 0)

                image_tensor = detection_graph.get_tensor_by_name(
                    'image_tensor:0')
                boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
                scores = detection_graph.get_tensor_by_name(
                    'detection_scores:0')
                classes = detection_graph.get_tensor_by_name(
                    'detection_classes:0')
                num_detection = detection_graph.get_tensor_by_name(
                    'num_detections:0')

                (boxes, scores, classes, num_detection) = sess.run(
                    [boxes, scores, classes, num_detection],
                    feed_dict={image_tensor: _bbox},
                )
                vis_util.visualize_boxes_and_labels_on_image_array(
                    bbox,
                    np.squeeze(boxes),
                    np.squeeze(classes).astype(np.int32),
                    np.squeeze(scores),
                    category_index,
                    use_normalized_coordinates=True,
                    line_thickness=20,
                    max_boxes_to_draw=20,
                )
                print('classes : {}'.format(classes.astype(np.int32)))
                print('a number of class : {} {}'.format(
                    classes.shape[0], classes.shape[1]))
                print('scores  : {}'.format(scores))
                print('a number of score : {} {}'.format(
                    scores.shape[0], scores.shape[1]))

                print(sys.stdout.write('classes_log {}'.format(classes_log)))
                print(sys.stdout.write('scores_log {}'.format(scores_log)))
                classes_log = np.append(
                    classes_log,
                    np.array([classes[0].astype(np.int32)]),
                    axis=0)
                scores_log = np.append(
                    scores_log, np.array([scores[0]]), axis=0)

                cv2.imshow('frame', frame)
                count += 1
                print(count)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    # # output log
                    # np.savetxt('classes.csv', classes_log, delimiter=',')
                    # np.savetxt('scores.csv', scores_log, delimiter=',')
                    break

            cap.release()
            cv2.destroyAllWindows()
            # # output log
            # np.savetxt('classes.csv', classes_log, delimiter=',')
            # np.savetxt('scores.csv', scores_log, delimiter=',')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        '--start_offset',
        dest='start_offset',
        type=int,
        default=0,
        help='please enter start offset (second)'
        ' that you want to start movie')
    parser.add_argument(
        '--video_file',
        dest='video_file',
        type=str,
        default=None,
        help='please enter a video file(filepath)'
        ' that you want to test movie')
    argv = parser.parse_args()
    main(argv.start_offset, argv.video_file)
