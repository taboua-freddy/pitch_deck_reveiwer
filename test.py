from typing import Container
import tensorflow as tf
from os.path import join
import os



src = join(os.getcwd(), "test.py")
dst = join(os.getcwd(), "test")
tf.io.gfile.copy(src, dst, True)
tf.io.gfile.rmtree(dst)
tf.io.gfile.exists()


# Container
# kitchenware
