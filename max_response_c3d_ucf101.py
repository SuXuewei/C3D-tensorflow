# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# ==============================================================================
# max response function to select the key frame from the video of 16 frames
# 20190507 su
# ==============================================================================


"""Trains and Evaluates the MNIST network using a feed dictionary."""
# pylint: disable=missing-docstring
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path
import time
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
import input_data
import c3d_model
import numpy as np
import random

# Basic model parameters as external flags.
flags = tf.app.flags
gpu_num = 2
# 20190507 su sta
# 一个视频由16帧组成，每一帧生成一个16帧的视频作为输入，给c3d模型，获取该帧对应真实类的概率
# 取原始视频16帧中对应概率最大的一个，由于硬件限制批次由10降为8，一个视频生成的16个输入视频
# 分两份每份8个视频放到两个GPU上跑
# 20190507 su end
flags.DEFINE_integer('batch_size', 8, 'Batch size.')
FLAGS = flags.FLAGS
# 20190502 su sta
model_save_dir = './models/'
# 20190502 su end

def placeholder_inputs(batch_size):
  """Generate placeholder variables to represent the input tensors.
  These placeholders are used as inputs by the rest of the model building
  code and will be fed from the downloaded data in the .run() loop, below.
  Args:
    batch_size: The batch size will be baked into both placeholders.
  Returns:
    images_placeholder: Images placeholder.
    labels_placeholder: Labels placeholder.
  """
  # Note that the shapes of the placeholders match the shapes of the full
  # image and label tensors, except the first dimension is now batch_size
  # rather than the full size of the train or test data sets.
  images_placeholder = tf.placeholder(tf.float32, shape=(batch_size,
                                                         c3d_model.NUM_FRAMES_PER_CLIP,
                                                         c3d_model.CROP_SIZE,
                                                         c3d_model.CROP_SIZE,
                                                         c3d_model.CHANNELS))
  labels_placeholder = tf.placeholder(tf.int64, shape=(batch_size))
  return images_placeholder, labels_placeholder

def _variable_on_cpu(name, shape, initializer):
  #with tf.device('/cpu:%d' % cpu_id):
  with tf.device('/cpu:0'):
    var = tf.get_variable(name, shape, initializer=initializer)
  return var

def _variable_with_weight_decay(name, shape, stddev, wd):
  var = _variable_on_cpu(name, shape, tf.truncated_normal_initializer(stddev=stddev))
  if wd is not None:
    weight_decay = tf.nn.l2_loss(var) * wd
    tf.add_to_collection('losses', weight_decay)
  return var

