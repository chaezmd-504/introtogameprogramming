from components.vector import Vector2D
from practice_code.body import Body, Polygon, Rectangle, Circle


def collide(body_1: Body, body_2: Body, include_rotation = True):
    normal, depth = None, None

    if body_1.shape_type == "Polygon" and body_2.shape_type == "Polygon":
        normal, depth = polygons_collision(body_1, body_2) 
    elif body_1.shape_type == "Circle" and body_2.shape_type == "Circle":
        normal, depth = circles_collision(body_1, body_2)
    elif body_1.shape_type == "Polygon" and body_2.shape_type == "Circle":
        normal, depth = polygon_circle_collision(body_1, body_2)
    elif body_1.shape_type == "Circle" and body_2.shape_type == "Polygon":
        normal, depth = polygon_circle_collision(body_2, body_1)

    if normal is None or depth is None:
        return
    
    if body_1.shape_type == "Polygon" and body_2.shape_type == "Polygon":
        contact_points = polygons_contact_points(body_1, body_2)
    elif body_1.shape_type == "Circle" and body_2.shape_type == "Circle":
        contact_points = circles_contact_points(body_1, body_2)
    elif body_1.shape_type == "Polygon" and body_2.shape_type == "Circle":
        contact_points = polygon_circle_contact_points(body_1, body_2)
    elif body_1.shape_type == "Circle" and body_2.shape_type == "Polygon":
        contact_points = polygon_circle_contact_points(body_2, body_1)
        normal = -normal
        
        
    if include_rotation:
        response_with_rotation(body_1, body_2, normal, depth, contact_points)
    else:
        response(body_1, body_2, normal, depth)

    return contact_points
###############################################################################################################
                        # Practice Code
###############################################################################################################
def response(body_1: Body, body_2: Body, normal_vector: Vector2D, penetration_depth: float):
    # Reverse the normal vector
    normal_vector *= -1

    # Separate the bodies to prevent overlap (Implement this function if not provided)
    separate_bodies(body_1, body_2, normal_vector, penetration_depth)
    
    # Calculate relative velocity between the two bodies
    relative_velocity = body_2.velocity - body_1.velocity
    
    # Compute the penetration velocity along the normal vector
    penetration_velocity = relative_velocity.dot(normal_vector)

    # Skip if bodies are moving away from each other
    if penetration_velocity > 0:
        return
    
    # Compute the coefficient of restitution (bounciness)
    r = min(body_1.bounce, body_2.bounce)  
    # or use r = (body_1.bounce + body_2.bounce)/2
    
    # Compute the impulse scalar (j)
    j = -(1+r)*penetration_velocity  # Fill in the denominator: Consider both bodies' masses
    j/=1/body_1.mass+1/body_2.mass

    # Compute the impulse vector
    impulse = normal_vector * j

    # Update velocities for body_1 and body_2 if they are not static
    if not body_1.is_static:
        body_1.velocity -= impulse/body_1.mass  # Fill in the velocity update for body_1
    if not body_2.is_static:
        body_2.velocity += impulse/body_2.mass  # Fill in the velocity update for body_2

    



def response_with_rotation(body_1: Body, body_2: Body, normal_vector: Vector2D, penetration_depth: float, contact_point: list[Vector2D]):
    # Step 1: Reverse the normal vector
    normal_vector *= -1  

    # Step 2: Separate the bodies to prevent overlap
    separate_bodies(body_1, body_2, normal_vector, penetration_depth)
    
    # Step 3: Calculate the contact point
    if len(contact_point) == 2: 
        contact_point = (contact_point[0] + contact_point[1]) / 2
    else:
        contact_point = contact_point[0]

    # Step 4: Calculate vectors from the body centers to the contact point
    r_1 = contact_point - body_1.center  
    r_2 = contact_point - body_2.center 

    # Step 5: Compute perpendicular vectors for angular velocity calculation
    r_1_perp = Vector2D(-r_1.y, r_1.x) 
    r_2_perp = Vector2D(-r_2.y, r_2.x)  

    # Step 6: Calculate relative velocity at the contact point
    relative_velocity = (body_2.velocity + r_2_perp*body_2.angular_velocity) - (body_1.velocity + r_1_perp*body_1.angular_velocity)  
    penetration_velocity = relative_velocity.dot(normal_vector)  

    # Step 7: Skip if bodies are moving away
    if penetration_velocity > 0:
        return

    # Step 8: Compute the coefficient of restitution (bounciness)
    r = min(body_1.bounce, body_2.bounce) 
    # or use r = (body_1.bounce + body_2.bounce)/2

    # Step 9: Compute the impulse scalar (j) 
    #j = -(1+r)*penetration_velocity
    #j/= 1/body_1.mass + 1/body_2.mass + (r_1_perp.dot(normal_vector)**2)/body_1.inertia + (r_2_perp.dot(normal_vector)**2)/body_2.inertia  
