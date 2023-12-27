import numpy as np

## Преобразованием цветовых компонентов и созданием вектора XYZ из координат X и Y

def g(x, alpha, mu, sigma1, sigma2):
    sigma = (x < mu)*sigma1 + (x >= mu)*sigma2
    return alpha*np.exp((x - mu)**2 / (-2*(sigma**2)))

# Вычисляет значение компоненты X путем суммирования трех компонент
def component_x(x): return g(x, 1.056, 5998, 379, 310) + \
    g(x, 0.362, 4420, 160, 267) + g(x, -0.065, 5011, 204, 262)

# Вычисляет значение компоненты Y путем суммирования двух компонент
def component_y(x): return g(x, 0.821, 5688, 469, 405) + \
    g(x, 0.286, 5309, 163, 311)

# Вычисляет значение компоненты Z путем суммирования двух компонент
def component_z(x): return g(x, 1.217, 4370, 118, 360) + \
    g(x, 0.681, 4590, 260, 138)

# Принимает значения компонент X и Y и возвращает вектор XYZ, где Z вычисляется как 1 - x - y
def xyz_from_xy(x, y):
    return np.array((x, y, 1-x-y))

# Словарные переменные, содержащие информацию о различных источниках света и цветовых пространствах
ILUMINANT = {
    'D65': xyz_from_xy(0.3127, 0.3291), # Стандартная иллюминанта D65
    'E':  xyz_from_xy(1/3, 1/3), # Равномерное распределение света
}

# Информация о различных цветовых пространствах
COLOR_SPACE = {
    # Каждый кортеж содержит следующие компоненты:
    'sRGB': (xyz_from_xy(0.64, 0.33), # Вектор XYZ для красного (R)
             xyz_from_xy(0.30, 0.60), # Вектор XYZ для зеленого (G)
             xyz_from_xy(0.15, 0.06), # Вектор XYZ для синего (B)
             ILUMINANT['D65']), # Вектор XYZ для иллюминанты

    'AdobeRGB': (xyz_from_xy(0.64, 0.33),
                 xyz_from_xy(0.21, 0.71),
                 xyz_from_xy(0.15, 0.06),
                 ILUMINANT['D65']),

    'AppleRGB': (xyz_from_xy(0.625, 0.34),
                 xyz_from_xy(0.28, 0.595),
                 xyz_from_xy(0.155, 0.07),
                 ILUMINANT['D65']),

    'UHDTV': (xyz_from_xy(0.708, 0.292),
              xyz_from_xy(0.170, 0.797),
              xyz_from_xy(0.131, 0.046),
              ILUMINANT['D65']),

    'CIERGB': (xyz_from_xy(0.7347, 0.2653),
               xyz_from_xy(0.2738, 0.7174),
               xyz_from_xy(0.1666, 0.0089),
               ILUMINANT['E']),
}


class ColourSystem:
    # Инициализируем объект цветовой системы с заданными параметрами
    def __init__(self, start=380, end=750, num=100, cs='sRGB'): #start и end: Начальная и конечная длины волны спектра в нанометрах, 
        #num: Количество точек в спектре, cs: Название цветового пространства из словаря COLOR_SPACE

        # Chromaticities
        bands = np.linspace(start=start, stop=end, num=num)*10 # Создается массив с равномерно распределенными значениями длины волны в заданном диапазоне

        # Вычисляются значения компонент X, Y и Z для каждой длины волны
        self.cmf = np.array([component_x(bands),
                             component_y(bands),
                             component_z(bands)])

        self.red, self.green, self.blue, self.white = COLOR_SPACE[cs] # Устанавливаются значения

        #Создается матрица преобразования от RGB к XYZ, а также ее обратная матрица 
        self.M = np.vstack((self.red, self.green, self.blue)).T
        self.MI = np.linalg.inv(self.M)

        # White scaling array
        self.wscale = self.MI.dot(self.white)

        # Создается матрица преобразования от XYZ к RGB
        self.A = self.MI / self.wscale[:, np.newaxis]

    # Возвращает матрицу преобразования XYZ в RGB
    def get_transform_matrix(self):

        XYZ = self.cmf
        RGB = XYZ.T @ self.A.T # Умножения матрицы цветовых спектров на обратную матрицу преобразования RGB в XYZ
        RGB = RGB / np.sum(RGB, axis=0, keepdims=True) # Нормализация матрицы RGB 
        return RGB
    
    # Преобразуем заданный спектр в значения RGB
    def spec_to_rgb(self, spec):
        M = self.get_transform_matrix()
        rgb = spec @ M # Умножает спектр на эту матрицу
        return rgb

    