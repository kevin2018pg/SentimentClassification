## 用于存放做fine-tuning的预训练模型
### 使用
[chinese-roberta-wwm-ext-large](https://huggingface.co/hfl/chinese-roberta-wwm-ext-large)
```
## 1 import
from transformers import AutoTokenizer, AutoModelForMaskedLM
  
tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext-large")

model = AutoModelForMaskedLM.from_pretrained("hfl/chinese-roberta-wwm-ext-large")


## 2 clone the model repo

git lfs install
git clone https://huggingface.co/hfl/chinese-roberta-wwm-ext-large
# if you want to clone without large files – just their pointers
# prepend your git clone with the following env var:
GIT_LFS_SKIP_SMUDGE=1
```

[chinese-roberta-wwm-ext](https://huggingface.co/hfl/chinese-roberta-wwm-ext)
```
...
```
