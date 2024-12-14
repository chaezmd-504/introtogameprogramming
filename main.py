import pygame
import sys
from components.vector import Vector2D
from practice_code.collision import collide
from practice_code.body import Body, Circle, Fragment, Rectangle, Polygon
from components.scene import Scene
import random
import math

# 기본 설정
WIDTH, HEIGHT = 800, 600
PLAYER_SPEED_X = PLAYER_SPEED_Y = 2
FPS = 360
GRAVITY = 9.8
COLORS = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "black": (0, 0, 0),
    "orange": (255, 128, 0),
    "cyan": (0, 255, 255),
}

# 파티클 리스트
particles = []

# 다각형의 속도를 저장할 변수
polygon_velocity = Vector2D(0, 0)

def create_particle_effect(pos, num_particles, area):
    #파티클 분해 효과 (넓이에 비례)
    base_life = 50  # 기본 생명력
    life_scale = 0.1  # 넓이에 따른 생명력 (얼마나 오래 파티클이 화면에 살아있을지지)

    for _ in range(num_particles):
        # 무작위 각도와 속력 생성
        angle = random.uniform(0, 2 * math.pi)  # 0 ~ 360도 
        speed = random.uniform(1, 5)  # 속력 범위 조정 가능

        # 속도 계산
        vel_x = math.cos(angle) * speed
        vel_y = math.sin(angle) * speed

        # 생명력 또한 다각형 넓이에 비례례
        life = base_life + int(area * life_scale)

        particles.append({
            "pos": [pos[0], pos[1]],  # 시작 위치
            "vel": [vel_x, vel_y],  # 속도
            "radius": random.randint(2, 5),  # 크기
            "life": life  
        })

# 파티클 업데이트 함수
def update_particles():
    for particle in particles[:]:
        particle["pos"][0] += particle["vel"][0] #위치 업업데이트
        particle["pos"][1] += particle["vel"][1]

        particle["life"] -= 1  # 생명력 감소
        if particle["life"] <= 0:  # 제거
            particles.remove(particle)

# 파티클 그리기 함수
def draw_particles(screen):
    for particle in particles:
        pygame.draw.circle(screen, (0,0,0), (int(particle["pos"][0]), int(particle["pos"][1])), particle["radius"])


# 초기화
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Physics Engine")
clock = pygame.time.Clock()

# 장면(Scene) 생성
Scene = Scene([], GRAVITY)

# 테두리 생성
border_thickness = 10
Scene.add(Rectangle(x=WIDTH / 2, y=HEIGHT, width=WIDTH, height=border_thickness, is_static=True, name="Top Border"))
Scene.add(Rectangle(x=WIDTH / 2, y=0, width=WIDTH, height=border_thickness, is_static=True, name="Bottom Border"))
Scene.add(Rectangle(x=0, y=HEIGHT / 2, width=border_thickness, height=HEIGHT, is_static=True, name="Left Border"))
Scene.add(Rectangle(x=WIDTH, y=HEIGHT / 2, width=border_thickness, height=HEIGHT, is_static=True, name="Right Border"))

# 점 리스트 (마우스 입력으로 다각형 정의)
mouse_points = []
new_polygon = None  # 새로 생성된 다각형
fragment = None

# 플레이어 이동
move_left = False
move_right = False
move_up = False
move_down = False
dt = 1 / FPS


