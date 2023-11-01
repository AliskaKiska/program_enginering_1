# -*- coding: utf-8 -*-
"""ProgEngNoteBook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B74GuHQDPf2mp9kKTaw-SAfwyOWrF0nC
"""

# Commented out IPython magic to ensure Python compatibility.
import os
from keras.models import Sequential
from keras.layers import Dense, Flatten
from keras.datasets import mnist
from keras.layers import Dropout
from keras.layers import Conv2D, MaxPooling2D
import tensorflow as tf

from keras.models import load_model
from keras.preprocessing import image

from google.colab import files
import numpy as np

import numpy as np
# %matplotlib inline

"""# Подготовка данных для обучения сети"""

batch_size = 100 # Размер мини-выборки
nb_classes = 10 # Количество классов изображений
nb_epoch = 25 # Количество эпох для обучения
img_rows, img_cols = 28, 28 # Размер изображений

mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

"""# Преобразование размерности и нормализация данных
Значение интенсивности пикселей в изображении находится в интервале [0,255]. Для наших целей их необходимо нормализовать - привести к значениям в интервале [0,1].
"""

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

"""Преобразуем метки классов в удобный для обучения нейронной сети формат (one hot encoding)

"""

y_train = tf.keras.utils.to_categorical(y_train, nb_classes)
y_test = tf.keras.utils.to_categorical(y_test, nb_classes)

"""#Конструируем нейронную сеть и компилируем:
loss (функция потерь) - оценка желаемого значения относительно спрогнозированного, применим categorical_crossentropy (кроссэнтропию) - функцию штрафа, которую следует использовать для задач классификации, как у нас;
optimizer (функция оптимизации) - агоритм "подгонки" внутренних параметров (весов и смещений) модели для минимизации функции потерь, optimizer="adam". Метод вычисляет индивидуальные адаптивные скорости обучения для различных параметров из оценок первого и второго моментов градиентов. Название получено из adaptive moment estimation - адаптивной оценки момента. Есть другие варианты оптимизаторов;
metrics (метрики) - используются для мониторинга процесса тренировки и тестирования, metrics=['accuracy'] значит, что мы будем вычислять в модели не только функцию штрафа, но и число правильно классифицированных примеров
"""

print("Если у вас уже есть модель ее можно загрузить, если нет нажмите 'cancel unload'.\n")
mod = files.upload()

pt = !ls
if pt[0].find('my_model.h5') != -1:

  model = load_model('my_model.h5')

else:

  # Создаем последовательную модель нейронной сети
  model = Sequential()
  # Первый сверточный слой
  model.add(Conv2D(img_rows, (3, 3), padding='same',
                          input_shape=(img_rows, img_cols, 1), activation='relu'))
  # Второй сверточный слой
  model.add(Conv2D(img_rows, (3, 3), activation='relu', padding='same'))
  # Первый слой подвыборки
  model.add(MaxPooling2D(pool_size=(2, 2)))
  # Слой регуляризации Dropout
  model.add(Dropout(0.25))

  # Третий сверточный слой
  model.add(Conv2D(2 * img_rows, (3, 3), padding='same', activation='relu'))
  # Четвертый сверточный слой
  model.add(Conv2D(2 * img_rows, (3, 3), activation='relu'))
  # Второй слой подвыборки
  model.add(MaxPooling2D(pool_size=(2, 2)))
  # Слой регуляризации Dropout
  model.add(Dropout(0.25))
  # Слой преобразования данных из 2D представления в плоское
  model.add(Flatten())
  # Полносвязный слой для классификации
  model.add(Dense(8 * img_rows, activation='relu'))
  # Слой регуляризации Dropout
  model.add(Dropout(0.5))
  # Выходной полносвязный слой
  model.add(Dense(nb_classes, activation='softmax'))

  #________________________________________________
  model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
  print(model.summary())

  #Обучаем модель
  model.fit(x_train,y_train,epochs=5)
  #Сохраняем модель
  model.save('my_model.h5')
  #Для удаления старой модели:
  #del model
  #Для загрузки модели:
  #model = load_model('my_model.h5')

