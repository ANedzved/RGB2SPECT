import cv2

import numpy as np
from skimage import morphology
from matplotlib import pyplot as plt

# Обнаружение области корней на изображении
def detectarearoot(img):
    # Извлечение ширины и высоты изображения
    height = img.shape[0]
    width = img.shape[1]
    #channels = img.shape[2]
    if height > 750 : # Изменение размера изображения, чтобы высота стала 750 пикселей с сохранением пропорций
        dim = (int(width*(750/height)), 750)
        img=cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        height = img.shape[0]
        width = img.shape[1]

    sx=int(width)
    sy=int(0.15*height) 
    
    # Выделение верхней части изображения, затем нижней части изображения
    cropped_image = img[0:sy, 0:sx]
    
    avg_color_per_row = np.average(cropped_image, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    dim = (width, 1)
    a1img=cv2.resize(cropped_image, dim, interpolation = cv2.INTER_LINEAR )
    
    
    cropped_image = img[height-sy:height, 0:sx]
    dim = (width, 1)
    a2img=cv2.resize(cropped_image, dim, interpolation = cv2.INTER_LINEAR )
    
    blank_image = np.zeros((2,width,3), np.uint8) # Создание пустого изображения размером двойной ширины изображения
    blank_image[0,:,:]=a1img
    blank_image[1,:,:]=a2img
    dim = (width,height)
    a1img=cv2.resize(blank_image, dim, interpolation = cv2.INTER_CUBIC ) # Изменение размера верхней и нижней частей изображения до исходной ширины и высоты
    ksize = (10, 10)
    a1img = cv2.blur(a1img, ksize) 
    avg_color_per_row = np.average(cropped_image, axis=0) # Расчет среднего цвета для верхней части изображения
    avg_color = np.average(avg_color_per_row, axis=0) # Вычитание среднего цвета из исходного изображения
    a1=avg_color.astype(int)
    
    print(a1)
    
    img0=img.astype(np.float16)-a1img
    img0[img0<0]=0
    img1=img0.astype(np.uint8)
    imghsv = cv2.cvtColor(img1, cv2.COLOR_BGR2HLS)# Преобразование изображения в оттенки серого
    imgg=imghsv[:,:,1]
    
    
    
    ret,im_th = cv2.threshold(imgg, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) # Применение пороговой фильтрации для получения бинарного изображения
    # Толщина стекла
    dglass = 0.025 * height
    d = int(dglass / 2)
    dglass = int(dglass)
    print(dglass)
    
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(d, d))
    im_th = cv2.morphologyEx(im_th, cv2.MORPH_CLOSE, kernel) # Применение морфологической операции "закрытие" для заполнения областей и объединения близко расположенных пикселей
    
    im_floodfill = im_th.copy()
    # Применение алгоритма заливки для заполнения области корней
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(im_floodfill, mask, (0,0), 255);
    im_floodfill_inv = cv2.bitwise_not(im_floodfill) # Создание маски для эрозии изображения с помощью морфологической операции "эрозия"
    imgb = im_th | im_floodfill_inv   
    
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    
    mask = cv2.erode(imgb,kernel,iterations = dglass)
    imgb = cv2.bitwise_and(img1, img1, mask=mask)
    
    # имеем содержимое чашки
    # ищем протяженные объекты
    
    gray = cv2.cvtColor(imgb, cv2.COLOR_BGR2GRAY) # Преобразование изображения в оттенки серого
    
    
    kernel1 = np.array((
            [0, 0, 1,-1, 1],
            [0, 1,-1, 1, 0],
            [1,-1, 1, 0, 0],
            ), np.uint8)
    
    kernel2 = np.array((
            [1,-1, 1, 0, 0],
            [0, 1,-1, 1, 0],
            [0, 0, 1,-1, 1],
            ), np.uint8)
    
    kernel = np.array((
              [ 1, -1, 1 ],
              [ 1, -1, 1 ],
              [ 1, -1, 1 ],
              ), np.uint8)
    
    # Применение морфологических операций открытия и закрытия(tophat) с различными ядрами для выделения корней
    gray = cv2.cvtColor(imgb, cv2.COLOR_BGR2GRAY)
    imgb0 = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    imgb1 = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel1)
    imgb2 = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel2) 
    
    imgb = cv2.bitwise_or(imgb0, imgb1)
    imgb = cv2.bitwise_or(imgb, imgb2)
    
    # Применение пороговой фильтрации для получения бинарного изображения корней
    ret,img1 = cv2.threshold(imgb, 5, 255, cv2.THRESH_BINARY)

    # Удаление маленьких объектов на изображении с помощью операции удаления малых объектов
    cleaned = morphology.remove_small_objects(img1, min_size=50, connectivity=2)
    # Подсчет количества связанных компонентов на изображении и удаление небольших компонентов, сохраняя только компоненты большого размера
    nb_blobs, im_with_separated_blobs, stats, _ = cv2.connectedComponentsWithStats(img1)
    # Нас интересует только размер больших двоичных объектов, содержащийся в последнем столбце статистики
    sizes = stats[:, -1]
    sizes = sizes[1:]
    nb_blobs -= 1
    min_size = 50  
    im_result = np.zeros_like(im_with_separated_blobs).astype(np.uint8) # Изображение только с сохраненными компонентами
    # Создание итогового изображения, где корни обозначены белым цветом, а фон - черным
    for blob in range(nb_blobs):
        if sizes[blob] >= min_size:
            # see description of im_with_separated_blobs above
            im_result[im_with_separated_blobs == blob + 1] = 255
    
    
    img1=im_result
    return im_result
    
    
if __name__ == '__main__':
    import sys
    from PyQt5 import QtGui, QtCore, QtWidgets


    
