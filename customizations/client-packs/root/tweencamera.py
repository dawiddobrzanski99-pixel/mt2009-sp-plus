import app
import tween
import constInfo
import mathUtils
import math

class CameraPitchTween(tween.LerpTween):
    def __init__(self, startValue, endValue, duration):
        tween.LerpTween.__init__(self, startValue, endValue, duration)

    def Process(self, progress):
        (distance, pitch, rotation, height) = app.GetCamera()
        app.SetCamera(distance, self.GetValue(), rotation, height)

class CameraRotationTween(tween.LerpTween):
    def __init__(self, startValue, endValue, duration):
        tween.LerpTween.__init__(self, startValue, endValue, duration)

    def Process(self, progress):
        (distance, pitch, rotation, height) = app.GetCamera()
        app.SetCamera(distance, pitch, self.GetValue(), height)


class CameraHeightTween(tween.LerpTween):
    def __init__(self, startValue, endValue, duration):
        tween.LerpTween.__init__(self, startValue, endValue, duration)

    def Process(self, progress):
        (distance, pitch, rotation, height) = app.GetCamera()
        (x, y, z) = app.GetCameraPosition()
        app.SetCamera2(x, y, self.GetValue(), distance, pitch, rotation)


class CameraLerpTween(tween.Tween):
    def __init__(self, duration):
        tween.Tween.__init__(self, duration)
        self.durationPerStep = self.duration / (len(constInfo.CAMERA_WAYPOINTS)-1)

    def GetValue(self, startValue, endValue):
        delta = endValue - startValue
        return startValue + delta * self.GetStepProgress()

    def GetCurrentStepIndex(self):
        step = int(self.timer/self.durationPerStep)
        if step >= len(constInfo.CAMERA_WAYPOINTS)-1:
            step = len(constInfo.CAMERA_WAYPOINTS) - 2

        return step

    def GetNextStepIndex(self):
        nextStep = self.GetCurrentStepIndex() + 1
        if nextStep >= len(constInfo.CAMERA_WAYPOINTS):
            nextStep = len(constInfo.CAMERA_WAYPOINTS)-1
        return nextStep

    def GetStepProgress(self):
        cze = self.durationPerStep * self.GetCurrentStepIndex()
        return mathUtils.GetProgressClamped01(self.timer - cze, self.durationPerStep)

    def GetDestValues(self, index):
        valueData = constInfo.CAMERA_WAYPOINTS
        distance = valueData[index]["distance"]
        pitch = valueData[index]["pitch"]
        # rotation = valueData[index]["rotation"]
        x = valueData[index]["x"]
        y = valueData[index]["y"]
        z = valueData[index]["z"]
        fov = valueData[index]["fov"]
        return (x, y, z, distance, pitch, fov)

    def GetDestRotation(self):
        rotationSteps = len(constInfo.CAMERA_WAYPOINTS)
        durationPerRotStep = self.duration / (rotationSteps-1)
        rotStep = int(self.timer / durationPerRotStep)
        if rotStep >= rotationSteps-1:
            rotStep = rotationSteps - 2

        nextRotStep = rotStep + 1

        oldRot = constInfo.CAMERA_WAYPOINTS[rotStep]["rotation"]
        newRot = constInfo.CAMERA_WAYPOINTS[nextRotStep]["rotation"]

        #rot step progress
        cze = durationPerRotStep * rotStep
        rotationStepProgress = mathUtils.GetProgressClamped01(self.timer - cze, durationPerRotStep)

        return mathUtils.interpolate_rotation(oldRot, newRot, rotationStepProgress)

    def Process(self, progress):
        (oldX, oldY, oldZ, oldDistance, oldPitch, oldFov) = self.GetDestValues(self.GetCurrentStepIndex())
        (newX, newY, newZ, newDistance, newPitch, newFov) = self.GetDestValues(self.GetNextStepIndex())

        destX = self.GetValue(oldX, newX)
        destY = self.GetValue(oldY, newY)
        destZ = self.GetValue(oldZ, newZ)
        destDistance = self.GetValue(oldDistance, newDistance)
        destPitch = self.GetValue(oldPitch, newPitch)
        # destRotation = self.GetValue(oldRotation, newRotation)
        destRotation = self.GetDestRotation()
        destFov = self.GetValue(oldFov, newFov)

        app.SetCamera2(destX, destY, destZ, destDistance, destPitch, destRotation)
        app.SetFov(destFov)


