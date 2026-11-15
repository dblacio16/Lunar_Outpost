"""Optional MP4 intro: uses OpenCV if installed; always falls back gracefully."""
from settings import VIDEOS,WIDTH,HEIGHT

class IntroVideo:
    def __init__(self,pygame):
        self.pg=pygame
        self.capture=None
        self.cv2=None
        self.frame=None
        try:
            import cv2
            file=VIDEOS/'fondo_lunar.mp4'
            if not file.is_file():return
            capture=cv2.VideoCapture(str(file))
            if capture.isOpened():
                self.capture=capture
                self.cv2=cv2
            else:capture.release()
        except (ImportError,OSError):pass

    def update(self):
        if self.capture is None:return
        ok,frame=self.capture.read()
        if not ok:
            self.capture.set(self.cv2.CAP_PROP_POS_FRAMES,0)
            ok,frame=self.capture.read()
            if not ok:return
        frame=self.cv2.resize(frame,(WIDTH,HEIGHT))
        frame=self.cv2.cvtColor(frame,self.cv2.COLOR_BGR2RGB)
        self.frame=self.pg.image.frombuffer(frame.tobytes(),(WIDTH,HEIGHT),'RGB').copy()

    def release(self):
        if self.capture is not None:self.capture.release()
