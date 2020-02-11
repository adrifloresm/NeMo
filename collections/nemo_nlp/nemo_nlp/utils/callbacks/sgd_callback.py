# Copyright (c) 2019 NVIDIA Corporation
__all__ = ['eval_iter_callback', 'eval_epochs_done_callback']

import collections
import numpy as np
import torch

from nemo.utils.exp_logging import get_logger
import nemo_nlp
from nemo_nlp.utils.metrics.sgd_metrics import *
import nemo_nlp.data.datasets.sgd.data_utils as data_utils
from fuzzywuzzy import fuzz

logger = get_logger('')

REQ_SLOT_THRESHOLD = 0.5
F1Scores = collections.namedtuple("F1Scores", ["f1", "precision", "recall"])

# Evaluation and other relevant metrics for DSTC8 Schema-guided DST.
# (1) Active intent accuracy.
ACTIVE_INTENT_ACCURACY = "active_intent_accuracy"
# (2) Slot tagging F1.
SLOT_TAGGING_F1 = "slot_tagging_f1"
SLOT_TAGGING_PRECISION = "slot_tagging_precision"
SLOT_TAGGING_RECALL = "slot_tagging_recall"
# (3) Requested slots F1.
REQUESTED_SLOTS_F1 = "requested_slots_f1"
REQUESTED_SLOTS_PRECISION = "requested_slots_precision"
REQUESTED_SLOTS_RECALL = "requested_slots_recall"
# (4) Average goal accuracy.
AVERAGE_GOAL_ACCURACY = "average_goal_accuracy"
AVERAGE_CAT_ACCURACY = "average_cat_accuracy"
AVERAGE_NONCAT_ACCURACY = "average_noncat_accuracy"
# (5) Joint goal accuracy.
JOINT_GOAL_ACCURACY = "joint_goal_accuracy"
JOINT_CAT_ACCURACY = "joint_cat_accuracy"
JOINT_NONCAT_ACCURACY = "joint_noncat_accuracy"

NAN_VAL = "NA"

def tensor2list(tensor):
    return tensor.detach().cpu().tolist()