# 게임 루프
while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 마우스 클릭으로 점 추가
            mouse_points.append((event.pos[0], HEIGHT - event.pos[1]))  # 좌표 변환
            print(f"점 추가: {mouse_points[-1]}")  # 디버깅 출력
        elif event.type == pygame.KEYDOWN:
            # 다각형 생성
            if event.key == pygame.K_RETURN and len(mouse_points) > 2:                    
                avg_x = sum(point[0] for point in mouse_points) / len(mouse_points)
                avg_y = sum(point[1] for point in mouse_points) / len(mouse_points)

                new_polygon = Polygon(
                    x=avg_x,
                    y=avg_y,
                    vertices=mouse_points,
                    mass=50,
                    is_static=False,  # 움직이는 다각형
                    name="Player Polygon (Movable)"
                )
                print("움직이는 다각형 생성")
                Scene.add(new_polygon)
                polygon_created = True
                mouse_points = []  # 점 초기화

                fragment = None

            elif event.key == pygame.K_LSHIFT and len(mouse_points) > 2:       
                # 정적인 다각형 생성 (쉬프트 키)
                avg_x = sum(point[0] for point in mouse_points) / len(mouse_points)
                avg_y = sum(point[1] for point in mouse_points) / len(mouse_points)

                new_polygon = Polygon(
                    x=avg_x,
                    y=avg_y,
                    vertices=mouse_points,
                    mass=0,
                    is_static=True,  # 정적인 다각형
                    name="Player Polygon (Static)"
                )
                print("정적인 다각형 생성")

                # Scene에 추가
                Scene.add(new_polygon)
                polygon_created = True
                mouse_points = []  # 점 초기화
                fragment = None

            elif event.key == pygame.K_LEFT:
                move_left = True
            elif event.key == pygame.K_RIGHT:
                move_right = True
            elif event.key == pygame.K_UP:
                move_up = True
            elif event.key == pygame.K_DOWN:
                move_down = True

            # F 키를 누르면 파편으로 변환
            elif event.key == pygame.K_f and new_polygon:
                # 유체 생성
                area = sum([abs(v.cross(new_polygon.local_vertices[(i + 1) % len(new_polygon.local_vertices)])) for i, v in enumerate(new_polygon.local_vertices)]) / 2
                radius = 10  # 각 원의 반지름
                num_circles = max(3, int(area / (3.14 * radius**2)))

                fragment = Fragment(new_polygon.center.x, new_polygon.center.y, radius, num_circles)

                for circle in fragment.circles:
                    circle.velocity = Vector2D(0, 0)
                    circle.angular_velocity = 0
                
                Scene.bodies.remove(new_polygon)
                Scene.bodies.extend(fragment.circles)
                Scene.add(fragment)
                new_polygon = None  # 다각형 제거
                

            # P 키를 눌러 다각형을 파티클로 분해
            elif event.key == pygame.K_p and new_polygon:
                # P 키 입력 시 다각형을 파티클로 변환
                print("P 키 입력: 다각형을 파티클로 변환!")

                # 다각형의 중앙점과 부피 계산
                centroid = new_polygon.get_center()  # 중심점 가져오기
                print(f"Polygon 중심: {centroid.x}, {centroid.y}")
                vertices = new_polygon.get_vertices()  # 변환된 꼭짓점 가져오기
                area = new_polygon.calculate_area()  # 부피(관성 모멘트) 계산

                # 다각형의 중심 속도 저장
                polygon_velocity  = new_polygon.velocity  # 다각형의 중심 속도

                # 넓이에 비례하여 파티클 개수 설정
                num_particles = max(10, int(area * 0.05))  

                # 다각형의 중심에서 파티클 생성
                create_particle_effect([centroid.x, centroid.y], num_particles,area)
                
                # 파티클 초기 속도 설정 (다각형의 중심 속도 추가)
                for particle in particles:
                    particle["vel"][0] += polygon_velocity .x  # x 방향 속도 추가
                    particle["vel"][1] += polygon_velocity .y  # y 방향 속도 추가

                
                Scene.bodies.remove(new_polygon)  # 다각형 제거
                new_polygon = None  # 다각형 객체도 None으로 설정

            elif event.key == pygame.K_r and fragment:


                # Fragment의 각 원을 Scene에서 제거
                for circle in fragment.circles:
                    if circle in Scene.bodies:
                        Scene.bodies.remove(circle)  # 원을 Scene에서 제거

                restored_polygon = fragment.restore_to_polygon()

                Scene.add(restored_polygon)
                Scene.bodies.remove(fragment)  # Scene에서 Fragment 제거
                fragment = None  # Fragment 객체도 None으로 설정

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                move_left = False
            elif event.key == pygame.K_RIGHT:
                move_right = False
            elif event.key == pygame.K_UP:
                move_up = False
            elif event.key == pygame.K_DOWN:
                move_down = False


    # 유체 제어
    if fragment:
        fragment.update_center()
        for circle in fragment.circles:
            
            if move_left:
                circle.velocity[0] -= PLAYER_SPEED_X/2
            if move_right:
                circle.velocity[0] += PLAYER_SPEED_X/2
            if move_up:
                circle.velocity[1] += PLAYER_SPEED_Y/2
            if move_down:
                circle.velocity[1] -= PLAYER_SPEED_Y/2

    # 움직이는 다각형 이동
    if new_polygon:
        if move_left:
            new_polygon.velocity[0] -= PLAYER_SPEED_X
        if move_right:
            new_polygon.velocity[0] += PLAYER_SPEED_X
        if move_up:
            new_polygon.velocity[1] += PLAYER_SPEED_Y
        if move_down:
            new_polygon.velocity[1] -= PLAYER_SPEED_Y

    # 물리 시뮬레이션 업데이트
    Scene.step(dt)

    # 파티클 업데이트
    update_particles()

    # 화면 그리기
    screen.fill(COLORS["white"])

        # 파티클 그리기
    draw_particles(screen)

    # 마우스로 생성 중인 점과 선
    for point in mouse_points:
        pygame.draw.circle(screen, COLORS["red"], (point[0], HEIGHT - point[1]), 5)
    if len(mouse_points) > 1:
        pygame.draw.lines(
            screen, COLORS["blue"], False, [(p[0], HEIGHT - p[1]) for p in mouse_points], 2
        )

    # 다각형 및 물리 객체 렌더링
    for body in Scene.bodies:
        if body.name == "Player Polygon (Movable)":
            color = COLORS["red"]
        elif body.name == "Player Polygon (Static)":
            color = COLORS["blue"]
        else:
            color = COLORS["black"]

        if body.shape_type == "Polygon":
            pygame.draw.polygon(
                screen,
                color,
                [(vertex.x, HEIGHT - vertex.y) for vertex in body.get_vertices()],
            )
        elif body.shape_type == "Circle":
            pygame.draw.circle(
                screen,
                COLORS["cyan"],
                (int(body.center[0]), int(HEIGHT - body.center[1])),
                int(body.radius),
            )

    pygame.display.flip()
    clock.tick(FPS)
