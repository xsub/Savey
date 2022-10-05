from PyQt5.QtCore import QRegExp  # NOTE: could Python's re instead
import subprocess
import glob

globals()['HASH'] = {}

if __name__ == "__main__":
    fhash = globals()['HASH']
    #from PyQt5.QtCore import QDateTime, QObject, QRegExp
    frx = QRegExp("[VID|IMG]_(\d+)_(\d+-?\d*)\.[jpg|png|mp4]")
    g = glob.glob("/tmp/IMG*")
    g.sort()

    prev_fdate = ""
    prev_ftime = ""
    prev_ftime_hm = ""
    prev_ftime_hms = ""
    last_index = ""
    index = 0

    for f in g:
        frx.indexIn(f)

        fdate=frx.cap(1)
        ftime=frx.cap(2)
        ftime_hm = ftime[0:4]
        ftime_hms = ftime[0:6]

        if fdate != prev_fdate:
            print("\n=====================")
            prev_fdate = fdate

        if ftime_hm != prev_ftime_hm:
            print("------------")
            prev_ftime_hm = ftime_hm
            if last_index == "":
                last_index = 0

            if last_index != index:
                fhash[(f"{fdate}-{ftime_hm}")] = [last_index, index]
                last_index = index

        ifcopy = ""
        if prev_ftime_hms != ftime_hms:
            prev_ftime_hms = ftime_hms
            print("SET")
        else:
            ifcopy = " - SCALED COPY"


        index+=1
        print(f"{index} F: {f}, '{fdate}', '{ftime}', {ftime_hm}, {ftime_hms} {ifcopy}")


    print (fhash)
