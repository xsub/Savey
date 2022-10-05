# (c) 2022 Linbedded Savey//PyQt5
#import PIL
import os
from PIL import Image
from PIL.ExifTags import TAGS


class SaveyExif:

    def __init__(self, filename):

        self.exif_hash = {}
        self.current_table_entry = 0
        self.keys = []

        if os.path.exists(filename):
            img = Image.open(filename)
        else:
            raise FileNotFoundError

        for k, v in img.getexif().items():
            tag = TAGS.get(k)
            self.keys.append(tag)
            self.exif_hash[tag] = v
            # print(f"{tag}: {v}")


    def __iter__(self):
        return self

    def __next__(self):
        if self.current_table_entry < len(self.keys)-1:
            tag = self.keys[self.current_table_entry]
            self.current_table_entry = self.current_table_entry + 1
            value = self.exif_hash[tag]
            return (tag, value)
        else:
            raise StopIteration
