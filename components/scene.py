from practice_code.body import Body
from practice_code.collision import collide


class Scene:
    def __init__(self, bodies: list[Body], gravity = 9.8):
        self.bodies: list[Body] = bodies
        self._contact_points = []
        
        
        self.gravity = gravity

    def add(self, body: Body):
        self.bodies.append(body)

    #remove 추가

    def remove(self, body):
        if body in self.bodies:
            self.bodies.remove(body)
            
    def update_position(self, dt):
        for body in self.bodies:
            if body.is_fragment:  # is_fluid 속성으로 Fluid 객체 확인
                for circle in body.circles:  # Fluid 내부의 Circle 객체들 처리
                    if not circle.is_static:
                        circle.center += circle.velocity * dt
                        # 필요한 경우, 각 Circle의 angle과 angular_velocity 업데이트
                        # circle.angle += circle.angular_velocity * dt
                # Fluid 객체의 중심을 업데이트
                body.update_center()
            elif body.is_static == False:  # 일반 Body 객체 처리
                body.center += body.velocity * dt
                body.angle += body.angular_velocity * dt


    def handle_collisions(self):
        self._contact_points = []
        for i in range(len(self.bodies) - 1):
            for j in range(i + 1, len(self.bodies)):
                if self.bodies[i] == self.bodies[j]:
                    continue

                contact_points = collide(self.bodies[i], self.bodies[j])
                if contact_points is None:
                    continue

                for point in contact_points:
                    if point is None:
                        continue

                    self._contact_points.append(point)

    def step(self, dt):
        self.update_position(dt)
        self.handle_collisions()