def eval_iter_callback(tensors,

                       global_vars):
    # intents
    if 'intent_status' not in global_vars:
        global_vars['active_intent_labels'] = []
    if 'intent_status' not in global_vars:
        global_vars['active_intent_preds'] = []

    # requested slots
    if 'requested_slot_status' not in global_vars:
        global_vars['requested_slot_status'] = []
    if 'req_slot_predictions' not in global_vars:
        global_vars['req_slot_predictions'] = []

    # categorical slots
    if 'cat_slot_correctness' not in global_vars:
        global_vars['cat_slot_correctness'] = []

    # noncategorical slots
    if 'noncat_slot_correctness' not in global_vars:
        global_vars['noncat_slot_correctness'] = []

    if 'joint_noncat_accuracy' not in global_vars:
        global_vars['joint_noncat_accuracy'] = []
    if 'joint_cat_accuracy' not in global_vars:
        global_vars['joint_cat_accuracy'] = []

    for kv, v in tensors.items():
        # intents
        if kv.startswith('logit_intent_status'):
            logit_intent_status = v[0]
        elif kv.startswith('intent_status'):
            intent_status = v[0]

        # requested slots
        elif kv.startswith('logit_req_slot_status'):
            logit_req_slot_status = v[0]
        elif kv.startswith('requested_slot_status'):
            requested_slot_status = v[0]
        elif kv.startswith('req_slot_mask'):
            requested_slot_mask = v[0]

        # categorical slots
        elif kv.startswith('logit_cat_slot_status'):
            logit_cat_slot_status = v[0]
        elif kv.startswith('logit_cat_slot_value'):
            logit_cat_slot_value = v[0]
        elif kv.startswith('categorical_slot_status'):
            categorical_slot_status = v[0]
        elif kv.startswith('num_categorical_slots'):
            num_categorical_slots = v[0]
        elif kv.startswith('categorical_slot_values'):
            categorical_slot_values= v[0]
        elif kv.startswith('cat_slot_values_mask'):
            cat_slot_values_mask= v[0]

        # noncategorical slots
        elif kv.startswith('logit_noncat_slot_status'):
            logit_noncat_slot_status = v[0]
        elif kv.startswith('logit_noncat_slot_start'):
            logit_noncat_slot_start = v[0]
        elif kv.startswith('logit_noncat_slot_end'):
            logit_noncat_slot_end = v[0]
        elif kv.startswith('noncategorical_slot_status'):
            noncategorical_slot_status = v[0]
        elif kv.startswith('num_noncategorical_slots'):
            num_noncategorical_slots = v[0]
        elif kv.startswith('noncategorical_slot_value_start'):
            noncategorical_slot_value_start = v[0]
        elif kv.startswith('noncategorical_slot_value_end'):
            noncategorical_slot_value_end = v[0]

        elif kv.startswith('user_utterance'):
            user_utterances = v[0]

    num_active_intents = torch.sum(intent_status, axis=1).unsqueeze(1)

    # the intents represented as a one hot vectors
    # logits shape [batch, max_num_intents + 1] where 1 is for NONE intent

    active_intent_onehot_labels = intent_status[num_active_intents.view(-1) > 0.5]
    # get indices of active intents and add 1 to take into account NONE intent
    active_intent_labels = active_intent_onehot_labels.max(dim=1)[1] + 1

    active_intent_preds = torch.argmax(logit_intent_status, 1)[num_active_intents.view(-1) > 0.5]

    global_vars['active_intent_labels'].extend(tensor2list(active_intent_labels))
    global_vars['active_intent_preds'].extend(tensor2list(active_intent_preds))

    '''
    num_active_intents = torch.sum(intent_status, axis=1).unsqueeze(1)
    tensor_ones = torch.ones(num_active_intents.size(), dtype=torch.long)
 
    if num_active_intents.is_cuda:
        tensor_ones = tensor_ones.cuda()
 
    # adding label for NONE intent - 1 if no acive intent for the dialogue
    none_intent_label = tensor_ones - num_active_intents
    onehot_intent_labels = torch.cat([none_intent_label, intent_status], axis=1)
    _, intent_labels = onehot_intent_labels.max(dim=1)

    '''

    # # mask example with no noncategorical slots
    # noncat_slots_mask = torch.sum(noncategorical_slot_status, 1) > 0

    # get req slots predictions
    req_slot_predictions = torch.nn.Sigmoid()(logit_req_slot_status)
    # mask examples with padded slots
    req_slot_predictions = req_slot_predictions.view(-1)[requested_slot_mask]
    requested_slot_status = requested_slot_status.view(-1)[requested_slot_mask]

    ones = req_slot_predictions.new_ones(req_slot_predictions.size())
    zeros = req_slot_predictions.new_zeros(req_slot_predictions.size())
    req_slot_predictions = torch.where(req_slot_predictions > REQ_SLOT_THRESHOLD, ones, zeros)

    global_vars['req_slot_predictions'].extend(tensor2list(req_slot_predictions))
    global_vars['requested_slot_status'].extend(tensor2list(requested_slot_status))

    
    # point_outputs_max = torch.argmax(point_outputs, dim=-1)
    # mask_paddings = (tgt_ids == data_desc.vocab.pad_id)
    # comp_res = ((point_outputs_max == tgt_ids) | mask_paddings)
    # comp_res = torch.all(comp_res, axis=-1, keepdims=False)

    # global_vars['comp_res'].extend(comp_res.cpu().numpy())
    # global_vars['gating_preds'].extend(torch.argmax(gate_outputs, axis=-1).cpu().numpy())

    # list of corectness scores, each corresponding to one slot in the
    # service. The score is a float either 0.0 or 1.0 for categorical slot,
    # and in range [0.0, 1.0] for non-categorical slot.
    


    # Categorical slots
    # mask unused slots for the service
    max_num_cat_slots = categorical_slot_status.size()[-1]
    max_num_slots_matrix = torch.arange(0, max_num_cat_slots, 1).to(num_categorical_slots.device)
    cat_slot_status_mask = max_num_slots_matrix  < torch.unsqueeze(num_categorical_slots, dim=-1)

    cat_slot_status_preds = torch.argmax(logit_cat_slot_status, -1)[cat_slot_status_mask]
    cat_slot_values_preds = torch.argmax(logit_cat_slot_value, -1)[cat_slot_status_mask]
    cat_slot_status_labels = categorical_slot_status[cat_slot_status_mask]
    cat_slot_values_labels = categorical_slot_values[cat_slot_status_mask]

    # determine if the slot status was predicted correctly
    correct_cat_slot_status_mask = cat_slot_status_labels == cat_slot_status_preds

    # evaluate cat slot prediction only if slot is active
    # if predicted slot status = 0,2 (off/doncare) but the true status is 1 (active) => categorical correctness
    # for such example is 0
    active_cat_slot_status_correctness = correct_cat_slot_status_mask * (cat_slot_status_labels == data_utils.STATUS_ACTIVE)
    cat_slot_values_correctness = (cat_slot_values_labels == cat_slot_values_preds).type(torch.int)

    cat_slot_correctness = torch.where(active_cat_slot_status_correctness, cat_slot_values_correctness, correct_cat_slot_status_mask.type(torch.int))
    global_vars['cat_slot_correctness'].extend(tensor2list(cat_slot_correctness))

    # check that num noncategorical slots is the same across the batch
    if not (num_categorical_slots.shape[0] * num_categorical_slots[0] == sum(num_categorical_slots)):
        raise ValueError(f'num_categorical_slots is not the same across the batch.' +
                          'The joint accuracy would be computed incorrectly.')

    joint_cat_accuracy = torch.prod(cat_slot_correctness.view(-1,num_categorical_slots[0]), -1)
    global_vars['joint_cat_accuracy'].extend(tensor2list(joint_cat_accuracy))


    # Noncategorical slots
    max_num_noncat_slots = noncategorical_slot_status.size()[-1]
    max_num_noncat_slots_matrix = torch.arange(0, max_num_noncat_slots, 1).to(num_noncategorical_slots.device)
    noncat_slot_status_mask = max_num_noncat_slots_matrix  < torch.unsqueeze(num_noncategorical_slots, dim=-1)

    noncat_slot_status_preds = torch.argmax(logit_noncat_slot_status, -1)[noncat_slot_status_mask]
    noncat_slot_value_start_preds = torch.argmax(logit_noncat_slot_start, -1)[noncat_slot_status_mask]
    noncat_slot_value_end_preds = torch.argmax(logit_noncat_slot_end, -1)[noncat_slot_status_mask]

    noncat_slot_status_labels = noncategorical_slot_status[noncat_slot_status_mask]
    noncat_slot_value_start_labels = noncategorical_slot_value_start[noncat_slot_status_mask]
    noncat_slot_value_end_labels = noncategorical_slot_value_end[noncat_slot_status_mask]

    correct_noncat_slot_status_mask = noncat_slot_status_labels == noncat_slot_status_preds
    active_noncat_slot_status_correctness = correct_noncat_slot_status_mask * (noncat_slot_status_labels == data_utils.STATUS_ACTIVE)
    
    # # calculate number of correct predictions
    # nonactive_noncat_slot_status_correctness = correct_noncat_slot_status_mask * (noncat_slot_status_labels != data_utils.STATUS_ACTIVE)
    # nonactive_noncat_slot_status_correctness = sum(nonactive_noncat_slot_status_correctness.type(torch.int))

    # find indices of noncat slots for which predicted status was correctly predicted and is ACTIVE
    inds_with_correct_active_noncat_slot_status = active_noncat_slot_status_correctness.type(torch.int).nonzero()

    # check that num noncategorical slots is the same across the batch
    if not (num_noncategorical_slots.shape[0] * num_noncategorical_slots[0] == sum(num_noncategorical_slots)):
        raise ValueError(f'num_noncategorical_slots is not the same across the batch. The fuzzy would not be computed correctly.')
    import pdb; pdb.set_trace()
    noncat_slot_correctness = get_noncat_slot_value_match(user_utterances,
                                                          inds_with_correct_active_noncat_slot_status,
                                                          noncat_slot_value_start_labels,
                                                          noncat_slot_value_end_labels,
                                                          noncat_slot_value_start_preds,
                                                          noncat_slot_value_end_preds,
                                                          num_noncategorical_slots[0])

    global_vars['noncat_slot_correctness'].extend(noncat_slot_correctness)

    joint_noncat_accuracy = torch.prod(noncat_slot_correctness.view(-1,num_noncategorical_slots[0]), -1)
    global_vars['joint_noncat_accuracy'].extend(tensor2list(joint_noncat_accuracy))

