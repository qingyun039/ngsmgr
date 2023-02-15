from ngsmgr.workflow.preprocess import PreProcess

config = {
    'read1': '/path/to/read1.fq.gz',
    'read2': '/path/to/read2.fq.gz',
}

w = PreProcess(config)
w.run()