#!/bin/bash

# convert the images folder to the test.list and train.list file according to
#   the distribution, command will clear the train.list and test.list files first
#
#   Args:
#       path: the path to the video folder
#       factor: denominator that split the train and test data. if the number 
#               is 4, then 1/4 of the data will be written to test.list and the
#               rest of the data will be written to train.list
#   Usage:
#       ./convert_images_to_list.sh path/to/video 4
#   Example Usage:
#       ./convert_images_to_list.sh ~/document/videofile 4
#   Example Output(train.list and test.list):
#       /Volumes/passport/datasets/action_kth/origin_images/boxing/person01_boxing_d1_uncomp 0
#       /Volumes/passport/datasets/action_kth/origin_images/boxing/person01_boxing_d2_uncomp 0
#       ...
#       /Volumes/passport/datasets/action_kth/origin_images/handclapping/person01_handclapping_d1_uncomp 1
#       /Volumes/passport/datasets/action_kth/origin_images/handclapping/person01_handclapping_d2_uncomp 1
#       ...

# 20190508 su sta
# 1. 为便于测试验证，测试与验证集合数据强制按比例分配
# 2. 为便于后面确认参与训练，测试的数据帧范围，在list中标出参与的数据帧起始下标和个数
# 20190508 su end

#先删除train.list和test.list文件
> train.list
> test.list
COUNT=-1
NUMB_FRAMES_PER_CLIP=16
for folder in $1/*
do
    COUNT=$[$COUNT + 1]
    TOTAL_COUNT=0
    TRAIN_COUNT=0
    TEST_COUNT=0
    for imagesFolder in "$folder"/*
    do
        ADD_TO_TRAIN_LIST=1
        if (($TOTAL_COUNT < 15)); then
            #前15条随机分（大体看了图片数据，每类中有25个图片文件夹），后面的则要考虑训练测试比率进行分配训练和测试数据
            #jot -r 1 1 $2, 使用jot产生随机数（-r）一个（-r后面的第一个数值1标示），范围从1到$2,左右都是闭区间，$2是调用脚本时传入的第二个参数
            #这样使用容易产生部分例子只在train.list或test.list中，测试时可能出现正确率为0的情况
            if (( $(jot -r 1 1 $2)  > 1 )); then
                TRAIN_COUNT=$[$TRAIN_COUNT + 1]
            else
                TEST_COUNT=$[$TEST_COUNT + 1]
                ADD_TO_TRAIN_LIST=0
            fi
        else
            if (($TEST_COUNT > 0)); then
                if (($(expr $TRAIN_COUNT / $TEST_COUNT) < $2)); then
                    TRAIN_COUNT=$[$TRAIN_COUNT + 1]
                else
                    TEST_COUNT=$[$TEST_COUNT + 1]
                    ADD_TO_TRAIN_LIST=0
                fi
            else
                TEST_COUNT=$[$TEST_COUNT + 1]
                ADD_TO_TRAIN_LIST=0
            fi
        fi

        START_INDEX=-1
        FILE_COUNT=$(ls | wc -w)
        if(($FILE_COUNT >= $NUMB_FRAMES_PER_CLIP)); then
            UP_BOUND=$[$FILE_COUNT - $NUMB_FRAMES_PER_CLIP];
            START_INDEX=$(jot -r 1 0 $UP_BOUND)
        fi
        if (($ADD_TO_TRAIN_LIST == 1)); then
            echo "$imagesFolder" $COUNT $START_INDEX >> train.list
        else
            echo "$imagesFolder" $COUNT $START_INDEX >> test.list
        fi
        TOTAL_COUNT=$[$TOTAL_COUNT + 1]
    done
done
