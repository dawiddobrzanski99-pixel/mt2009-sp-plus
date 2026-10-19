import app
import mathUtils

class TweenManager:
	def __init__(self):
		self.tweens = []

	# def __del__(self):
	#	 print "tweenManager destroyed"

	def OnUpdate(self):
		for tween in self.tweens:
			tween.OnUpdate()

	def CreateTween(self, tween):
		tween.destroyEvent = self.DestroyTween
		self.tweens.append(tween)
		# print "tween added to self.tweens"

	def DestroyTween(self, tween):
		self.tweens.remove(tween)
		tween.Destroy()
		del tween

	def Destroy(self):
		for tween in self.tweens:
			tween.Destroy()
		self.tweens = []


class Tween:
	def __init__(self, duration):
		self.duration = int(duration*1000)
		self.timer = 0
		self.isStarted = False
		self.destroyEvent = None

		# print "tween created"

	# def __del__(self):
	#	 print "tween destroyed"

	def Destroy(self):
		self.isStarted = False
		self.destroyEvent = None
		self.timer = 0
		self.duration = 0

	def OnUpdate(self):
		if self.isStarted:

			# print "tween " + str(self.timer)
			self.timer += app.FIXED_UPDATE_TIMESTEP
			self.Process(self.GetProgress())
			if self.timer >= self.duration:
				self.OnFinish()

	def OnFinish(self):
		# print "finish tween"
		self.StopTween()
		if self.destroyEvent:
			self.destroyEvent(self)

	def StartTween(self):
		self.isStarted = True
		self.Process(self.GetProgress())

	def StopTween(self):
		self.isStarted = False
		self.Process(self.GetProgress())

	def GetProgress(self):
		return mathUtils.GetProgressClamped01(self.timer, self.duration)

	def Process(self, progress):
		return



class LerpTween(Tween):
	def __init__(self, startValue, endValue, duration):
		Tween.__init__(self, duration)
		self.startValue = startValue
		self.endValue = endValue

	def GetValue(self):
		delta = self.endValue - self.startValue
		return self.startValue + delta * self.GetProgress()
