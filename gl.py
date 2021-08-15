import struct
import queue
from obj import Obj
import aritmetic as ar
from aritmetic import V3, Square, Triangle


def char(c):
    # ocupa 1 byte
    return struct.pack('=c', c.encode('ascii'))


def word(w):
    # short, ocupa 2 bytes
    return struct.pack('=h', w)


def dword(dw):
    # long, ocupa 4 bytes
    return struct.pack('=l', dw)


def color(r, g, b):
    return bytes([b, g, r])


BLACK = color(0, 0, 0)


class Renderer(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.current_color = BLACK
        self.clear_color = BLACK
        self.clear()

        # Para los puertos
        self.port_width = width
        self.port_height = height
        self.x = 0
        self.y = 0

        self.xm = round(width/2)
        self.ym = round(height/2)

        # Para modelos
        self.model_points = []
        self.model_squares = []
        self.model_triangles = []

        # Modelos en 3d
        self.light = V3(0, 0, -1)

    def clear(self):
        self.framebuffer = [
            [self.clear_color for _ in range(self.width)]
            for _ in range(self.height)
        ]

        self.zbuffer = [
            [-99999 for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def write(self, filename):
        f = open(filename, 'bw')
        # file header ' siempre es BM y ocupa 14 bytes
        f.write(char('B'))
        f.write(char('M'))
        # Se multiplica por tres por ser rgb
        f.write(dword(14 + 40 + 3*(self.width*self.height)))
        f.write(dword(0))
        f.write(dword(14+40))  # En donde

        # info header '
        f.write(dword(40))  # Tamaño del info header
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))    # pela pero se pone
        f.write(word(24))   # Siempre es 24
        f.write(dword(0))   # pela
        f.write(dword(3*(self.width*self.height)))

        for i in range(4):        # Cosas que pelan
            f.write(dword(0))

        # bitmap
        for y in range(self.height):
            for x in range(self.width):
                # Ahora solo se verifica que este dentro del view port
                if (self.x <= x) and (x <= self.port_width) and (self.y <= y) and (y <= self.port_height):
                    f.write(self.framebuffer[y][x])
                else:
                    f.write(BLACK)
        f.close()

    def do_point(self, x, y, color=None):
        self.framebuffer[y][x] = color or self.current_color

    def port_point(self, x, y):
        xp = round(self.xm + (x * self.xm))
        yp = round(self.ym + (y * self.ym))

        if (self.port_width <= xp):
            xp = self.port_width - 1
        elif (xp < self.x):
            xp = self.x
        if (self.port_height <= yp):
            yp = self.port_height - 1
        elif (yp < self.y):
            yp = self.y
        self.framebuffer[yp][xp] = self.current_color

    def load(self, filename, x, y):
        model = Obj(filename)

        for face in model.faces:
            size = len(face)
            for j in range(size):
                f0 = face[j][0] - 1
                f1 = face[(j+1) % size][0] - 1

                v0 = model.vertices[f0]
                v1 = model.vertices[f1]

                x0, y0 = v0[0] + x, v0[1] + y
                x1, y1 = v1[0] + x, v1[1] + y
                self.model_points.append((x0, y0, x1, y1))

    def load3d(self, filename, traslation=(0, 0, 0), scale=(1, 1, 1)):
        model = Obj(filename)

        for face in model.faces:
            size = len(face)

            vertices = []
            for i in range(size):  # Se obtienen los vertices
                fi = face[i][0] - 1
                point = model.vertices[fi]

                # Ahora se convirte normalizados a screen
                xf = (point[0]*scale[0] + traslation[0])
                yf = (point[1]*scale[1] + traslation[1])
                zf = point[2]*scale[2] + traslation[2]

                xp = round(self.xm + (xf * self.xm))
                yp = round(self.ym + (yf * self.ym))

                if (self.port_width <= xp):
                    xp = self.port_width - 1
                elif (xp < self.x):
                    xp = self.x
                if (self.port_height <= yp):
                    yp = self.port_height - 1
                elif (yp < self.y):
                    yp = self.y

                # Ahora se convierte en V3 y se mete
                P = V3(xp, yp, zf)
                vertices.append(P)
            if size == 4:
                self.model_squares.append(Square(*vertices))
            elif size == 3:
                self.model_triangles.append(Triangle(*vertices))


def glInit():  # 5 pts
    pass


def glCreateWindow(width, height):  # 5 pts
    global framebuffer
    framebuffer = Renderer(width, height)


def glViewPort(x, y, width, height):  # 10 pts
    # Verificar que sean validos
    tempw = x + width
    temph = y + height
    ftempw = framebuffer.width
    ftemph = framebuffer.height
    if (tempw <= ftempw) and (temph <= ftemph):
        # Asignando valores
        framebuffer.x = x
        framebuffer.y = y
        framebuffer.port_width = width + x
        framebuffer.port_height = height + y

        # Calculando la mitad
        framebuffer.xm = tempw - round((tempw - x)/2)
        framebuffer.ym = ftemph - round((ftemph - y)/2)


def glClear():  # 20 pts
    framebuffer.clear()


def glClearColor(r, g, b):  # 10 pts
    r = round(r*255)
    g = round(g*255)
    b = round(b*255)
    framebuffer.clear_color = color(r, g, b)


def glVertex(x, y):  # 30 pts
    framebuffer.port_point(x, y)


def glColor(r, g, b):  # 15 pts
    r = round(r*255)
    g = round(g*255)
    b = round(b*255)
    framebuffer.current_color = color(r, g, b)


def glFinish(name):  # 5 pts
    framebuffer.write(str(name) + '.bmp')


def glLine(x0, y0, x1, y1):
    # obteniendo la altura del port y el largo
    width = framebuffer.port_width - framebuffer.x
    heigth = framebuffer.port_height - framebuffer.y

    # Se realiza la multiplicacion y se vuelven enteros
    x0, x1 = round(x0 * width), round(x1 * width)
    y0, y1 = round(y0 * heigth), round(y1 * heigth)

    dy = y1 - y0
    dx = x1 - x0

    desc = (dy*dx) < 0

    dy = abs(dy)
    dx = abs(dx)

    steep = dy > dx

    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

    if desc and (y0 < y1):
        y0, y1 = y1, y0
    elif (not desc) and (y1 < y0):
        y0, y1 = y1, y0

    if (x1 < x0):
        x1, x0 = x0, x1

    offset = 0
    threshold = dx
    y = y0

    # y = mx + b
    points = []
    for x in range(x0, x1):
        xtemp = x / width
        ytemp = y / heigth

        if steep:
            points.append((ytemp, xtemp))
        else:
            points.append((xtemp, ytemp))

        offset += (dy/dx) * 2 * dx
        if offset >= threshold:
            y += 1 if y0 < y1 else -1
            threshold += 1 * 2 * dx

    for point in points:
        glVertex(*point)


def line(x0, y0, x1, y1):
    dy = y1 - y0
    dx = x1 - x0

    desc = (dy*dx) < 0

    dy = abs(dy)
    dx = abs(dx)

    steep = dy > dx

    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

    if desc and (y0 < y1):
        y0, y1 = y1, y0
    elif (not desc) and (y1 < y0):
        y0, y1 = y1, y0

    if (x1 < x0):
        x1, x0 = x0, x1

    offset = 0
    threshold = dx
    y = y0

    # y = mx + b
    points = []
    for x in range(x0, x1+1):
        if steep:
            points.append((y, x))
        else:
            points.append((x, y))

        offset += (dy/dx) * 2 * dx
        if offset >= threshold:
            y += 1 if y0 < y1 else -1
            threshold += 1 * 2 * dx

    for point in points:
        framebuffer.do_point(*point)


def glFill(x, y):
    fb = framebuffer
    buffer = fb.framebuffer
    color = fb.current_color
    width, heigth = fb.width, fb.height
    cola = queue.Queue()
    cola.put((x, y))

    # Pintando
    while not cola.empty():
        x, y = cola.get()
        if y == heigth or x == width:
            continue
        elif (buffer[x][y] == color):
            continue
        else:
            buffer[x][y] = color
            cola.put((x, y-1))
            cola.put((x+1, y))
            cola.put((x, y+1))
            cola.put((x-1, y))


def draw(points):
    size = len(points)
    for i in range(size):
        j = (i + 1) % size
        line(*points[i], *points[j])


def glDrawModel(filename, x, y):
    framebuffer.load(filename, x, y)
    points = framebuffer.model_points
    for point in points:
        glLine(*point)


def paintTriangle(A, B, C):
    xmin, xmax, ymin, ymax = ar.getMinBox(A, B, C)

    # Se recorre la caja
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            # Miramos si esta adentro
            P = V3(x, y, 0)
            # Con coordenadas barycentircas
            w, v, u = ar.barycentric(A, B, C, P)
            if (w < 0 or v < 0 or u < 0):
                continue

            # Se obtiene la normal

            normal = ar.getNormalDirection(A, B, C)

            # # Luego la intensidad con la que se pinta
            intensity = ar.pointProduct(normal, framebuffer.light)

            base = round(200 * intensity)

            if (base < 0):
                continue
            elif (base > 255):
                base = 255

            paint_color = color(base, base, base)

            z = A.z * w + B.z * v + C.z * u

            # Ahora miramos la posicion en z
            if z > framebuffer.zbuffer[x][y]:
                framebuffer.do_point(x, y, paint_color)
                framebuffer.zbuffer[x][y] = z


def paintSquare(A, B, C, D):
    paintTriangle(A, B, C)
    paintTriangle(A, C, D)


def glPaintModel(filename, traslation=(0, 0, 0), scale=(1, 1, 1)):
    framebuffer.load3d(filename, traslation, scale)
    squares = framebuffer.model_squares
    triangles = framebuffer.model_triangles

    # Se pintan los cuadrados
    for square in squares:
        A, B, C, D = square.getVertices()
        paintSquare(A, B, C, D)
    # Se pintan los triangulos
    for triangle in triangles:
        A, B, C = triangle.getVertices()
        paintTriangle(A, B, C)


glCreateWindow(600, 600)
# glPaintModel('./face.obj', (0, -0.6, 0), (0.05, 0.05, 100))
glPaintModel('./girl.obj', (0, -0.9, 0), (1, 1, 1000))
glFinish('out')
