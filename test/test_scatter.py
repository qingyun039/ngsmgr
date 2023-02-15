from collections.abc import Iterable

def scatter(data, **kwargs):
    inmaps = {}
    for key, val in kwargs.items():
        if val == 'key':
            inmaps['key'] = key
        elif val == 'val':                    # value is str
            inmaps['val'] = key
        elif val[:4] == 'val.':
            try:
                inmaps[int(val[4:])] = key    # value is list
            except:
                inmaps[val[4:]] = key         # value is dict
        else:
            pass                              # other is error
    
    scatter_data = []
    if isinstance(data, dict):
        for key, val in data.items():
            outmaps = {}
            tmpmaps = inmaps.copy()
            outmaps[tmpmaps['key']] = key
            del tmpmaps['key']
            if isinstance(val, (dict, list)):
                for i in tmpmaps:
                    outmaps[inmaps[i]] = val[i]
            else:
                outmaps[tmpmaps['val']] = val
            scatter_data.append(outmaps)
    elif isinstance(data, list):
        for val in data:
            outmaps = {}
            if isinstance(val, (dict,list)):
                for i in inmaps:
                    outmaps[inmaps[i]] = val[i]
            else:
                outmaps[inmaps['val']] = val
            scatter_data.append(outmaps)
    print(scatter_data)
    return scatter_data

samples = {
            'sample1': [
                '/path/to/sample1_R1.fastq.gz',
                '/path/to/sample1_R2.fastq.gz'
            ],
            'sample2': [
                '/path/to/sample2_R1.fastq.gz',
                '/path/to/sample2_R2.fastq.gz'
            ],
            'sample3': [
                '/path/to/sample3_R1.fastq.gz',
                '/path/to/sample3_R2.fastq.gz'
            ]
        }


bamfiles = ['mother.bam', 'father.bam', 'proband.bam']
familes = [
    ['mother1.bam', 'father1.bam', 'proband1.bam'],
    ['mother2.bam', 'father2.bam', 'proband2.bam']
]

scatter(samples, prefix='key', read1='val.0', read2='val.1')  # 
scatter(bamfiles, bamfile='val')
scatter(familes, m='val.0', f='val.1', c='val.2')