#Простая оценка
model.evaluate(x_test,  y_test, verbose=2)

import cv2
from google.colab.patches import cv2_imshow
import numpy as np
import pandas as pd
from copy import deepcopy

def count_spot_stack(image, x, y): #количественная оценка "пятна"
  mx, my = image.shape
  res=0
  xl, xr, yl, yr = x, x, y, y
  stack={(x, y)}
  while stack:
    pixel=stack.pop()
    if not image[pixel]:
      res+=1
      x, y = pixel

      if x < xl:
        xl = x
      elif x > xr:
        xr = x
      if y < yl:
        yl = y
      elif y > yr:
        yr = y

      stack|=set(pix for pix in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)] if (0<=pix[0]<mx and 0<=pix[1]<my))
      image[pixel]=True
  del stack
  return {"value": res, "bounds": (xl, xr, yl, yr)}

def find_spots(image): #Поиск пятен на изображении
  id=0
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if image[x, y]==0:
        mask=deepcopy(image)
        temp = count_spot_stack(image, x, y)
        xl, xr, yl, yr = temp["bounds"]
        xx=(xr-xl+1)//28*3
        yy=(yr-yl+1)//28*3
        xl-=xx
        xr+=xx
        yl-=yy
        yr+=yy
        mask&=image
        yield {"id": id} | temp | {"mask": deepcopy(mask[xl:xr+1, yl:yr+1])}
        del mask
        id+=1

def color_spots(image, color, spots): #Окрашивание набора пятен в один цвет
  try:
    img=cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
  except:
    img=deepcopy(image)

  color=tuple(reversed(color))
  mask_bin=np.full(image.shape[:2], True)
  mask1=img*0
  for spot in spots:
    xl, xr, yl, yr = spot["bounds"]
    mask_bin[xl:xr+1, yl:yr+1]+=spot["mask"]
  mask2=deepcopy(img)
  mask2[:, :]=0
  mask2[mask_bin==True]=(255, 255, 255)
  mask1=mask2/np.array([255,255,255])
  img[mask_bin==True]=(255, 255, 255)
  return img*(1-mask1+mask1*np.array(color)/np.array([255,255,255]))



def color_spots_cond(image, spots, color_cond): #Окрашивание набора пятен в зависимости от указанных в color_cond условий
  try:
    img=cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
  except:
    img=deepcopy(image)

  color_cond={tuple(reversed(color)): cond for color, cond in color_cond.items()}
  if (255, 255, 255) not in color_cond:
      color_cond|={(255, 255, 255): lambda spot: True}
  masks_bin={color: np.full(img.shape[:2], 0) for color in color_cond}
  mask1=img*0
  for spot in spots:
    xl, xr, yl, yr = spot["bounds"]
    for color, cond in color_cond.items():
      if cond(spot):
        masks_bin[color][xl:xr+1, yl:yr+1]+=spot["mask"]
        break
  for color, mask_bin in masks_bin.items():
    img[mask_bin==255]=color

  return img


def make_table(spots, word_cond):
    df=pd.DataFrame([{"id": spot["id"], "value":spot["value"], "left":spot["bounds"][0], "up":spot["bounds"][2], "right":spot["bounds"][1], "down":spot["bounds"][3]} for spot in spots])
    word_cond=word_cond|{"Вне классификации" : lambda spot: True}
    words=[]
    for spot in spots:
        for word, cond in word_cond.items():
            if cond(spot):
                words.append(word)
                break
    df["word"] = words
    return df

porog=255-75

img_load = files.upload()
for i in img_load.keys():
  pass

img = cv2.imread(i, cv2.IMREAD_GRAYSCALE)


img2 = deepcopy(img)
img2[img2<=porog]=0
img2[img2>porog]=255
img2.dtype=np.uint8

result=""
for spot in find_spots(deepcopy(img2)):
  temp=cv2.resize(spot["mask"], (28,28), interpolation = cv2.INTER_AREA)
  temp=temp.reshape(1,28,28,1)
  temp=1-temp/255
  prediction = model.predict([temp], verbose=0)[0]
  result+=str(np.argmax(prediction))

print(result)