# 이부분 수정했음 분모가 0일경우 때문에
    denominator = (
        1 / body_1.mass + 1 / body_2.mass + 
        (r_1_perp.dot(normal_vector)**2) / max(body_1.inertia, 1e-8) +  # Avoid division by zero
        (r_2_perp.dot(normal_vector)**2) / max(body_2.inertia, 1e-8)
    )
    
    if denominator == 0:  # Check if the denominator is zero
        return

    j = -(1 + r) * penetration_velocity / denominator

    # Step 10: Compute the impulse vector
    impulse = normal_vector * j  

    # Step 11: Update body_1's linear velocity and angular velocity
    body_1.velocity -= impulse/body_1.mass  
    body_1.angular_velocity -= r_1.cross(impulse)/body_1.inertia  

    # Step 12: Update body_2's linear velocity and angular velocity
    body_2.velocity += impulse/body_2.mass  
    body_2.angular_velocity += r_2.cross(impulse)/body_2.inertia  




############################################################################################################################################################

def polygons_collision(polygon_1: Polygon, polygon_2: Polygon):
    normal = Vector2D(0, 0)
    depth = float('inf')
    
    vertices1 = polygon_1.get_vertices()
    vertices2 = polygon_2.get_vertices()
    
    for i in range(len(vertices1)):
        va = vertices1[i]
        vb = vertices1[(i + 1) % len(vertices1)]
        edge = vb - va
        axis = Vector2D(-edge.y, edge.x).normalize()
        min_a, max_a = project_vertices(polygon_1.get_vertices(), axis)
        min_b, max_b = project_vertices(polygon_2.get_vertices(), axis)

        if min_a >= max_b or min_b >= max_a:
            return None, None

        axis_depth = min(max_b - min_a, max_a - min_b)

        if axis_depth < depth:
            depth = axis_depth
            normal = axis

    # Add axes from polygon_2
    for i in range(len(vertices2)):
        va = vertices2[i]
        vb = vertices2[(i + 1) % len(vertices2)]
        edge = vb - va
        axis = Vector2D(-edge.y, edge.x).normalize()
        min_a, max_a = project_vertices(polygon_1.get_vertices(), axis)
        min_b, max_b = project_vertices(polygon_2.get_vertices(), axis)

        if min_a >= max_b or min_b >= max_a:
            return None, None

        axis_depth = min(max_b - min_a, max_a - min_b)

        if axis_depth < depth:
            depth = axis_depth
            normal = axis

    direction = (polygon_1.center - polygon_2.center).normalize()

    if direction.dot(normal) < 0:
        normal *= -1


    return normal, depth

def polygon_circle_collision(polygon: Polygon, circle: Circle):
    assert polygon.shape_type == "Polygon" and circle.shape_type == "Circle", \
        "Shape types of polygon and circle must be 'Polygon' and 'Circle' respectively."
    
    normal = Vector2D(0, 0)
    penetration_depth = float('inf')
    
    vertices = polygon.get_vertices()
    
    for i in range(len(vertices)):
        va = vertices[i]
        vb = vertices[(i + 1) % len(vertices)]

        edge = vb - va

        axis = Vector2D(-edge.y, edge.x).normalize()
       
        # project circle onto axis
        min_a, max_a = project_vertices(vertices, axis)
        min_b, max_b = project_circle(circle.center, circle.radius, axis)
        
        if max_a <= min_b or max_b <= min_a:
            return None, None
        
        axis_depth = min(max_b - min_a, max_a - min_b)

        if axis_depth < penetration_depth:
            penetration_depth = axis_depth
            normal = axis
    
    cp_index = find_closest_point_on_polygon(circle.center, vertices)
    
    cp = vertices[cp_index]
    
    axis = (cp - circle.center).normalize()

    min_a, max_a = project_circle(circle.center, circle.radius, axis)
    min_b, max_b = project_vertices(vertices, axis)

    if max_a <= min_b or max_b <= min_a:
        return None, None
    
    axis_depth = min(max_b - min_a, max_a - min_b)

    if axis_depth < penetration_depth:
        penetration_depth = axis_depth
        normal = axis


    direction = (polygon.center - circle.center).normalize()
   
    if direction.dot(normal) < 0:
        normal *= -1
        
    return normal, penetration_depth


