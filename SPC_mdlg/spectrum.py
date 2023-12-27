import colour

import numpy as np
import math as m

from SPC_mdlg.spec2rgb import ColourSystem
from PIL import Image
from colour import algebra
from deconvolution import Deconvolution

koef = np.array([ 0.31882265,  0.32213316,  0.32502251,  0.32779818,  0.33043881,
        0.33257235,  0.3342477 ,  0.33542576,  0.33626229,  0.33738184,
        0.3392991 ,  0.34233832,  0.35519391,  0.4073947 ,  0.33161019,
        0.32643071,  0.32320322,  0.32047572,  0.31765365,  0.31934682,
        0.32288776,  0.32679227,  0.34266206,  0.9021497,  0.62763606,
        0.48886961,  0.46912303,  0.46964774,  0.4695014 ,  0.46950603,
        0.46931944,  0.37471236,  0.36826355,  0.36418711,  0.36021436,
        0.36352626,  0.36694935,  0.37010136,  0.37352739,  0.37708051,
        0.38020615,  0.38512596,  0.46923212,  0.46983945,  0.46821843,
        0.46975067,  0.46861531,  0.46719991,  0.46637595,  0.46401847,
        0.46034698,  0.45481294,  0.44827728,  0.44100904,  0.43263152,
        0.42388046,  0.41542684,  0.40438543,  0.39285752,  0.58070652])


# Ортогонализация векторов с помощью метода Грама-Шмидта
def GramSchmidt(*a): 
    k = len(a[0]) # Количество компонент в каждом векторе
    N = len(a); # Количество векторов, переданных в функцию
    b = [[0] * k for i in range(N)] # Список, который будет содержать ортогональные векторы
    b[0] = a[0]
    for i in range(1,N): # Вычисление проекции текущего вектора a[i] на каждый из уже ортогонализованных векторов b[j]
        sum = a[i]
        for j in range(0,i):
            scolar_ab=0
            scolar_bb=0
            proj=[i for i in range(k)]
            for n in range(k):
                scolar_ab += b[j][n]*a[i][n] # Скалярное произведение векторов b[j] и a[i]
                scolar_bb += b[j][n]*b[j][n]
            for n in range(k):
                proj[n] = (scolar_ab/scolar_bb)*b[j][n] # Проекция
            for n in range(k):
                sum[n] -= proj[n] # Проекция вычитается, чтобы получить новый вектор sum
        b[i] = sum
    return b;


def spectral_color(l):
    t = r = g =  b = 0.0 # Переменные для вычисления значений компонент цвета
    if ((l >= 400.0) and (l < 410.0)):
        t = (l - 400.0)/(410.0 - 400.0)
        r = +(0.33*t) - (0.20*t*t)
        
    elif ((l >= 410.0) and (l < 475.0)):
        t = (l - 410.0)/(475.0 - 410.0)
        r = 0.14 - (0.13*t*t)
        
    elif ((l >= 545.0) and (l < 595.0)):
        t = (l - 545.0)/(595.0 - 545.0)
        r = +(1.98*t) - (t*t)
        
    elif ((l >= 595.0) and (l < 650.0)):
        t = (l - 595.0)/(650.0 - 595.0)
        r = 0.98 + (0.06*t) - (0.40*t*t)
        
    elif ((l >= 650.0) and (l < 700.0)):
        t = (l - 650.0)/(700.0 - 650.0)
        r = 0.65 - (0.84*t) + (0.20*t*t)
        
    if ((l >= 415.0) and (l < 475.0)):
        t = (l - 415.0)/(475.0 - 415.0)
        g = +(0.80*t*t)
            
    elif ((l >= 475.0) and (l < 590.0)): 
        t =(l - 475.0)/(590.0 - 475.0)
        g = 0.8 + (0.76*t) - (0.80*t*t)
        
    elif ((l >= 585.0) and (l < 639.0)):
        t =(l - 585.0)/(639.0 - 585.0)
        g = 0.84 - (0.84*t)           
        
    if ((l >= 400.0) and (l < 475.0)): 
        t = (l - 400.0)/(475.0-  400.0)
        b = +(2.20*t)-(1.50*t*t)
        
    elif ((l >= 475.0) and (l < 560.0)): 
        t = (l - 475.0)/(560.0 - 475.0)
        b = 0.7 - (t) + (0.30*t*t)
        
    return [r,g,b]


# Используя заданные диапазоны значений длины волны, вычисляем компоненты цвета R, G, B
def spectral2color(w):
    if w >= 380 and w < 440:
        R = -(w - 440.) / (440. - 380.)
        G = 0.0
        B = 1.0
    elif w >= 440 and w < 490:
        R = 0.0
        G = (w - 440.) / (490. - 440.)
        B = 1.0
    elif w >= 490 and w < 510:
        R = 0.0
        G = 1.0
        B = -(w - 510.) / (510. - 490.)
    elif w >= 510 and w < 580:
        R = (w - 510.) / (580. - 510.)
        G = 1.0
        B = 0.0
    elif w >= 580 and w < 645:
        R = 1.0
        G = -(w - 645.) / (645. - 580.)
        B = 0.0
    elif w >= 645 and w <= 780:
        R = 1.0
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    return [R,G,B]


