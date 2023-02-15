import copy
from ngsmgr.utils.biofile import fasta_dict_file
from ngsmgr.workflow.base import BaseWorkflow
from ngsmgr.errors import AnalysisConfigError

class PreProcess(BaseWorkflow):
    """PreProcess workflow class
    
    数据预处理流程，针对每个样本进行以下处理：
        1. 使用fastqc对原始下机数据进行质控
        2. 提取UMI序列（如果有）
        3. 使用fastp进行接头和低质量序列过滤
        4. 使用bwa比对到参考基因组
        5. 使用samtools进行PCR重复标识（可选)
        6. 使用fgbio进行基于UMI的矫正（可选）
        7. 使用GATK进行碱基质量值矫正
        8. 质控信息生成整理
    
    Config:
        sample: 样本名
        platform: 测序平台
        read1: fastq 1
        read2: fastq 2
        umi1: umi1
        umi2: umi2
        adapter1: adapter 1
        adapter2: adapter 2
    """
    modules = [ 'ngsmgr.modules.inline:'+mod for mod in 
                    ['fastp', 
                     'bwa_mem', 
                     'samtools_markdup', 
                     'gatk_baserecalibrator', 
                     'gatk_applybqsr',
                     'gatk_bedtointervallist',
                     'gatk_collecthsmetrics',
                     'gatk_collectinsertsizemetrics',
                     'gatk_estimatelibrarycomplexity',
                     'bamdst',
                    ]
              ]
    modules.append('ngsmgr.modules.common:mosdepth')

    def run(self):
        """workflow generate"""
        if not (self.config.read1 and self.config.read2):
            raise AnalysisConfigError("没有指定输入fastq文件")
        if not self.config.reference:
            raise AnalysisConfigError("没有指定参考基因组文件")
        (self.fastp(self.config.read1, self.config.read2, args=self.config.fastp_args)
             .bwa_mem(self.config.reference, 'read1', 'read2', args=self.config.bwa_args)
             .samtools_markdup('bamout', args=self.config.markdup_args))
        if self.config.bqsr_args:
            (self.gatk_baserecalibrator('bamout', self.config.reference)
                .gatk_applybqsr('bamout', 'bqsr_table', self.config.reference, args=self.config.bqsr_args))
        
        # QC
        if self.config.bedfile:
            align = self.p
            dictfile = fasta_dict_file(self.config.reference)
            self.gatk_bedtointervallist(self.config.bedfile, dictfile, parents=[align.id]).gatk_collecthsmetrics(align.outs.bamout, 'interval_list', 'interval_list', parents=[self.p.id, align.id])
            self.gatk_collectinsertsizemetrics(align.outs.bamout, parents=[align.id])
            self.gatk_estimatelibrarycomplexity(align.outs.bamout, parents=[align.id])

            self.bamdst(self.config.bedfile, align.outs.bamout, parents=[align.id])
            self.mosdepth(align.outs.bamout, parents=[align.id])

        # if self.config.bedfile:
        #     self.bamdst('bamout', self.config.bedfile, parents=[self.getdep('samtools_markdup').id])
        # else:
        #     self.mosdepth('bamout')

