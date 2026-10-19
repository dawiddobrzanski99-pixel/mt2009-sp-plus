import math

def GetProgressClamped01(val, maxVal):
    if maxVal == 0:
        return 0
    return min(float(val) / maxVal, 1)

def Clamp01(val):
    return min(max(val, 0.0), 1.0)

# def GetLerp(v1, v2, t):
#     delta = 0
#     if v2 < v1:
#         delta = v1 + v2
#     elif v2 > v1:
#         delta = v1 - v2
#     else:
#         return v1
#     return v1 + delta * t

def GetLerp(v1, v2, t):
    delta = v2 - v1
    return v1 + delta * t

def GetEaseInCirc(v):
    return 1 - math.sqrt(1-math.pow(v, 2))

def GetEaseInQuint(v):
    return math.pow(v, 4)

def GetEaseOutCirc(v):
    return math.sqrt(1 - math.pow(v-1, 2))

def GetEaseInExpo(v):
    if v > 0:
        return math.pow(2, 10 * v - 10)
    return v

def GetEaseOutExpo(v):
    if v < 1:
        return math.pow(2, -10 * v)
    return v

def binomial_coefficient(n, k):
    """
    Calculate binomial coefficient (n choose k).

    Parameters:
        n (int): Total number of items.
        k (int): Number of items to choose.

    Returns:
        int: Binomial coefficient value.
    """
    result = 1
    for i in range(1, k + 1):
        result = result * (n - i + 1) // i
    return result


def bezier(t, *values):
    """
    Compute a point on a Bezier curve.

    Parameters:
        t (float): Parameter ranging from 0 to 1.
        *points (tuple or list): Control points.

    Returns:
        tuple or list: Interpolated point on the Bezier curve.
    """
    n = len(values) - 1
    u = 1 - t

    p = sum(binomial_coefficient(n, i) * t ** (n - i) * u ** i * values[i] for i in range(n + 1))

    return p


def bezier_rotation(t, *angles):
    """
    Interpolate rotation values using a Bezier curve.

    Parameters:
        t (float): Parameter ranging from 0 to 1.
        *angles (float): Control rotation values.

    Returns:
        float: Interpolated rotation value.
    """
    n = len(angles) - 1
    u = 1 - t

    # Ensure all angles are within the -180 to 180 range
    angles = [(angle + 180) % 360 - 180 for angle in angles]

    # Calculate the shortest path for interpolation
    for i in range(1, len(angles)):
        diff = angles[i] - angles[i - 1]
        if abs(diff) > 180:
            if diff > 0:
                angles[i] -= 360
            else:
                angles[i] += 360

    p = sum(binomial_coefficient(n, i) * t**(n-i) * u**i * angles[i] for i in range(n + 1))

    # Wrap the result within the -180 to 180 range
    result = (p + 180) % 360 - 180

    return result

def interpolate_rotation(start, end, t):
    """
    Interpolate rotation values, handling wrapping around -180 to 180 range.

    Parameters:
        start (float): Starting rotation value.
        end (float): Ending rotation value.
        t (float): Interpolation parameter. Should be in the range [0, 1].

    Returns:
        float: Interpolated rotation value.
    """
    # Ensure both start and end are within the -180 to 180 range
    start = (start + 180) % 360 - 180
    end = (end + 180) % 360 - 180

    # Calculate the shortest path for interpolation
    diff = end - start
    if abs(diff) > 180:
        if diff > 0:
            end -= 360
        else:
            end += 360

    # Perform linear interpolation
    result = start + t * (end - start)

    # Wrap the result within the -180 to 180 range
    result = (result + 180) % 360 - 180

    return result
