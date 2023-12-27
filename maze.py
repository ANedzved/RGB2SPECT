import cv2
import numpy as np

#Helper functions and classes
class Vertex:
    def __init__(self,x_coord,y_coord):
        self.x = x_coord
        self.y = y_coord
        self.d = float('inf') # Расстояние от источника
        self.parent_x = None
        self.parent_y = None
        self.processed = False
        self.index_in_queue = None

# Возвращает соседа непосредственно сверху, снизу, справа и слева
def get_neighbors(mat, r, c):
    shape = mat.shape
    neighbors = []
    # Проверка, что соседи находятся в пределах границ изображения
    if r > 0 and not mat[r - 1][c].processed:
         neighbors.append(mat[r - 1][c])
    if r < shape[0] - 1 and not mat[r + 1][c].processed:
            neighbors.append(mat[r + 1][c])
    if c > 0 and not mat[r][c - 1].processed:
        neighbors.append(mat[r][c - 1])
    if c < shape[1] - 1 and not mat[r][c + 1].processed:
            neighbors.append(mat[r][c + 1])
    return neighbors

# "Всплытие" в очереди с приоритетом
def bubble_up(queue, index):
    if index <= 0: # Если index меньше или равен 0
        return queue # Элемент уже находится в корне очереди (на самом верху), и функция возвращает исходную очередь без изменений
    p_index=(index-1)//2 # Вычисляется индекс родительского элемента
    if queue[index].d < queue[p_index].d:
            # Обмен местами между текущим элементом и родительским элементом
            queue[index], queue[p_index] = queue[p_index], queue[index]
            queue[index].index_in_queue = index
            queue[p_index].index_in_queue = p_index
            queue = bubble_up(queue, p_index)
    return queue

# "Спуск" в очереди с приоритетом    
def bubble_down(queue, index):
    length = len(queue)
    
    # Вычисляются индексы левого и правого дочерних элементов
    lc_index = 2*index + 1
    rc_index = lc_index + 1
    
    if lc_index >= length:
        return queue # Текущий элемент находится в конце очереди и не имеет дочерних элементов
    if lc_index < length and rc_index >= length:
        # У текущего элемента есть только левый дочерний элемент
        if queue[index].d > queue[lc_index].d:
            # Обмен местами между ними в очереди с приоритетом
            queue[index], queue[lc_index] = queue[lc_index], queue[index]
            # Обновляются индексы элементов в очереди после обмена
            queue[index].index_in_queue = index
            queue[lc_index].index_in_queue = lc_index 
            queue = bubble_down(queue, lc_index) # Для левого дочернего элемента, чтобы проверить и, при необходимости, переместить его ниже
    else:
        # У текущего элемента есть и левый, и правый дочерний элементы, выбирается наименьший из них по значению d
        small = lc_index
        if queue[lc_index].d > queue[rc_index].d:
            small = rc_index
        if queue[small].d < queue[index].d:
            # Обмен местами между ними в очереди с приоритетом
            queue[index],queue[small] = queue[small],queue[index]
            # Обновляются индексы элементов в очереди после обмена
            queue[index].index_in_queue = index 
            queue[small].index_in_queue = small
            queue = bubble_down(queue, small) # Для выбранного дочернего элемента, чтобы проверить и, при необходимости, переместить его ниже
    return queue

# Вычисляет расстояние между пикселями, основываясь на разнице их цветовых компонент
def get_distance(img,u,v):
    # Вычисление расстояния между пикселями u и v на основе их цветовых компонент (красный, зеленый и синий каналы)
    return 0.1 + (float(img[v][0]) - float(img[u][0]))**2 + (float(img[v][1]) - float(img[u][1]))**2 + (float(img[v][2]) - float(img[u][2]))**2

# Рисуем путь (линию) на изображении
def drawPath(img,path, thickness=2):
    x0, y0 = path[0] # Извлекаются начальные координаты пути
    for vertex in path[1:]:
        x1, y1 = vertex # Координаты текущей точки пути извлекаются из переменной
        cv2.line(img,(x0, y0),(x1, y1),(255, 0, 0), thickness) # Рисуем линию на изображении
        x0, y0 = vertex

# Находим кратчайший путь между двумя точками на изображении
def find_shortest_path(img, src, dst):
    pq = [] # Создается пустая очередь с приоритетом
    # Извлекаются координаты начальной точки пути из src и конечной точки пути из dst
    source_x = src[0] 
    source_y = src[1]
    dest_x = dst[0]
    dest_y = dst[1]
    imagerows, imagecols = img.shape[0], img.shape[1] # Получаются размеры изображения
    matrix = np.full((imagerows, imagecols), None) #Создается двумерный массив для хранения вершин графа
    for r in range(imagerows):
        for c in range(imagecols):
            matrix[r][c] = Vertex(c, r) # Для каждого элемента создается объект с координатами (c, r)
            matrix[r][c].index_in_queue = len(pq) 
            pq.append(matrix[r][c]) # Устанавливается индекс каждой вершины в очереди pq
    # Устанавливается значение расстояния до начальной вершины равным 0
    matrix[source_y][source_x].d = 0
    pq = bubble_up(pq, matrix[source_y][source_x].index_in_queue)
    while len(pq) > 0:
        u = pq[0] # Извлекается вершина с наименьшим расстоянием u из начала очереди
        u.processed = True # Устанавливается флаг processed для вершины u равным True, чтобы отметить ее как обработанную
        pq[0] = pq[-1] # Последний элемент очереди pq перемещается на место удаленной вершины u
        pq[0].index_in_queue = 0 # Обновляется индекс в очереди для этого элемента
        pq.pop() # Удаляется последний элемент очереди pq
        pq = bubble_down(pq, 0) # Для восстановления свойств min-heap в очереди
        neighbors = get_neighbors(matrix, u.y, u.x) # Получаем соседей вершины u
        for v in neighbors:
            # Для каждого соседа v из списка соседей вычисляется расстояние
            dist = get_distance(img,(u.y, u.x),(v.y, v.x)) 
            if u.d + dist < v.d: 
                # Обновляются значения для вершины v
                v.d = u.d + dist
                v.parent_x = u.x
                v.parent_y = u.y
                idx = v.index_in_queue # Обновляется индекс v.index_in_queue в очереди
                pq = bubble_down(pq, idx) # Чтобы восстановить свойства min-heap
                pq = bubble_up(pq, idx) # Чтобы упорядочить элементы с учетом измененного значения v.d
       
    # Создается пустой список path, который будет содержать координаты вершин кратчайшего пути                   
    path = []
    iter_v = matrix[dest_y][dest_x] # Извлекается последняя вершина
    path.append((dest_x, dest_y)) # Добавляются в список
    while(iter_v.y != source_y or iter_v.x != source_x):
        path.append((iter_v.x, iter_v.y)) # Координаты текущей вершины iter_v добавляются в список
        iter_v = matrix[iter_v.parent_y][iter_v.parent_x] # Обновляется iter_v, присваивая ей родительскую вершину

    path.append((source_x, source_y)) # Координаты начальной вершины добавляются в список
    return path