def run_test():
  test_list_file = './test.list'
  num_test_videos = len(list(open(test_list_file,'r')))
  print("Number of test videos={}".format(num_test_videos))

  # Get the sets of images and labels for training, validation, and
  images_placeholder, labels_placeholder = placeholder_inputs(FLAGS.batch_size * gpu_num)
  with tf.variable_scope('var_name') as var_scope:
    weights = {
            'wc1': _variable_with_weight_decay('wc1', [3, 3, 3, 3, 64], 0.04, 0.00),
            'wc2': _variable_with_weight_decay('wc2', [3, 3, 3, 64, 128], 0.04, 0.00),
            'wc3a': _variable_with_weight_decay('wc3a', [3, 3, 3, 128, 256], 0.04, 0.00),
            'wc3b': _variable_with_weight_decay('wc3b', [3, 3, 3, 256, 256], 0.04, 0.00),
            'wc4a': _variable_with_weight_decay('wc4a', [3, 3, 3, 256, 512], 0.04, 0.00),
            'wc4b': _variable_with_weight_decay('wc4b', [3, 3, 3, 512, 512], 0.04, 0.00),
            'wc5a': _variable_with_weight_decay('wc5a', [3, 3, 3, 512, 512], 0.04, 0.00),
            'wc5b': _variable_with_weight_decay('wc5b', [3, 3, 3, 512, 512], 0.04, 0.00),
            'wd1': _variable_with_weight_decay('wd1', [8192, 4096], 0.04, 0.001),
            'wd2': _variable_with_weight_decay('wd2', [4096, 4096], 0.04, 0.002),
            'out': _variable_with_weight_decay('wout', [4096, c3d_model.NUM_CLASSES], 0.04, 0.005)
            }
    biases = {
            'bc1': _variable_with_weight_decay('bc1', [64], 0.04, 0.0),
            'bc2': _variable_with_weight_decay('bc2', [128], 0.04, 0.0),
            'bc3a': _variable_with_weight_decay('bc3a', [256], 0.04, 0.0),
            'bc3b': _variable_with_weight_decay('bc3b', [256], 0.04, 0.0),
            'bc4a': _variable_with_weight_decay('bc4a', [512], 0.04, 0.0),
            'bc4b': _variable_with_weight_decay('bc4b', [512], 0.04, 0.0),
            'bc5a': _variable_with_weight_decay('bc5a', [512], 0.04, 0.0),
            'bc5b': _variable_with_weight_decay('bc5b', [512], 0.04, 0.0),
            'bd1': _variable_with_weight_decay('bd1', [4096], 0.04, 0.0),
            'bd2': _variable_with_weight_decay('bd2', [4096], 0.04, 0.0),
            'out': _variable_with_weight_decay('bout', [c3d_model.NUM_CLASSES], 0.04, 0.0),
            }
  logits = []
  for gpu_index in range(0, gpu_num):
    with tf.device('/gpu:%d' % gpu_index):
      logit = c3d_model.inference_c3d(images_placeholder[gpu_index * FLAGS.batch_size:(gpu_index + 1) * FLAGS.batch_size,:,:,:,:], 0.6, FLAGS.batch_size, weights, biases)
      logits.append(logit)
  logits = tf.concat(logits,0)
  norm_score = tf.nn.softmax(logits)
  saver = tf.train.Saver()
  sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
  init = tf.global_variables_initializer()
  sess.run(init)
  # Create a saver for writing training checkpoints.
  model_file = tf.train.latest_checkpoint(model_save_dir)
  saver.restore(sess, model_file)

  write_file = open("key_frames.list", "w+")
  next_start_pos = 0
  right_count = 0
  random_right_count = 0
  random_frame_index = 0
  random_test_loop_count = 100
  top1_predicted_label = 0
  for step in xrange(num_test_videos):
    start_time = time.time()
    test_images, test_labels, next_start_pos, read_dirnames, frame_start_index = \
            input_data.read_vedio_clips_and_label(
                    test_list_file,
                    start_pos=step
                    )
    predict_score = norm_score.eval(
            session=sess,
            feed_dict={images_placeholder: test_images}
            )
    valid_len = len(test_images)
    key_frame_index = 0
    true_label = test_labels[key_frame_index]
    max_accuracy = predict_score[key_frame_index][true_label]

    #print("read_dirnames: " + read_dirnames[0])
    #print("true_label: %d" % true_label)

    for i in range(0, valid_len):
      if (max_accuracy < predict_score[i][true_label]):
        key_frame_index = i
        max_accuracy = predict_score[i][true_label]

    #统计选择关键帧情况的正确数据
    top1_predicted_label = np.argmax(predict_score[key_frame_index])
    if (top1_predicted_label == true_label):
        right_count = right_count + 1

    #统计随机选择一帧情况的正确数据
    for i in xrange(0, random_test_loop_count):
      random_frame_index = random.randrange(0,valid_len)
      top1_predicted_label = np.argmax(predict_score[random_frame_index])
      if (top1_predicted_label == true_label):
          random_right_count = random_right_count + 1

    # Write results: dircrector name, true label, frame start index, key frame index, max accuracy
    write_file.write('{} {} {} {} {}\n'.format(
      read_dirnames[key_frame_index],
      true_label,
      frame_start_index,
      key_frame_index,
      predict_score[key_frame_index][true_label]))

  accuracy = right_count / num_test_videos
  random_accuracy = random_right_count / (random_test_loop_count * num_test_videos)
  write_file.write("model file: " + model_file + "\n")
  write_file.write("total count: %d\n" % num_test_videos)
  write_file.write("right count: %d\n" % right_count)
  write_file.write("random right count: %d\n" % random_right_count)
  write_file.write("random test loop count: %d\n" % random_test_loop_count)
  write_file.write("key frame case accuracy: " + "{:.5f}\n".format(accuracy))
  write_file.write("random frame case accuracy: " + "{:.5f}\n".format(random_accuracy))
  print("model file: " + model_file)
  print("total count: %d" % num_test_videos)
  print("right count: %d" % right_count)
  print("random right count: %d" % random_right_count)
  print("random test loop count: %d" % random_test_loop_count)
  print("accuracy: " + "{:.5f}".format(accuracy))
  print("random accuracy: " + "{:.5f}".format(random_accuracy))
  write_file.close()
  print("done")

def main(_):
  run_test()

if __name__ == '__main__':
  tf.app.run()