def fuzzy_string_match(str_label, str_preds):
    """Returns fuzzy string similarity score in range [0.0, 1.0]."""

    # The higher the score, the higher the similarity between the two strings.
    return fuzz.token_sort_ratio(str_label, str_preds) / 100.0


def get_noncat_slot_value_match(user_utterances,
                            indices,
                            noncat_slot_value_start_labels,
                            noncat_slot_value_end_labels,
                            noncat_slot_value_start_preds,
                            noncat_slot_value_end_preds,
                            num_noncategorical_slots):
    """Calculate non-categorical slots correctness.

    Args:
      str_ref_list: a list of reference strings.
      str_hyp: the hypothesis string.

    Returns:
    score: The highest fuzzy string match score of the references and hypotheis.
    """
    noncat_slot_correctness = []
    # user_utterance_ind = indices / 
    for ind in indices:
        import pdb; pdb.set_trace()
        user_utterance = user_utterances[indices / num_noncategorical_slots]
        str_label = user_utterance[noncat_slot_value_start_labels[ind] : noncat_slot_value_end_labels[ind]]
        str_preds = user_utterance[noncat_slot_value_start_preds[ind] : noncat_slot_value_end_preds[ind]]
        noncat_slot_correctness.append(max(0, fuzzy_string_match(str_label, str_preds)))
    
    return noncat_slot_correctness


