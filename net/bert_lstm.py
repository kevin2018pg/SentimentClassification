# -*- coding: utf-8 -*-
# @Time    : 2020/4/4 17:16
# @Author  : Kevin
# @File    : bert_lstm.py
# @Version : python 3.6
# @Desc    :
from transformers import BertPreTrainedModel, BertModel
from torch import nn
import torch
from torch.nn import CrossEntropyLoss, MSELoss
from net.utils.focal_loss import FocalLoss


# 旧版transformers
# from transformers.modeling_bert import BertLayerNorm, BertEmbeddings, BertEncoder, BertPooler
# 新版transformers
# from transformers.models.bert.modeling_bert import *

class BertForSequenceClassificationLSTM(BertPreTrainedModel):
    def __init__(self, config, args):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.args = args
        config.output_hidden_states = True
        self.bert = BertModel(config)
        self.lstm = nn.LSTM(config.hidden_size,
                            config.hidden_size,
                            num_layers=1,
                            bias=True,
                            batch_first=True,
                            dropout=config.hidden_dropout_prob,
                            bidirectional=True)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.nums = 5
        hidden_size_changed = config.hidden_size * self.nums
        self.pooler = nn.Sequential(
            nn.Linear(hidden_size_changed, config.hidden_size),
            nn.Tanh()
        )
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        # if args.fl_gamma:
        #     self.label_focal_loss = FocalLoss(num_class=config.num_labels,
        #                                    gamma=args.fl_gamma)
        self.label_focal_loss = FocalLoss(num_class=config.num_labels,
                                          gamma=1)
        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            original_logits=None,
    ):
        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
        )
        pooled_output = outputs[1]
        # pooled_output = self.dropout(pooled_output)
        hidden_output = outputs[2][-1]
        sequences_lengths = torch.sum(attention_mask, dim=-1)
        sorted_batch, sorted_lengths, _, restoration_idx = \
            sort_by_seq_lens(hidden_output, sequences_lengths)
        packed_batch = nn.utils.rnn.pack_padded_sequence(sorted_batch,
                                                         sorted_lengths,
                                                         batch_first=True)

        lstm_outputs, _ = self.lstm(packed_batch, None)
        lstm_outputs, _ = nn.utils.rnn.pad_packed_sequence(lstm_outputs,
                                                           batch_first=True)
        reordered_outputs = lstm_outputs.index_select(0, restoration_idx)

        last_mean = torch.mean(reordered_outputs, dim=1)
        last_max, _ = torch.max(reordered_outputs, dim=1)
        last_cat = torch.cat((pooled_output, last_max, last_mean), dim=-1)
        last_cat = torch.squeeze(last_cat)
        pooled_output = self.pooler(last_cat)
        logits = self.classifier(pooled_output)

        outputs = (logits,) + outputs[2:]  # add hidden states and attention if they are here

        if labels is not None:
            if self.num_labels == 1:
                #  We are doing regression
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1), labels.view(-1))
            else:
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
                # loss = self.label_focal_loss(logits.view(-1, self.num_labels), labels.view(-1))
                probs = torch.nn.functional.softmax(logits.view(-1, self.num_labels), dim=-1)
                # loss +=  -2e-2 * torch.sum(probs * torch.log(probs))
                # loss += -3e-2 * torch.norm(probs, 'nuc')
            if original_logits is not None:
                loss = torch.nn.functional.kl_div(
                    torch.nn.functional.softmax(original_logits.view(-1, self.num_labels), dim=-1),
                    torch.nn.functional.softmax(logits.view(-1, self.num_labels), dim=-1),
                    reduction='mean'
                )
                loss = 0.5 * loss
            outputs = (loss,) + outputs
        return outputs  # (loss), logits, (hidden_states), (attentions)


def sort_by_seq_lens(batch, sequences_lengths, descending=True):
    """
    Sort a batch of padded variable length sequences by their length.

    Args:
        batch: A batch of padded variable length sequences. The batch should
            have the dimensions (batch_size x max_sequence_length x *).
        sequences_lengths: A tensor containing the lengths of the sequences in the
            input batch. The tensor should be of size (batch_size).
        descending: A boolean value indicating whether to sort the sequences
            by their lengths in descending order. Defaults to True.

    Returns:
        sorted_batch: A tensor containing the input batch reordered by
            sequences lengths.
        sorted_seq_lens: A tensor containing the sorted lengths of the
            sequences in the input batch.
        sorting_idx: A tensor containing the indices used to permute the input
            batch in order to get 'sorted_batch'.
        restoration_idx: A tensor containing the indices that can be used to
            restore the order of the sequences in 'sorted_batch' so that it
            matches the input batch.
    """
    sorted_seq_lens, sorting_index = \
        sequences_lengths.sort(0, descending=descending)

    sorted_batch = batch.index_select(0, sorting_index)

    idx_range = \
        sequences_lengths.new_tensor(torch.arange(0, len(sequences_lengths)))
    _, reverse_mapping = sorting_index.sort(0, descending=False)
    restoration_index = idx_range.index_select(0, reverse_mapping)

    return sorted_batch, sorted_seq_lens, sorting_index, restoration_index
