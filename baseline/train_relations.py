import pickle
from simpletransformers.classification import (
    ClassificationModel, ClassificationArgs
)
import pandas as pd

def train(trainfile):
    data = pd.read_pickle(trainfile)
    train = data.iloc[:int(0.7 * len(data))]
    test = data.iloc[int(0.7 * len(data)):]
    model_args = ClassificationArgs(num_train_epochs=10)
    model = ClassificationModel("roberta", "roberta-base", use_cuda=False)
    model.train_model(train, args=model_args)
    result, model_outputs, wrong_predictions = model.eval_model(test)
    print(result)


if __name__ == '__main__':
    train('relations.pkl')


