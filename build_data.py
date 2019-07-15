import tensorflow as tf
import random
import os
import time

try:
  from os import scandir
except ImportError:
  # Python 2 polyfill module
  from scandir import scandir
    

FLAGS = tf.flags.FLAGS

tf.flags.DEFINE_string('X_input_dir', 'data/trainA',
                       'X input directory, default: data/trainA')
tf.flags.DEFINE_string('Y_input_dir', 'data/trainB',
                       'Y input directory, default: data/trainB')
tf.flags.DEFINE_string('X_output_file', 'data/tfrecords/trainA.tfrecords',
                       'X output tfrecords file, default: data/tfrecords/trainA.tfrecords')
tf.flags.DEFINE_string('Y_output_file', 'data/tfrecords/trainB.tfrecords',
                       'Y output tfrecords file, default: data/tfrecords/trainB.tfrecords')

tf.flags.DEFINE_string('X_input_dir_test', 'data/testA',
                       'X input directory, default: data/testA')
tf.flags.DEFINE_string('Y_input_dir_test', 'data/testB',
                       'Y input directory, default: data/testB')
tf.flags.DEFINE_string('X_output_file_test', 'data/tfrecords/testA.tfrecords',
                       'X output tfrecords file, default: data/testA.tfrecords')
tf.flags.DEFINE_string('Y_output_file_test', 'data/tfrecords/testB.tfrecords',
                       'Y output tfrecords file, default: data/tfrecords/testB.tfrecords')

copy_file_count=0

def copy_certain_number_file(source_dir, start_index, number, image_name_start_index, target_A_dir, target_B_dir):
  """
  copyt source folder special index files
  """
  print(source_dir)
  files = os.listdir(source_dir)
  #按照文件名去掉后四个字符（.jpg扩展名）转换成数值进行排序
  #files.sort(key=lambda x: int(x[:-4]))
  files.sort(key=lambda x: x.lower())

  if (start_index + number) > len(files):
    return

  random_index=random.randint(0, number-1)

  for i in range(number):
    source_f = os.path.join(source_dir, files[start_index + i])
    target_file = '%06d.jpg' % (image_name_start_index + i)
    target_B_file = os.path.join(target_B_dir, target_file)
    if random_index==i:
      target_A_file = os.path.join(target_A_dir, target_file)
    print(files[start_index + i])

    if os.path.isfile(source_f):
      if not os.path.exists(target_A_dir):
        os.makedirs(target_A_dir)
      if not os.path.exists(target_B_dir):
        os.makedirs(target_B_dir)
      #文件创建+填写=文件拷贝
      file_data=open(source_f, "rb").read()
      open(target_B_file, "wb").write(file_data)
      if random_index == i:
        open(target_A_file, "wb").write(file_data)
      print("%s %s 复制完毕" %(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), source_f))


def copy_clip_frames(filename, target_A_dir, target_B_dir, start_index, batch_size, num_frames_per_clip=16):
  """
  :param filename: train.list or test.list
  :param target_dir: target director, e.g. "trainA"
  :param start_index: start index of the clipper list, base on 0
  :param batch_size: number of clippser to copy
  :param num_frames_per_clip: number of frames per clipper
  :return:
  """
  lines = open(filename,'r')
  batch_index = 0
  image_name_index = start_index * num_frames_per_clip
  next_batch_start = -1
  lines = list(lines)

  print("filename :" + filename)
  print("target_A_dir :" + target_A_dir)
  print("target_B_dir :" + target_B_dir)
  print("start_index : %d" % start_index)
  print("batch_size : %d" % batch_size)
  print("num_frames_per_clip : %d" % num_frames_per_clip)

  if (start_index + batch_size) > len(lines):
    return
  if start_index < 0:
    start_index = 0

  for index in range(start_index, len(lines)):
    if(batch_index>=batch_size):
      #next_batch_start = index
      break
    line = lines[index].strip('\n').split()
    dirname = line[0]
    #tmp_label = line[1]
    clip_start_index = int(line[2])

    print("start_index: %d" %(start_index))
    print("dirname: " + dirname)
    print("clip_start_index: %d" % int(clip_start_index))
    print("image_name_index: %d" % int(image_name_index))
    #print("dirname : " + dirname)
    #print("tmp_label: %d" % int(tmp_label))
    #print("tmp_start_index: %d" % int(tmp_start_index))
    #20190508 su sta 传入起始数据帧下标，取指定范围的数据帧
    copy_certain_number_file(dirname, int(clip_start_index), num_frames_per_clip, image_name_index, target_A_dir, target_B_dir)
    batch_index = batch_index + 1
    image_name_index = image_name_index + num_frames_per_clip

  return (start_index + index)

