## SentimentClassification
TextSentimentClassification（文本分类任务）
### Task

* 以roberta，chinese-roberta_wwm_ext,chinese-roberta-wwm-ext-large,uer提供的mixed模型为预训练基础，在上面进行模型的微调，之后根据任务的特点进行改进，最后对多个模型进行投票集成。

### Introduction

* data：该目录下放置了模型的训练数据，未进行train、dev的划分，模型训练过程中会在程序中划分，eval为验证数据。
* net：该目录下放置做了fine-tuning的model.py 文件，如bert_bilstm_attention、bert_transfer_learning等。
* pretrained_model：该目录下放置了fine-tuning的预训练模型，可以clone仓库或自行导入。
* submission：该目录会在程序运行后生成，目录下存放着各个模型的模型文件和验证集测试集的oof结果。
* process_data.py：该文件负责将给出的数据进行清洗。
* k_fold_bert_variants_model.py：该文件下包括了Processor类，Dataset类等，负责对数据的处理。convert_example_to_features函数，将文本数据转化为模型的输入特征。
* model_train_and_eval.py：该文件下包括了模型的train、evaluate、test函数，用于对模型的训练和测试。
* utils.py：该文件下包括了模型的collate函数、set_logger函数，用于Dataset加载时格式的转化、设置日志等。
* macro_weight.py：该文件负责测试usual_k_fold_model 下所有模型的k折结果性能。
* voting.py：该文件负责将usual_k_fold_model 下的结果进行投票集成，并输出在dev下的结果。（投票方法为模型输出的prob概率值的均值）
* run_test.sh：该文件是执行入口脚本，可进行参数调整修改。

### How to run ?

* 运行 run_test.sh 显存不足需要调整batch size，本队训练过程中均通过软batch将size设置为64，随机种子也已经固定。
* 运行 voting.py 会根据目录下各个模型的oof文件进行投票集成，并生成最终的结果。

### Download Pretrained models

* [chinese-roberta_wwm_ext](https://huggingface.co/hfl/chinese-roberta-wwm-ext)
* [roberta](https://huggingface.co/models) 
* [uer_mixed_large](https://github.com/dbiir/UER-py) 

### Contact

* kevin2018pg@163.com