def circles_collision(body_1: Circle, body_2: Circle):
    assert body_1.shape_type == "Circle" and body_2.shape_type == "Circle", \
        "Both body_1 and body_2 must be of shape_type 'Circle' for Circle collision."
    
    distance = Vector2D.distance(body_1.center, body_2.center)

    if distance >= body_1.radius + body_2.radius:

        return None, None
    

    normal_vector = (body_1.center - body_2.center).normalize()

    penetration_depth  = body_1.radius + body_2.radius - distance


    return normal_vector, penetration_depth


def project_circle(center, radius: float, axis: Vector2D):
    direction = axis.normalize()
    direction_and_radius = direction * radius

    p1 = center + direction_and_radius
    p2 = center - direction_and_radius

    min_proj = p1.dot(axis)
    max_proj = p2.dot(axis)

    if min_proj > max_proj:
        min_proj, max_proj = max_proj, min_proj

    return min_proj, max_proj




def project_vertices(vertices: list[Vector2D], axis: Vector2D):
    min_proj = float('inf')
    max_proj = float('-inf')

    for v in vertices:
        proj = v.dot(axis)

        if proj < min_proj:
            min_proj = proj
        if proj > max_proj:
            max_proj = proj

    return min_proj, max_proj

def project_circle(center, radius: float, axis: Vector2D):
    direction = axis.normalize()
    direction_and_radius = direction * radius

    p1 = center + direction_and_radius
    p2 = center - direction_and_radius

    min_proj = p1.dot(axis)
    max_proj = p2.dot(axis)

    if min_proj > max_proj:
        min_proj, max_proj = max_proj, min_proj

    return min_proj, max_proj

def find_closest_point_on_polygon(circle_center: Vector2D, vertices: list[Vector2D]):
    result = -1
    min_distance = float('inf')

    for i, v in enumerate(vertices):
        dist = Vector2D.distance(v, circle_center)

        if dist < min_distance:
            min_distance = dist
            result = i

    return result

def separate_bodies(body_1: Body, body_2: Body, normal, penetration_depth):
    separation_vector = normal * penetration_depth

    
    if body_1.is_static:
        body_2.center += separation_vector
    elif body_2.is_static:
        body_1.center -= separation_vector
    else:
        body_1.center -= separation_vector / 2
        body_2.center += separation_vector / 2



def point_to_line_segment_projection(point: Vector2D, a: Vector2D, b: Vector2D):
    ab = b - a 
    ap = point - a 
    
    proj = ap.dot(ab)
    d = proj / ab.dot(ab) 

    if d <= 0:
        contact_point = a
    elif d >= 1:
        contact_point = b
    else: 
        contact_point = a + ab * d

    distance = Vector2D.distance(contact_point, point)

    return contact_point, distance


def polygons_contact_points(polygon_1: Polygon, polygon_2: Polygon):
    epsilon = 0.0005
    min_distance = float('inf')
    contact_point_1 = None
    contact_point_2 = None

    for i in range(len(polygon_1.get_vertices())):
        vp = polygon_1.get_vertices()[i]
        for j in range(len(polygon_2.get_vertices())):
            va = polygon_2.get_vertices()[j]
            vb = polygon_2.get_vertices()[(j + 1) % len(polygon_2.get_vertices())]

            cp, distance = point_to_line_segment_projection(vp, va, vb)

            if contact_point_1 is not None and abs(distance - min_distance) < epsilon and not cp.distance_to(contact_point_1) < epsilon:
                contact_point_2 = cp
            elif distance < min_distance:
                min_distance = distance
                contact_point_2 = None
                contact_point_1 = cp

    for i in range(len(polygon_2.get_vertices())):
        vp = polygon_2.get_vertices()[i]
        for j in range(len(polygon_1.get_vertices())):
            va = polygon_1.get_vertices()[j]
            vb = polygon_1.get_vertices()[(j + 1) % len(polygon_1.get_vertices())]

            cp, distance = point_to_line_segment_projection(vp, va, vb)

            if contact_point_1 is not None and abs(distance - min_distance) < epsilon and not cp.distance_to(contact_point_1) < epsilon:
                contact_point_2 = cp
            elif distance < min_distance:
                min_distance = distance
                contact_point_2 = None
                contact_point_1 = cp

    return [cp for cp in [contact_point_1, contact_point_2] if cp is not None]

def polygon_circle_contact_points(polygon: Polygon, circle: Circle):

    min_distance = float('inf')
    vertices = polygon.get_vertices()
    
    for i in range(len(vertices)):
        va = vertices[i]
        vb = vertices[(i + 1) % len(vertices)]

        cp, distance = point_to_line_segment_projection(circle.center, va, vb)

        if distance < min_distance:
            min_distance = distance
            contact_point = cp

        
    return [contact_point]

def circles_contact_points(body_1: Circle, body_2: Circle):
    normal = (body_2.center - body_1.center).normalize()

    contact_point = body_1.center + normal * body_1.radius

    return [contact_point]

