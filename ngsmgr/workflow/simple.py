from ngsmgr.base import Pipeline
from ngsmgr.workflow.base import BaseWorkflow

class Simple(BaseWorkflow):
    modules = [
        'ngsmgr.modules.inline:fastp',
        'ngsmgr.modules.inline:bwa_mem'
    ]
    def run(self):
        for sample in self.config['samples']:
            read1 = self.config['samples'][sample][0]
            read2 = self.config['samples'][sample][1]
            prefix = sample
            self.config['prefix'] = prefix

            job = self.fastp(read1, read2, prefix=prefix, args='fastp_args').bwa_mem('genome_ref', 'read1', 'read2')
        
        #self.scatter(self.config['samples'], prefix='key', read1='val.0', read2='val.1').fastp()
        pass

if __name__ == '__main__':
    config = {
        'genome_ref':'/path/to/hg19.fasta',
        'samples': {
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
        },
        'fastp_args': {
            'path': '/path/to/fastp',
            '--n_base_limit': 5,
            '--average_qual': 20,
            '--adapter_sequence': 'abcdefg',
            '--adapter_sequence_r2': 'gfedcba',
            'resource': {
                'cpus': 8,
                'mems': '8G',
            }
        },
        # 'bwa_args': {
        #     '-M': None,
        #     '-Y': None,
        #     '-t': 18
        # }
    }
    s = Simple(config)
    s.run()
    print(s.config.heh)
    #s.outs()