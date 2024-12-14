import math
import random
from components.vector import Vector2D


class Body():
    def __init__(self, x, y, mass = 1, bounce = 0.5, name = None, is_static = False):
        self.center = Vector2D(x, y)
        self.angle = 0    
        self.name = name
        self.shape_type = None
        self.velocity = Vector2D(0, 0)
        self.angular_velocity = 0#
        
        
        self.inertia = None#
        self.mass = mass if not is_static else float("inf") #
        self.bounce = bounce #
        self.is_static = is_static#

        self.is_fragment = False 

class Rectangle(Body):
    def __init__(self, x, y, width, height, mass = 1, bounce = 0.5, name = None, is_static = False):
        super().__init__(x, y, mass, bounce, name, is_static)
        self.width = width
        self.height = height
        self.shape_type = "Polygon"
        half_width = self.width / 2
        half_height = self.height / 2

        self.local_vertices = [
            Vector2D(-half_width, -half_height),
            Vector2D(half_width, -half_height),
            Vector2D(half_width, half_height),
            Vector2D(-half_width, half_height)
        ]
        #
        self.inertia = (1 / 12) * mass * (width * width + height * height) if not is_static else float("inf")
        
    
    def get_axes(self):
        self.x_axis = Vector2D(math.cos(self.angle), math.sin(self.angle))
        self.y_axis = Vector2D(-math.sin(self.angle), math.cos(self.angle)) 
        
        return [self.x_axis, self.y_axis] 

    def get_vertices(self):
        return [vertex.rotate(self.angle).add(self.center) for vertex in self.local_vertices]

    def rotate(self, angle, in_radians=True):
        if not in_radians:
            angle = math.radians(angle)
        self.angle += angle



class Polygon(Body):
    def __init__(self, x, y, vertices: list[Vector2D, list, tuple], mass=1, bounce=0.5, name=None, is_static=False):
        super().__init__(x, y, mass, bounce, name, is_static)
        centroid = (
            sum(vertex[0] for vertex in vertices) / len(vertices),
            sum(vertex[1] for vertex in vertices) / len(vertices),
        )

        self.local_vertices = [Vector2D(vertex[0] - centroid[0], vertex[1] - centroid[1]) for vertex in vertices]
      
        self.shape_type = "Polygon"
        self.inertia = self.calculate_inertia() if not is_static else float("inf")#
    
    def get_center(self):
    # get_vertices로 변환된 꼭짓점을 가져옴
        vertices = self.get_vertices()
        # x, y 좌표 각각의 평균 계산
        center_x = sum(vertex.x for vertex in vertices) / len(vertices)
        center_y = sum(vertex.y for vertex in vertices) / len(vertices)
        return Vector2D(center_x, center_y)

    def get_vertices(self):
        return [vertex.rotate(self.angle).add(self.center) for vertex in self.local_vertices]
    
    ####
    def calculate_inertia(self):
    # Initialize variables
        area = 0
        center = Vector2D(0, 0)
        mmoi = 0

        # Set the last vertex as the initial previous vertex
        prev = len(self.local_vertices) - 1

        # Iterate through each edge of the polygon
        for index in range(len(self.local_vertices)):
            a = self.local_vertices[prev]  # Previous vertex
            b = self.local_vertices[index]  # Current vertex

            # Calculate the area of the triangle formed by the edge
            area_step = a.cross(b)/2  

            # Calculate the centroid of the triangle
            center_step = (a+b)/3  

            # Calculate the moment of inertia for the triangle
            mmoi_step = area_step* (a.dot(a)+b.dot(b)+a.dot(b))/6

            # Update the centroid considering the new triangle
            center = (center*area+center_step*area_step)/(area_step+area)

            # Accumulate the area and moment of inertia
            area += area_step 
            mmoi += mmoi_step  

            # Move to the next edge
            prev = index 

        # Calculate the density of the polygon
        density = self.mass/area  

        # Adjust the moment of inertia with the density
        mmoi *= density 

        # Apply the parallel axis theorem to adjust for the centroid
        mmoi -= self.mass*center.dot(center) 

        # Return the final moment of inertia
        return mmoi


    def rotate(self, angle, in_radians=True):
        if not in_radians:
            angle = math.radians(angle)
        self.angle += angle

    
    def calculate_area(self):
        # 다각형의 면적을 구하는 함수 (Shoelace Theorem)
        area = 0
        n = len(self.local_vertices)

        for i in range(n):
            j = (i + 1) % n  # 다음 점, 마지막 점은 첫 번째 점으로 연결됨
            area += self.local_vertices[i].x * self.local_vertices[j].y
            area -= self.local_vertices[i].y * self.local_vertices[j].x

        return abs(area) / 2

class Circle(Body):
    def __init__(self, x, y, radius, mass = 5, bounce = 0.5, name = None, is_static = False):
        super().__init__(x, y, mass, bounce, name, is_static)
        self.radius = radius
        self.shape_type = "Circle"
        self.inertia = (1 / 2) * mass * radius * radius if not is_static else float("inf")
        self.velocity = Vector2D(0,0)
        self.angular_velocity = 1

    def rotate(self, angle, in_radians=True):
        if not in_radians:
            angle = math.radians(angle)
        self.angle += angle


class Fragment(Body):
    def __init__(self, x, y, radius, num_circles, spacing=2, mass=0.5, bounce=0.3, name="Fragment", is_static=False):
        super().__init__(x, y, mass, bounce, name, is_static)
        self.is_fragment = True  # Fluid 객체는 True로 설정
        self.circles = []
        self.center = Vector2D(x, y)
        
        # 무작위 초기 위치 배치
        for _ in range(num_circles):
            # 중심 주변의 무작위 위치 생성
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(radius * spacing * 0.5, radius * spacing * 1.5)
            circle_x = x + math.cos(angle) * distance
            circle_y = y + math.sin(angle) * distance
            circle = Circle(circle_x, circle_y, radius, mass, bounce)
            # 각 원의 속도와 각속도를 0으로 설정
            circle.velocity = Vector2D(0, 0)
            circle.angular_velocity = 0
            self.circles.append(circle)


    def update_center(self):
        #fragment의 중심 위치를 계산함
        avg_x = sum(circle.center.x for circle in self.circles) / len(self.circles)
        avg_y = sum(circle.center.y for circle in self.circles) / len(self.circles)
        self.center = Vector2D(avg_x, avg_y)

    def restore_to_polygon(self):
        # 원들의 중심과 주변 점을 사용하여 다각형을 복원
        points = []
        
        # 각 원을 대표하는 외부 점을 추출
        for circle in self.circles:
            points.append((circle.center.x, circle.center.y))
        
        # Convex Hull을 사용하여 바깥 점들만 선택하여 다각형을 만듦
        hull_points = convex_hull(points)
        
        # 복원된 점들을 사용하여 다각형을 반환
        return Polygon(x=self.center.x, y=self.center.y, vertices=hull_points, mass=50, is_static=False, name="Restored Polygon")

class Particle(Body):
    def __init__(self, x, y, velocity, mass=1, bounce=0.5, name=None, is_static=False):
        super().__init__(x, y, mass, bounce, name, is_static)
        self.velocity = velocity

def convex_hull(points):
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    # 점들을 정렬
    points = sorted(points)
    
    # 다각형의 바깥 점들을 point에 저장장
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    # 마지막 점은 중복되므로 제외하고 합침
    return lower[:-1] + upper[:-1]

