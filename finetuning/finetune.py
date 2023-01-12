from simpletransformers.language_modeling.language_modeling_model import LanguageModelingModel
import logging


logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

train_args = {
    "reprocess_input_data": True,
    "overwrite_output_dir": True,
    "num_train_epochs": 5
}

model = LanguageModelingModel('roberta', 'roberta-base', args=train_args, use_cuda=True)

model.train_model("data/train.txt", eval_file="data/text.txt")

#model.eval_model("data/test.txt") fuck evaluation

