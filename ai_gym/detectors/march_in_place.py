import time
import math
from ai_gym.core.base_exercise import BaseExercise


class MarchInPlaceDetector(BaseExercise):
    """Tracks marching from adaptive knee lift; does not depend on foot landmarks."""
    MIN_VISIBILITY=0.40
    RAISE_THRESHOLD=0.18
    RELEASE_THRESHOLD=0.07
    STEP_COOLDOWN_SECONDS=0.20
    MARCH_TIMEOUT_SECONDS=1.50

    def __init__(self):
        super().__init__(measurement_type="time"); self.stage="not_marching"; self.duration_seconds=0.0; self._start_time=None; self._accumulated_duration=0.0; self._left=False; self._right=False; self._baseline={"left":None,"right":None}; self._last_step_time=None; self._last_knee=None; self._last_valid_time=None

    def _lift(self,landmarks,side):
        h,k=(23,25) if side=="left" else (24,26)
        if min(getattr(landmarks[i],"visibility",1.0) for i in (h,k))<self.MIN_VISIBILITY:return None
        return landmarks[h].y-landmarks[k].y

    def _update(self,side,lift,scale):
        state=self._left if side=="left" else self._right
        n=lift/scale
        b=self._baseline[side]
        if b is None:self._baseline[side]=n; b=n
        elif not state and n<b+0.10:self._baseline[side]=0.98*b+0.02*n; b=self._baseline[side]
        change=max(0,n-b); event=False
        if not state and change>=self.RAISE_THRESHOLD: state=True; event=True
        elif state and change<=self.RELEASE_THRESHOLD: state=False
        if side=="left":self._left=state
        else:self._right=state
        return event,change

    def process(self,landmarks):
        now=time.monotonic()
        if landmarks is None or len(landmarks)<27:
            self._handle_missing_frame(now); return {"duration_seconds":round(self.duration_seconds,2),"stage":self.stage,"status":"Landmarks unavailable"}
        left=self._lift(landmarks,"left"); right=self._lift(landmarks,"right")
        if left is None and right is None:
            self._handle_missing_frame(now); return {"duration_seconds":round(self.duration_seconds,2),"stage":self.stage,"status":"Knees not clearly visible"}
        scale=0.25
        if len(landmarks)>11 and min(getattr(landmarks[i],"visibility",1.0) for i in (11,23))>=self.MIN_VISIBILITY: scale=max(math.hypot(landmarks[11].x-landmarks[23].x,landmarks[11].y-landmarks[23].y),0.08)
        events=[]; changes={}
        if left is not None:
            e,c=self._update("left",left,scale); changes["left"]=c
            if e:events.append("left")
        if right is not None:
            e,c=self._update("right",right,scale); changes["right"]=c
            if e:events.append("right")
        if events and (self._last_step_time is None or now-self._last_step_time>=self.STEP_COOLDOWN_SECONDS):
            knee=events[0]
            self._last_step_time=now; self._last_knee=knee; self._last_valid_time=now
            if self._start_time is None:self._start_time=now
            self.stage="marching"
        elif self._last_valid_time is None and (self._start_time is not None):self._last_valid_time=now
        if self._start_time is not None:
            if self._last_step_time is not None and now-self._last_step_time<=self.MARCH_TIMEOUT_SECONDS:self.duration_seconds=self._accumulated_duration+now-self._start_time; self.stage="marching"
            else:self._pause(now)
        return {"duration_seconds":round(self.duration_seconds,2),"stage":self.stage,"left_knee_lift":round(changes.get("left",0),3),"right_knee_lift":round(changes.get("right",0),3),"knee_lift":round(max(changes.values()) if changes else 0,3),"last_knee":self._last_knee,"status":"Keep marching" if self.stage=="marching" else "Lift your knees and march"}

    def _handle_missing_frame(self,now):
        if self._start_time is None:return
        if self._last_step_time is not None and now-self._last_step_time<=self.MARCH_TIMEOUT_SECONDS:self.duration_seconds=self._accumulated_duration+now-self._start_time; return
        self._pause(now)

    def _pause(self,now):
        if self._start_time is not None:self._accumulated_duration+=now-self._start_time
        self._start_time=None; self.duration_seconds=self._accumulated_duration; self.stage="not_marching"

    def reset(self):
        self.reset_common_state(); self.stage="not_marching"; self.duration_seconds=0.0; self._start_time=None; self._accumulated_duration=0.0; self._left=False; self._right=False; self._baseline={"left":None,"right":None}; self._last_step_time=None; self._last_knee=None; self._last_valid_time=None
