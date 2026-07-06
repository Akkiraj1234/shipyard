from pathlib import Path
import sys

RoadmapCommand = None
InitCommand = None
DoctorCommand = None


registry = {
    "roadmap": RoadmapCommand,
    "init": InitCommand,
    "doctor": DoctorCommand,
}




def get_args():
    args = sys.argv
    return args