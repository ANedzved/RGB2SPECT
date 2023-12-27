import cv2
import numpy as np

from PIL import Image

#подключаем QT
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtGui import QIcon, qRgb
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QStackedLayout

# пока не понял, что это. Надо разобраться
from myprocess import detectarearoot 
from maze import find_shortest_path
from maze import drawPath

# подключаем matplotlib для QT
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# подключение расчета спектра
from SPC_mdlg.spectrum import image2spect

###############################################################################
# Класс для скройлинга 
class ImScrollArea(QScrollArea):

    def __init__(self):
        QScrollArea.__init__(self)

    def wheelEvent(self, ev):
        if ev.modifiers() == Qt.ShiftModifier:
            do_zoom_x = False
        if ev.modifiers() == Qt.ControlModifier:
            if ev.type() == QtCore.QEvent.Wheel:
                #ev.ignore()
                do_zoom_x = False
    


###############################################################################
# Класс для поля в окошке в котором будет рисовать matplotlib
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=0, height=0, dpi=100):
        self.spcw=[]
        self.spcb=[]
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


###############################################################################
# основной класс для создания интерфейса программы
class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
      
        self.scaleFactor = 0.0
        self.x = 0
        self.y = 0
        self.ox = 0
        self.oy = 0
        self.mouseState = ""
        self.mouseAction = 1
        #0 - none
        #1 - интерфейсная функция для вычисления линейного уравнения
        ## параметры функции
        
        # координаты прямоугольного участка выделенного мышью
        self.Coords1x, self.Coords1y = 'NA', 'NA' # NA - Not Available(не доступно)
        self.Coords2x, self.Coords2y = 'NA', 'NA'

        self.printer = QPrinter()
        #  выстраиваем интерфейс на QT
        self.imageLabel = QLabel() # объект QLabel, который будет использоваться для отображения изображений
        self.imageLabel.setBackgroundRole(QPalette.Base) 
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark) 
        
        self.scrollArea.setWidget(self.imageLabel)
 
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=0, height=0, dpi=100)
        self.spcw=np.array(0)
        self.spcb=np.array(0)
        
        self.layout = QStackedLayout() # Создается объект QStackedLayout, который предоставляет макет для управления несколькими виджетами
        self.layout.addWidget(self.scrollArea) #Добавляется объект QScrollArea в макет self.layout
        self.layout.addWidget(self.sc) # Добавляется объект MplCanvas в макет self.layout

        self.layout.setCurrentIndex(0) # Устанавливается текущий индекс макета self.layout на 0, что означает отображение первого виджета (QScrollArea)
        
        self.widget = QWidget() # Создается объект QWidget, который будет использоваться в качестве главного виджета
        self.widget.setLayout(self.layout) # Устанавливается макет self.layout для объекта QWidget.
        self.setCentralWidget(self.widget)

        self.createActions() # Вызывается метод для создания действий приложения
        self.createMenus() # Вызывается метод для создания меню приложения
        self._createToolBars() # Вызывается метод для создания панели инструментов приложения
        self.image=np.zeros((500, 400, 3), np.uint8)
        
        self.setWindowTitle("Image spectrum viewer") # Устанавливается заголовок окна приложения
        self.resize(500, 400) # Устанавливается размер окна приложения
        self.statusBar().showMessage('Ready') # Отображается строка состояния приложения с сообщением "Ready"

        
    

    ###############################################################################
    # Создание панели инструментов (toolbar) в пользовательском окне приложения
    def _createToolBars(self):
        
        homeAction = QAction(QIcon('resurses/home.png'), 'root Area', self)
        homeAction.setShortcut('Ctrl+H')
        homeAction.triggered.connect(self.open) # При активации действия вызывается метод open

        selectbarAction = QAction(QIcon('resurses/select.png'), 'select Bar', self)
        selectbarAction.setShortcut('Ctrl+B')
        selectbarAction.triggered.connect(self.selectBar)

        selectAction = QAction(QIcon('resurses/pen.png'), 'select Region', self)
        selectAction.setShortcut('Ctrl+R')
        selectAction.triggered.connect(self.selectRegion)

        specrumAction = QAction(QIcon('resurses/analytics.png'), 'Spectrum calculation', self)
        specrumAction.setShortcut('Ctrl+S')
        specrumAction.triggered.connect(self.img2spectrum)

        self.toolbar = self.addToolBar('Exit') # Создается панель инструментов с названием 'Exit'
        self.toolbar.addAction(homeAction) # Добавляется на панель инструментов self.toolbar
        self.toolbar.addAction(selectbarAction)
        self.toolbar.addAction(selectAction)
        self.toolbar.addAction(specrumAction)

    # Преобразование из изображения openCV в QPixmap
    def cv2qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format
        
        return QPixmap.fromImage(p)
    
    # Отображение изображение cv_img в пользовательском интерфейсе    
    def display_cv(self, cv_img):
        self.image=cv_img.copy() #Копия cv_img сохраняется в переменной self.image. Это позволяет сохранить оригинальное изображение и работать с его копией
        self.imageLabel.setPixmap(self.cv2qt(self.image)) # Устанавливается пиксмап (QPixmap) для виджета

        self.printAct.setEnabled(True)
        self.fitToWindowAct.setEnabled(True)
        self.showImgAct.setEnabled(True)
        
        # Включаются кнопки для доступа в использовании
        self.img2blackspectrumAct.setEnabled(True)
        self.img2whitespectrumAct.setEnabled(True)
        self.img2spectrumAct.setEnabled(True)
        #self.img2brightness.setEnabled(True) #<-----------------------# Enable
        
        self.updateActions() # Обновление состояния действий в пользовательском интерфейсе в соответствии с текущим состоянием
        self.swith2image() # Переключение на режим отображения изображения
        
        # Подгоняем размер виджета под размер отображаемого изображения
        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()
        self.update() # Обновляет пользовательский интерфейс
    
    # Преобразование координат из координатной системы экрана в координатную систему изображения       
    def coordinate_scr2img(self,x,y):
        iX=iY=0 # Переменные будут содержать преобразованные координаты изображения
        if (self.scaleFactor!=0): #Проверка, что текущий масштаб изображения не равен 0
            scf=(1/self.scaleFactor) # Вычисление обратного значения масштаба и сохранение результата в переменной scf
                                     # Это позволяет получить масштабный коэффициент для преобразования координат
            dp=self.imageLabel.pos() # Получение позиции виджета 
            
            #Вычисление преобразованных координат iX и iY
            iX = (x- self.widget.frameGeometry().left()+
                  self.scrollArea.frameGeometry().left()-dp.x())*scf
            iY = (y- self.widget.frameGeometry().top()+
                  self.scrollArea.frameGeometry().top()-dp.y())*scf
        return(iX,iY)
   
    # Преобразование координат из координатной системы изображения в координатную систему экрана
    def coordinate_img2scr(self,x,y):
        dp=self.scrollArea.pos()
        iX = x*self.scaleFactor+self.widget.frameGeometry().left()-self.scrollArea.frameGeometry().left()+dp.x()
        iY = y*self.scaleFactor+self.widget.frameGeometry().top()-self.scrollArea.frameGeometry().top()+dp.y()
        return(iX,iY)

    # Открытие выбранного файла изображения и его отображение в пользовательском интерфейсе
    def open(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                QDir.currentPath()) # Открывается диалоговое окно выбора файла. Выбранный путь к файлу сохраняется в переменной fileName
        
        if fileName:
            #self.img=cv2.imread(fileName)            
            f = open(fileName, "rb") # Файл изображения открывается для чтения в двоичном режиме и сохраняется в переменной f
            chunk = f.read() # Чтение содержимого файла
            chunk_arr = np.frombuffer(chunk, dtype=np.uint8) # Преобразование содержимого файла в массив NumPy типа uint8
            self.img = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR) # Декодирование массива в изображение с помощью OpenCV
            self.Coords1x=self.Coords1y=0 # Обнуление координат
            height, width, channels = self.img.shape # Получение высоты (height), ширины (width) и числа каналов (channels) изображения
            self.Coords2x= width # Задание координаты Coords2x равной ширине изображения
            self.Coords2y= height # Задание координаты Coords2y равной высоте изображения
            self.scaleFactor=1.0
            self.display_cv(self.img ) # Отображение изображения в пользовательском интерфейсе


    # Печать изображения
    def print_(self):
        dialog = QPrintDialog(self.printer, self) # Создается диалоговое окно печати
        if dialog.exec_(): # Проверяется, что пользователь подтвердил диалоговое окно печати
            painter = QPainter(self.printer) # Создается объект QPainter для выполнения рисования на принтере
            rect = painter.viewport() # Получаем область вывода рисунка на принтере
            size = self.imageLabel.pixmap().size() # Получается размер изображения 
            size.scale(rect.size(), Qt.KeepAspectRatio) # Масштабирование размера изображения, чтобы сохранить соотношение сторон и поместить его в область вывода
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height()) # Устанавливается область вывода 
            painter.setWindow(self.imageLabel.pixmap().rect()) # Устанавливается окно window для рисования на принтере
            painter.drawPixmap(0, 0, self.imageLabel.pixmap()) # Выполняется рисование пиксмапа изображения 

    ## Масштабированием изображения
    # Увеличивает масштаб изображения
    def zoomIn(self):
        self.scaleImage(1.25)

    # Уменьшает масштаб
    def zoomOut(self):
        self.scaleImage(0.8)

    # Возвращает изображение к нормальному размеру
    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    # Подгоняет изображение к размеру окна
    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked() # Проверяет значение флажка
        self.scrollArea.setWidgetResizable(fitToWindow) # Настраиваем на возможность изменения размера содержимого
        if not fitToWindow: # Если флажок не установлен
            self.normalSize() # Возвращаем к нормальному размеру

        self.updateActions()

    # Диалоговое окно "О программе"
    def about(self):
        QMessageBox.about(self, "About Image spectrum viewer",
                "<p>The <b>Image spectrum viewer</b> is an application for "
                "calculating the spectral characteristics of an image. This application"
                " consists of a graphical interface and various methods for calculating "
                "the spectrum and brightness. The resulting results"
                " can be presented in the form of a histogram. It can "
                "also reveal the roots in the image.</p>"
                "<p>Images are easily opened and can be printed "
                "</p>"
                "<p>In addition the example shows how to use QPainter to "
                "print an image.</p>")

    # Действия, которые могут быть выполнены в пользовательском интерфейсе
    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open) # Устанавливается ярлык

        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P",
                enabled=False, triggered=self.print_)

        self.exitAct = QAction("&Exit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("&Zoom &In (25%)", self, shortcut="Ctrl++",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("&Zoom &Out (25%)", self, shortcut="Ctrl+-",
                enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+N",
                enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow) # Действие для подгонки изображения к размеру окна. Включено изначально
        
        self.showImgAct = QAction("&Switch to image (&1)", self, enabled=False,
                checkable=True, shortcut="1", triggered=self.swith2image) # Действие для переключения на отображение изображения

        self.showPlotAct = QAction("&Switch to plot (&2)", self, enabled=False,
               checkable=True, shortcut="2", triggered=self.swith2plot) # Действие для переключения на отображение графика

        self.aboutAct = QAction("&About", self, triggered=self.about) # Действие для отображения информации о программе

        self.aboutQtAct = QAction("&About &Qt", self,
                triggered=QApplication.instance().aboutQt) # Действие для отображения информации о фреймворке Qt
        
        self.img2spectrumAct = QAction("Specrum", self, enabled=False,
               checkable=True, triggered=self.img2spectrum) # Действие для конвертации изображения в спектр
        
        self.img2whitespectrumAct = QAction("White Specrum", self, enabled=False,
               checkable=True, triggered=self.img2whitespectrum) # Действие для конвертации изображения в белый спектр
        
        self.img2blackspectrumAct = QAction("Black Specrum", self, enabled=False,
               checkable=True, triggered=self.img2blackspectrum) # Действие для конвертации изображения в черный спектр
        
        self.img2brightnessAct = QAction("Luma", self, enabled=False,
               checkable=True, triggered=self.img2brightness) # Действие для конвертации изображения в яркость

    ## Переключения между отображением изображения и отображением графика
    def swith2image(self):
        self.layout.setCurrentIndex(0) # Переключает текущий индекс в макете на значение 0, которое соответствует отображению изображения
    
    def swith2plot(self):
        self.layout.setCurrentIndex(1) # Переключает текущий индекс в макете на значение 1, которое соответствует отображению графика
    
    ## Создание меню
    def createMenus(self):
        #Меню "File" для операций с файлами
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator() # Добавляется разделитель
        self.fileMenu.addAction(self.exitAct)

        #Меню "View" для операций с видом
        self.viewMenu = QMenu("&View", self)
        # Изменение масштаба
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator() # Добавляется разделитель
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addSeparator() # Добавляется разделитель
        self.viewMenu.addAction(self.showImgAct)
        self.viewMenu.addAction(self.showPlotAct)
        
        # Меню "Processing" для операций с обработкой данных
        self.procMenu = QMenu("&Processing", self)
        self.procMenu.addAction(self.img2spectrumAct)
        self.procMenu.addAction(self.img2whitespectrumAct)
        self.procMenu.addAction(self.img2blackspectrumAct)
        self.procMenu.addAction(self.img2brightnessAct) #ТУТ ПИСАЛА Я

        # Меню "Help" для справки
        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        # Добавление каждого меню в строку меню бара виджета
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.procMenu)
        self.menuBar().addMenu(self.helpMenu)

    # Обновляем доступность (enabled/disabled) некоторых действий
    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    # Масштабируем изображение
    def scaleImage(self, factor):
        self.scaleFactor *= factor # Коэффициент масштабирования умножается на текущий масштаб
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size()) # Изменяем размеры виджета

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor) # Корректировки положения полос прокрутки
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        # Доступность действий обновляеМ в зависимости от значения масштаба
        self.zoomInAct.setEnabled(self.scaleFactor < 3.0) 
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    # Корректируем положение полосы прокрутки
    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))

    # Обрабатываем событие нажатия кнопки мыши на виджете
    def mousePressEvent (self, eventQMouseEvent):
        self.originQPoint = self.scrollArea.mapFrom(self, eventQMouseEvent.pos()) # Преобразование координат положения курсора мыши
       
        x = int(eventQMouseEvent.x()) # Получаем целочисленные значения координат x и y из события нажатия кнопки мыши
        y = int(eventQMouseEvent.y())
        (self.x,self.y) = self.coordinate_scr2img(x,y) # Преобразование координат из системы координат виджета в систему координат изображения
        text1 = str(self.x)
        text2 = str(self.y)
        vstr = str("X: " + text1 + " " +"Y: " + text2 + "/" + "Act: " + self.mouseState) # Формируется строка, которая содержит текст с координатами X и Y и состоянием
        self.statusBar().showMessage(vstr) # Строка состояния (status bar) виджета обновляется с помощью метода showMessage, чтобы отобразить vstr
        self.Coords1x=int(self.x)
        self.Coords1y=int(self.y)
        
    # Обработка событий перемещения мыши
    def mouseMoveEvent (self, eventQMouseEvent):
        x = int(eventQMouseEvent.x()) # Получаем целочисленные значения координат x и y
        y = int(eventQMouseEvent.y())
        (self.x,self.y) = self.coordinate_scr2img(x,y) # Преобразование координат из системы координат виджета в систему координат изображения
        text1 = str(self.x)
        text2 = str(self.y)
        vstr = str("X: "+text1+" "+"Y: "+text2) # Формируется строка, которая содержит текст с координатами X и Y
        self.statusBar().showMessage(vstr) # Строка состояния (status bar) виджета обновляется с помощью метода showMessage, чтобы отобразить vstr
        self.Coords2x=int(self.x)
        self.Coords2y=int(self.y)
        if self.mouseAction == 1: #1 - функция для вычисления линейного уравнения
            if(self.mouseState=='contour'):
                print (self.mouseState=='contour')
                print (self.mouseState)
                p = find_shortest_path(self.img, (self.Coords1x, self.Coords1y), ( self.Coords2x, self.Coords2y)) # Вызов метода для нахождения кратчайший путь
                img2=self.img.copy()
                drawPath(img2,p) # Нанесение найденного пути p на скопированное изображение с помощью функции drawPath
                self.display_cv(img2) # Отображение измененного изображения
            if(self.mouseState=='bar'):
                img2=self.img.copy()
                cv2.rectangle(img2, (self.Coords1x, self.Coords1y), ( self.Coords2x, self.Coords2y),(0, 255, 255),0) # Наносится прямоугольник с координатами
                self.display_cv(img2)


    # Обработка отжима кнопки мыши
    def mouseReleaseEvent (self, eventQMouseEvent):
        if self.mouseAction == 1:
            print ((self.Coords1x,self.Coords1y))
            print ((self.Coords2x,self.Coords2y))
            print ((self.x,self.y))
            print ((self.ox,self.oy))
            print ("-------------------------------------------------")

    # Обработка двойного щелчка мыши
    def  mouseDoubleClickEvent (self, eventQMouseEvent):
        x = int(eventQMouseEvent.x()) # Получаем целочисленные значения координат x и y
        y = int(eventQMouseEvent.y())
        (self.x,self.y) = self.coordinate_scr2img(x,y) # Преобразование координат из системы координат виджета в систему координат изображения
        text1 = str(self.x)
        text2 = str(self.y)
        vstr=str("X: " + text1 + " " + "Y: " + text2)# Формируется строка, которая содержит текст с координатами X и Y
        self.statusBar().showMessage(vstr) # Строка состояния (status bar) виджета обновляется с помощью метода showMessage, чтобы отобразить vstr
    
    #Обработка вращения колесика мыши    
    def  wheelEvent (self, wheelEvent)-> None:
        # Проверка модификаторов события wheelEvent для определения, 
        # какие клавиши были нажаты вместе с вращением колесика мыши
        if wheelEvent.modifiers() == Qt.ShiftModifier: # Если зажата клавиша Shift
            do_zoom_x = False
        if wheelEvent.modifiers() == Qt.ControlModifier:# Если зажата клавиша Control (или Cmd на macOS)
            do_zoom_y = False
            #wheelEvent.accept()
            #wheelEvent.ignore()
            y = int(wheelEvent.angleDelta().y()) # Получение значения вращения колесика мыши по оси y
            if (y > 0): # При положительном значении увеличиваем масштаб
                self.zoomIn()
            if (y < 0): # При отрицательном значении уменьшаем масштаб
                self.zoomOut()
            text1 = str(self.scaleFactor)
            vstr = str("scaleFactor: " + text1 + " ")
            self.statusBar().showMessage(vstr) # Обновление строки состояния (status bar) виджета с помощью метода showMessage, чтобы отобразить текущий масштаб
        else:
            wheelEvent.accept() # В противном случае, событие колесика мыши принимается (accept) для обработки
            
    def  binArea(self):
        img=self.image
        img0=detectarearoot(img) # Поиск корня
        self.display_cv(img0) # Отображения изображения
    
    # Изменение состояния мыши    
    def  selectBar(self):
        if self.mouseState == 1:
            self.mouseState = 0
        else:
            self.mouseState = 1
        if self.mouseState == 'bar':
            self.mouseState = 0
        else:
            self.mouseState = 'bar'

    def  selectRegion(self):
        if self.mouseState == 'contour':
            self.mouseState = 0
        else:
            self.mouseState = 'contour'

    # Вычисление спектра
    def img2spectrum(self):
        self.sc.axes.cla() # Очищает текущий график
        imgtemp = self.img[self.Coords1y:self.Coords2y, self.Coords1x:self.Coords2x] #Сохраняем выбранный прямоугольник
        img00 = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2RGB) # Конвертирует цветовое пространство выбранной области из BGR в RGB
        impil = Image.fromarray(img00) # Создает объект Image из массива
        QApplication.setOverrideCursor(Qt.WaitCursor) # Устанавливает курсор ожидания
        spc = image2spect(impil) # Преобразовываем изображение в спектральные данные
        
        if self.spcb.ndim > 0 & self.spcw.ndim > 0: # Проверяет размерность атрибутов
            drange=(self.spcw-self.spcb) # Вычисляет разницу между белым и черным спектром
            drange[drange<=1] =1 # Если значения меньше или равны 1, устанавливает их равными 1
            spcn=(spc-self.spcb)/drange # Вычисляет нормализованные спектральные данные
        else:
            spcn=spc
        self.showPlotAct.setEnabled(True) # Включает действие представление графика
        QApplication.restoreOverrideCursor() # Восстанавливает исходный курсор
        ve=(np.arange(400, 700, 5)) # Включает действие
        self.sc.axes.bar(ve,spcn, color ='maroon',
        width = 4) # Создает столбчатую диаграмму на графике с использованием значений из ve и spcn
        self.sc.axes.plot(ve,spcn) # Строит линейный график на графике с использованием значений из ve и spcn
        self.swith2plot() # Переключает режим отображения на график
        self.sc.figure.canvas.draw() # Обновляет холст (canvas) графика. 
        self.sc.show() # Показывает график
        
        
    def img2whitespectrum(self):
        imgtemp=self.img[self.Coords1y:self.Coords2y, self.Coords1x:self.Coords2x]
        img0 = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2RGB)
        impil = Image.fromarray(img0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.spcw= spc = image2spect(impil) 
        
        self.showPlotAct.setEnabled(True)
        QApplication.restoreOverrideCursor()
        ve=(np.arange(380, 750, (750-380)/310))
        self.sc.axes.plot(ve,self.spcw)
        self.swith2plot()
        self.sc.figure.canvas.draw()
        self.sc.show()
        
    def img2blackspectrum(self):
        imgtemp=self.img[self.Coords1y:self.Coords2y, self.Coords1x:self.Coords2x]
        img0 = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2RGB)
        impil = Image.fromarray(img0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.spcb = spc = image2spect(impil) 
        
        self.showPlotAct.setEnabled(True)
        QApplication.restoreOverrideCursor()
        ve=(np.arange(380, 750, (750-380)/310))

        self.sc.axes.plot(ve,self.spcb)
        self.swith2plot()
        self.sc.figure.canvas.draw()
        self.sc.show()

    #Что-то на моем
    def img2brightness(self):
        imgtemp=self.img[self.Coords1y:self.Coords2y, self.Coords1x:self.Coords2x]
        img0 = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2RGB)
        impil = Image.fromarray(img0)
        red = impil[:, :, 0]
        grn = impil[:, :, 1]
        blu = impil[:, :, 2]
        COEF_R = 0.2126
        COEF_G = 0.7152
        COEF_B = 0.0722
    
        luma = red * COEF_R + grn * COEF_G + blu * COEF_B

        pb = luma - blu
        pr = luma - red
        
        self.showPlotAct.setEnabled(True)
        QApplication.restoreOverrideCursor()
        ve=(np.arange(380, 750, (750-380)/310))

        self.sc.axes.plot(ve,pb)
        self.swith2plot()
        self.sc.figure.canvas.draw()
        self.sc.show()


################################################################################################################


import sys
# Отображаем изображение в диалоговом окне
def dlgshow(img):
    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.display_cv(img) # Отображаем изображение 

    imageViewer.show() # Показываем окно
    imageViewer.activateWindow() # Активируем окно
       
    sys.exit(app.exec_()) # Запускаеv цикл обработки событий приложения QApplication и выходиv из программы при закрытии окна


# Определяется точка входа в программу
if __name__ == '__main__':
    import sys
    from PyQt5 import QtGui, QtCore, QtWidgets

    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('logo.png'))
    imageViewer = ImageViewer()
    
    imageViewer.show()
    imageViewer.activateWindow()
   
    sys.exit(app.exec_())
    