class CameraBezierTween(tween.Tween):
    def __init__(self, duration, num_points, isRotationBezierInterpolation):
        tween.Tween.__init__(self, duration)
        self.num_points = num_points
        self.durationPerStep = self.duration / (self.num_points-1)
        self.isRotationBezierInterpolation = isRotationBezierInterpolation

    def GetValue(self, startValue, endValue):
        delta = endValue - startValue
        return startValue + delta * self.GetStepProgress()

    def GetCurrentStepIndex(self):
        step = int(self.timer/self.durationPerStep)
        if step >= self.num_points-1:
            step = self.num_points - 2

        return step

    def GetNextStepIndex(self):
        nextStep = self.GetCurrentStepIndex() + 1
        if nextStep >= self.num_points:
            nextStep = self.num_points-1
        return nextStep

    def GetStepProgress(self):
        cze = self.durationPerStep * self.GetCurrentStepIndex()
        return mathUtils.GetProgressClamped01(self.timer - cze, self.durationPerStep)

    def GetDestValues(self, index):
        valueData = constInfo.CAMERA_BEZIER_POINTS
        distance = valueData["distance"][(self.num_points-1)-index]
        pitch = valueData["pitch"][(self.num_points-1)-index]
        if self.isRotationBezierInterpolation:
            rotation = valueData["rotation"][(self.num_points-1)-index]
        else:
            rotation = 0
        x = valueData["x"][(self.num_points-1)-index]
        y = valueData["y"][(self.num_points-1)-index]
        z = valueData["z"][(self.num_points-1)-index]
        fov = valueData["fov"][(self.num_points-1)-index]

        return (x, y, z, distance, pitch, rotation, fov)

    def GetDestRotation(self):
        rotationSteps = len(constInfo.CAMERA_WAYPOINTS)
        durationPerRotStep = self.duration / (rotationSteps-1)
        rotStep = int(self.timer / durationPerRotStep)
        if rotStep >= rotationSteps-1:
            rotStep = rotationSteps - 2

        nextRotStep = rotStep + 1

        oldRot = constInfo.CAMERA_WAYPOINTS[rotStep]["rotation"]
        newRot = constInfo.CAMERA_WAYPOINTS[nextRotStep]["rotation"]

        #rot step progress
        cze = durationPerRotStep * rotStep
        rotationStepProgress = mathUtils.GetProgressClamped01(self.timer - cze, durationPerRotStep)

        return mathUtils.interpolate_rotation(oldRot, newRot, rotationStepProgress)

    def Process(self, progress):
        (oldX, oldY, oldZ, oldDistance, oldPitch, oldRotation, oldFov) = self.GetDestValues(self.GetCurrentStepIndex())
        (newX, newY, newZ, newDistance, newPitch, newRotation, newFov) = self.GetDestValues(self.GetNextStepIndex())

        destX = self.GetValue(oldX, newX)
        destY = self.GetValue(oldY, newY)
        destZ = self.GetValue(oldZ, newZ)
        destDistance = self.GetValue(oldDistance, newDistance)
        destPitch = self.GetValue(oldPitch, newPitch)
        if self.isRotationBezierInterpolation:
            destRotation = self.GetValue(oldRotation, newRotation)
        else:
            destRotation = self.GetDestRotation()
        destFov = self.GetValue(oldFov, newFov)

        app.SetCamera2(destX, destY, destZ, destDistance, destPitch, destRotation)
        app.SetFov(destFov)