def copy_source(source_dir, target_dir):
  """
  copy source images to target dir for build tfrecords
  author: su
  :param source_dir: 
  :param target_dir: 
  :return: 
  """
  global copy_file_count
  print(source_dir)
  print("%s 当前处理文件夹%s已处理%s 个文件"
        %(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), source_dir, copy_file_count))
  for f in os.listdir(source_dir):
    sourcr_f = os.path.join(source_dir, f)
    target_file = '%06d.jpg' % (copy_file_count)
    target_file = os.path.join(target_dir, target_file)

    if os.path.isfile(sourcr_f):
      if not os.path.exists(target_dir):
        os.makedirs(target_dir)
      copy_file_count+=1
      #文件创建+填写=文件拷贝
      open(target_file, "wb").write(open(sourcr_f, "rb").read())
      print("%s %s 复制完毕" %(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), target_file))

    if os.path.isdir(sourcr_f):
      copy_source(sourcr_f, target_dir)

def data_reader(input_dir, shuffle=True):
  """Read images from input_dir then shuffle them
  Args:
    input_dir: string, path of input dir, e.g., /path/to/dir
  Returns:
    file_paths: list of strings
  """
  file_paths = []

  for img_file in scandir(input_dir):
    if img_file.name.endswith('.jpg') and img_file.is_file():
      file_paths.append(img_file.path)

  if shuffle:
    # Shuffle the ordering of all image files in order to guarantee
    # random ordering of the images with respect to label in the
    # saved TFRecord files. Make the randomization repeatable.
    shuffled_index = list(range(len(file_paths)))
    random.seed(12345)
    random.shuffle(shuffled_index)

    file_paths = [file_paths[i] for i in shuffled_index]

  return file_paths


def _int64_feature(value):
  """Wrapper for inserting int64 features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _bytes_feature(value):
  """Wrapper for inserting bytes features into Example proto."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _convert_to_example(file_path, image_buffer):
  """Build an Example proto for an example.
  Args:
    file_path: string, path to an image file, e.g., '/path/to/example.JPG'
    image_buffer: string, JPEG encoding of RGB image
  Returns:
    Example proto
  """
  file_name = file_path.split('/')[-1]

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/file_name': _bytes_feature(tf.compat.as_bytes(os.path.basename(file_name))),
      'image/encoded_image': _bytes_feature((image_buffer))
    }))
  return example

def data_writer(input_dir, output_file):
  """Write data to tfrecords
  """
  file_paths = data_reader(input_dir)

  # create tfrecords dir if not exists
  output_dir = os.path.dirname(output_file)
  try:
    os.makedirs(output_dir)
  except os.error as e:
    pass

  images_num = len(file_paths)

  # dump to tfrecords file
  writer = tf.python_io.TFRecordWriter(output_file)

  for i in range(len(file_paths)):
    file_path = file_paths[i]

    with tf.gfile.FastGFile(file_path, 'rb') as f:
      image_data = f.read()

    example = _convert_to_example(file_path, image_data)
    writer.write(example.SerializeToString())

    if i % 500 == 0:
      print("Processed {}/{}.".format(i, images_num))
  print("Done.")
  writer.close()

def main(unused_argv):
  # print("Convert X data to tfrecords...")
  # data_writer(FLAGS.X_input_dir, FLAGS.X_output_file)
  # print("Convert Y data to tfrecords...")
  # data_writer(FLAGS.Y_input_dir, FLAGS.Y_output_file)
  # print("copy_source test")
  # copy_source('test_source_dir', 'test_target_dir')

  # print("copy_folder_specil_index_file test")
  # copy_certain_number_file('test_source_dir/c1', 1, 2, 1, 'test_target_dir/testA', 'test_target_dir/testB')

  # 从UCF101的clips中拷贝生成tfrecord用的图片
  print("copy_clip_frames test")
  copy_clip_frames('train.list', 'data/trainA', 'data/trainB', 0, 3)
  copy_clip_frames('test.list', 'data/testA', 'data/testB', 0, 3)
  # copy_clip_frames('train.list', 'data/trainA', 'data/trainB', 0, 9000)
  # copy_clip_frames('test.list', 'data/testA', 'data/testB', 0, 3000)

  # 生成tfrecords文件
  # print("Convert X data to tfrecords...")
  # data_writer(FLAGS.X_input_dir, FLAGS.X_output_file)
  # print("Convert Y data to tfrecords...")
  # data_writer(FLAGS.Y_input_dir, FLAGS.Y_output_file)
  # print("Convert X data to tfrecords...")
  # data_writer(FLAGS.X_input_dir_test, FLAGS.X_output_file_test)
  # print("Convert Y data to tfrecords...")
  # data_writer(FLAGS.Y_input_dir_test, FLAGS.Y_output_file_test)

if __name__ == '__main__':
  tf.app.run()
