from pyb import millis

def savetofile(data: str, file_name='output.txt', rewrite=False, end='\n', timestamp=True):
    mls = millis()
    sec = (mls//1000) % 60
    mins = (mls//(60*1000)) % 60
    hours = (mls//(60*24*1000))
    f = open(file_name, 'w' if rewrite else 'a')
    starttime = str(hours)+'h'+str(mins)+'m'+str(sec)+'s:\t' if timestamp else ''
    data_to_write = starttime+str(data)+end
    f.write(data_to_write)
    f.close()
    return data_to_write