def eval_epochs_done_callback(global_vars):
    active_intent_labels = np.asarray(global_vars['active_intent_labels'])
    active_intent_preds = np.asarray(global_vars['active_intent_preds'])

    active_intent_accuracy = sum(active_intent_labels == active_intent_preds) / len(active_intent_labels)

    req_slot_predictions = np.asarray(global_vars['req_slot_predictions'], dtype=int)
    requested_slot_status = np.asarray(global_vars['requested_slot_status'], dtype=int)
    req_slot_metrics = compute_f1(req_slot_predictions, requested_slot_status)

    correctness_cat_slots = np.asarray(global_vars['cat_slot_correctness'], dtype=int)
    # joint_acc, turn_acc = \
    #     evaluate_metrics(global_vars['comp_res'],
    #                      global_vars['gating_labels'],
    #                      global_vars['gating_preds'],
    #                      data_desc.gating_dict["ptr"])

    # gating_comp_flatten = (np.asarray(global_vars['gating_labels']) == np.asarray(global_vars['gating_preds'])).ravel()
    # gating_acc = np.sum(gating_comp_flatten) / len(gating_comp_flatten)
    
    cat_slot_correctness = np.asarray(global_vars['cat_slot_correctness'])
    noncat_slot_correctness = np.asarray(global_vars['noncat_slot_correctness'])

    average_cat_accuracy = np.mean(cat_slot_correctness)
    average_noncat_accuracy = np.mean(noncat_slot_correctness)
    average_goal_accuracy = np.mean(np.concatenate((cat_slot_correctness, noncat_slot_correctness)))

    metrics = {'all_services':
        {
        # Active intent accuracy
        "active_intent_accuracy": active_intent_accuracy,
        "average_cat_accuracy": average_cat_accuracy,
        "average_goal_accuracy": average_goal_accuracy,
        "average_noncat_accuracy": average_noncat_accuracy,
        # "joint_cat_accuracy": 0.7009794862317501,
        # "joint_goal_accuracy": 0.4904726693494299,
        # "joint_noncat_accuracy": 0.6226867035546613,

        # Slot tagging F1
        "requested_slots_f1": req_slot_metrics.f1,
        "requested_slots_precision": req_slot_metrics.precision,
        "requested_slots_recall": req_slot_metrics.recall,

        # Average goal accuracy

            }
        }
    print(metrics)



    # active_intent_acc = metrics.get_active_intent_accuracy(
    #         frame_ref, frame_hyp)
    # slot_tagging_f1_scores = metrics.get_slot_tagging_f1(
    #     frame_ref, frame_hyp, turn_ref["utterance"], service)
    # requested_slots_f1_scores = metrics.get_requested_slots_f1(
    #     frame_ref, frame_hyp)
    # goal_accuracy_dict = metrics.get_average_and_joint_goal_accuracy(
    #     frame_ref, frame_hyp, service)

    return metrics