## Возвращает матрицу поворота в трехмерном пространстве вокруг одной из осей
# Матрицу поворота вокруг оси X
def Rx(theta):
  return np.matrix([[ 1, 0           , 0           ],
                   [ 0, m.cos(theta),-m.sin(theta)],
                   [ 0, m.sin(theta), m.cos(theta)]])

# Матрицу поворота вокруг оси Y 
def Ry(theta):
  return np.matrix([[ m.cos(theta), 0, m.sin(theta)],
                   [ 0           , 1, 0           ],
                   [-m.sin(theta), 0, m.cos(theta)]])
 
# Матрицу поворота вокруг оси X
def Rz(theta):
  return np.matrix([[ m.cos(theta), -m.sin(theta), 0 ],
                   [ m.sin(theta), m.cos(theta) , 0 ],
                   [ 0           , 0            , 1 ]]) 


class ColourDeconvolution:
    
    def __init__(self, imgc, vl=int((750 - 380)/5)):
        self.vlen = vl
        self.im = imgc
        self.RGB = []
        self.spc = []
    
    def CycleDeconv(self,i):
        a1 = self.RGB[i]
        
        if(a1[0] == 0 and a1[1] == 0 and a1[2] == 0):
            return 0
        
        # Создание списков
        bb1 = [a1[0],a1[1],a1[2]] 
        bb2 = bb3 = [0.5, 0.5, 0.5]
        
        #Выполнение ортогонализации Грама-Шмидта
        b1, b2, b3 = GramSchmidt(bb1, bb2, bb3)
        
        decimg = Deconvolution(image=self.im,basis=[b1, b2]) # Деконволюция изображения
        
        layer1, layer2 = decimg.out_images(mode=[0, 1]) # Извлечение слоев изображений
        
        hsv_img = layer1.convert('HSV') # Преобразование layer1 в цветовое пространство HSV
        hsv = np.array(hsv_img)
        #hsv[..., 0] = (hsv[..., 2])*(hsv[..., 1]/255) # Преобразование значения цветового канала
        
        k = koef[i] # Вычисление значения коэффициента k
       
        hsv[..., 0] = (hsv[..., 2]) # Преобразование значения цветового канала
        
        new_img = Image.fromarray(hsv, 'HSV')
        im1 = Image.Image.split(new_img) # Разделение изображения new_img на каналы
        
        v = np.mean(im1[0]) # Вычисление среднего значения пикселей в первом канале
        v/= 255*k # Нормализация
        self.spc[i]=v
        return v
        
    def img2spect(self):
        global koef  # Установка глобальной переменной koef
    
        color_space = 'CIERGB'
        cs_ciergb  = ColourSystem(cs=color_space, start=380, end=750, num=self.vlen) # Создание объекта цветовой системы
        self.RGB = cs_ciergb.get_transform_matrix() # Получение матрицы преобразования цветового пространства CIERGB
        
        RGBn=self.RGB.copy() # Создание копии матрицы
        RGBn*=-1 # Умножение матрицы на -1
        RGBn[RGBn<0] = 0 # Обеспечить неотрицательные значения в матрице
        self.RGB[self.RGB<0] = 0
        #width, height = self.im.size
        self.spc = np.zeros(self.vlen)
        
        for i in range(self.vlen):
             self.CycleDeconv(i)
        return self.spc
				

    def img2spect2(self):
        global koef
        kernel = np.array([1.0,1.0,1.0]) # Определение ядра 

        koef = np.apply_along_axis(lambda x: np.convolve(x, kernel, mode='same'), 0, koef) # Применение операции свертки к массиву

        wavelength_range = np.arange(400, 700 , 5) # Определение диапазона длин волн 
        rgb_spectrum = colour.XYZ_to_sRGB(colour.wavelength_to_XYZ(wavelength_range)) # Преобразование длин волн в цветовое пространство sRGB
        self.RGB = colour.algebra.normalise_maximum(rgb_spectrum) # Нормализация полученного спектра
        self.vlen = len(wavelength_range)
        
        rgb = np.array([self.RGB*255]) # Создание массива rgb с преобразованием self.RGB в диапазон от 0 до 255.
        image = Image.fromarray(rgb.astype('uint8'), 'RGB')
        
        self.spc = np.zeros(self.vlen)
        for i in range(self.vlen):
             self.CycleDeconv(i)
             print(i) # Для уверенности, что работает, потом нужно стереть
        
        return (self.spc)


# Вычисление спектра 
def image2spect(img):
    coldc = ColourDeconvolution(img, 74)
    sp = coldc.img2spect2()
    return sp # Возвращение спектра



