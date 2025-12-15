import hou, re, os



def atoi(text):
    return int(text) if text.isdigit() else text



def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]



def multisort(l):
    l.sort(key=natural_keys)
    return l



def splitver(string,frmats):
    frmat = None
    sec = None

    for fmt in frmats:
        if len(re.findall('%s(?=\d+)'%(fmt), string)) > 0:
            sec = re.split('%s(?=\d+)'%(fmt), string)
            sec = [sec[0]] + re.split(r'(^[^\D]+)', sec[1])[1:]

            frmat = fmt
            break
    
    return sec,frmat



def foldersearch(path,matchlist,frmat,sec):
    padding = 3
    fmt = '_v'
    for f in os.listdir(path[0]):
        result = splitver(f,frmat)

        if result[0]:
            if result[0][0] == sec[0] and result[0][2] == sec[2]:
                result,fmt = result
                matchlist.append(result[1])
                padding = len(result[1])

    matchlist = list(dict.fromkeys(matchlist))
    matchlist.sort(key=natural_keys)
    matchlist.reverse()
    
    return matchlist,padding,fmt



def buildpath(padding,path,matchlist,frmat,sec):
    matchlist = [int(v) for v in matchlist]
    v = str(max(matchlist)+1).zfill(padding)

    return '%s/%s%s%s%s'%(path[0],sec[0],frmat,v,sec[2])



def incsave():
    
    path = hou.hipFile.path().rsplit('/',1)
    
    sec,frmat = splitver(path[1],['_v','_V'])
    
    if sec:
        matchlist = [sec[1]]
        padding = len(sec[1])
        matchlist = foldersearch(path,matchlist,[frmat],sec)[0]
        
    else:
        sec = path[1].rsplit('.',1)
        sec[1]='.'+sec[1]
        sec.insert(1,'')

        frmat = ['_v','_V']
        
        matchlist,padding,frmat = foldersearch(path,['000'],frmat,sec)

    hippath = buildpath(padding,path,matchlist,frmat,sec)

    hou.hipFile.save(hippath,True)