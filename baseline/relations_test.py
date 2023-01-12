
from relations2int import mapping
from simpletransformers.classification import (
    ClassificationModel, ClassificationArgs
)
import pandas as pd
from pprint import pprint
from sklearn.metrics import *

def f1(true,pred):
    return f1_score(true,pred,average="macro")
def recall(true,pred):
    return recall_score(true,pred,average="macro")
def precision(true,pred):
    return precision_score(true,pred,average="macro")


def train(trainfile):
    data = pd.read_pickle(trainfile)
    data["labels"] = [mapping[label] for label in data["labels"]]
    data = data.sample(frac=1)
    training_set = data.iloc[:int(0.7 * len(data))]
    test = data.iloc[int(0.7 * len(data)):]
    model_args = ClassificationArgs(num_train_epochs=15, learning_rate= .00004844, train_batch_size=32, use_multiprocessing=False, use_multiprocessing_for_evaluation=False)
    model_args.labels_list = list(set(data['labels']))
    model_args.use_early_stopping = True
    model_args.early_stopping_delta = 0.01
    model_args.early_stopping_metric = "mcc"
    model_args.early_stopping_metric_minimize = False
    model_args.early_stopping_patience = 5
    model_args.evaluate_during_training_steps = 1000
    model_args.overwrite_output_dir = True

    model = ClassificationModel("roberta", "roberta-base", use_cuda=True,cuda_device=1,args=model_args, num_labels=len(set([lab for lab in data['labels']])))
    model.train_model(training_set)
    result, model_outputs, wrong_predictions = model.eval_model(test, f1_score= f1, recall = recall, precision=precision)
    pprint(result, width=1)

if __name__ == '__main__':
    train('/data/batwood/R21-Modeling/relations_basic.pkl')
    #train('/data/batwood/R21-Modeling/relations.pkl')