def get_average_and_joint_goal_accuracy(frame_ref, frame_hyp, service):
  """Get average and joint goal accuracies of a frame.

  Args:
    frame_ref: single semantic frame from reference (ground truth) file.
    frame_hyp: single semantic frame from hypothesis (prediction) file.
    service: a service data structure in the schema. We use it to obtain the
      list of slots in the service and infer whether a slot is categorical.

  Returns:
    goal_acc: a dict whose values are average / joint
        all-goal / categorical-goal / non-categorical-goal accuracies.
  """
  goal_acc = {}

  list_acc, slot_active, slot_cat = compare_slot_values(
      frame_ref["state"]["slot_values"], frame_hyp["state"]["slot_values"],
      service)

  # (4) Average goal accuracy.
  active_acc = [acc for acc, active in zip(list_acc, slot_active) if active]
  goal_acc[AVERAGE_GOAL_ACCURACY] = np.mean(
      active_acc) if active_acc else NAN_VAL
  # (4-a) categorical.
  active_cat_acc = [
      acc for acc, active, cat in zip(list_acc, slot_active, slot_cat)
      if active and cat
  ]
  goal_acc[AVERAGE_CAT_ACCURACY] = (
      np.mean(active_cat_acc) if active_cat_acc else NAN_VAL)
  # (4-b) non-categorical.
  active_noncat_acc = [
      acc for acc, active, cat in zip(list_acc, slot_active, slot_cat)
      if active and not cat
  ]
  goal_acc[AVERAGE_NONCAT_ACCURACY] = (
      np.mean(active_noncat_acc) if active_noncat_acc else NAN_VAL)

  # (5) Joint goal accuracy.
  goal_acc[JOINT_GOAL_ACCURACY] = np.prod(list_acc) if list_acc else NAN_VAL
  # (5-a) categorical.
  cat_acc = [acc for acc, cat in zip(list_acc, slot_cat) if cat]
  goal_acc[JOINT_CAT_ACCURACY] = np.prod(cat_acc) if cat_acc else NAN_VAL
  # (5-b) non-categorical.
  noncat_acc = [acc for acc, cat in zip(list_acc, slot_cat) if not cat]
  goal_acc[JOINT_NONCAT_ACCURACY] = np.prod(
      noncat_acc) if noncat_acc else NAN_VAL

  return goal_acc


F1Scores = collections.namedtuple("F1Scores", ["f1", "precision", "recall"])

def compute_f1(predictions, labels):
  """Compute F1 score from labels (grouth truth) and predictions.

  Args:
    predictions: numpy array of predictions
    labels: numpy array of labels

  Returns:
    A F1Scores object containing F1, precision, and recall scores.
  """
  true = sum(labels)
  positive = sum(predictions)
  true_positive = sum(predictions&labels)

  precision = float(true_positive) / positive if positive else 1.0
  recall = float(true_positive) / true if true else 1.0
  if precision + recall > 0.0:
    f1 = 2.0 * precision * recall / (precision + recall)
  else:  # The F1-score is defined to be 0 if both precision and recall are 0.
    f1 = 0.0

  return F1Scores(f1=f1, precision=precision, recall=recall)