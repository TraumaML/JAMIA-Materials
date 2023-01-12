import wandb
from simpletransformers.ner import NERModel, NERArgs
import pandas as pd
import os


#os.environ["HTTPS_PROXY"] = "http://micc.tengbenet.cluster:18888"


# Get dataset
data = pd.read_pickle("annotation_data.pkl")

# Let's just go ahead and make sure this is actually random
data = data.sample(frac=1)

# Split into train and test
train = data.iloc[:int(0.7 * len(data))]
test = data.iloc[int(0.7 * len(data)):]



def main():
    # Specify labels
    # Hyperparameters and WandB.....

    wandb.init()
    config = wandb.config
    model_args = NERArgs()
    model_args.labels_list = list(set(data['labels']))
    model_args.use_early_stopping = True
    model_args.early_stopping_delta = 0.01
    model_args.early_stopping_metric = "mcc"
    model_args.early_stopping_metric_minimize = False
    model_args.early_stopping_patience = 5
    model_args.evaluate_during_training_steps = 1000
    model_args.overwrite_output_dir = True
    model_args.wandb_project = 'R21-Modeling'
    model_args.update_from_dict(config.__dict__['_items'])

    pprint(model_args)

    """
    model = NERModel('roberta', 'roberta-base',
                     args=model_args, use_cuda=True, cuda_device=1)
    # Train
    model.train_model(train)
    # Test
    result, model_outputs, preds_list = model.eval_model(test)
    metrics = {"f1_score": float(result['f1_score']),
               "precision": float(result["precision"]),
               "recall": float(result["recall"])}
    wandb.log(metrics)
    wandb.join()

    """
if __name__ == "__main__":
    main()
