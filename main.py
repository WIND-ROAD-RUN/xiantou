from Mt.MApplication import MApplication
from Mt.MMainWindow import MMainWindow
from Mt.MPushButton import MPushButton
from Mt.MCheckBox import MCheckBox
from Mt.MLabel import MLabel
from Mt.MDialog import MDialog
from Mt.MTabWidget import MTabWidget
from Mt.GPIOBlink import GPIOBlink

from MaixCam.MainWindow import MaixCamMainWindow
from MaixCam.FrameCallBefor import FrameCallBefore
from MaixCam.RunningInfo import RunningInfo, RunMode

from MaixCam.Modules import Modules

from maix import image

def iniEnv():

    # using chinese font
    image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf", size=32)
    image.set_default_font("sourcehansans")
    RunningInfo().instance().run_mode = RunMode.STOP
    Modules().instance()

def main():
    iniEnv()
    app = MApplication()
    win = MaixCamMainWindow(0, 0, app.img_width, app.img_height,margin=0)
    
    frameCallBefore = FrameCallBefore()

    app.setPreFrameCallback(frameCallBefore)

    app.setMainWindow(win)
    win.show()      
    app.exec(interval_ms=0)

if __name__ == "__main__":
    main()