import os
import time
import datetime

def delete_file(path_target,deadline):
	for f in os.listdir(path_target):
		f = os.path.join(path_target, f)
		if os.path.isfile(f):
			#timestamp_now = datetime.datetime.now().timestamp()
			timestamp_now = time.time()
			is_old = os.stat(f).st_mtime < timestamp_now - (deadline  * 1 * 60 * 60)
			if is_old:
				os.remove(f)
				print (f, 'is deleted')
def timestamp(self):
    "Return POSIX timestamp as float"
    if self._tzinfo is None:
        return _time.mktime((self.year, self.month, self.day,
                             self.hour, self.minute, self.second,
                             -1, -1, -1)) + self.microsecond / 1e6
    else:
        return (self - _EPOCH).total_seconds()
