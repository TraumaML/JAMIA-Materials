import train
import wandb
import os

os.system("rd /s /q outputs runs")

if __name__ == "__main__":
    sweep_config = {
        "method": "bayes",  # grid, random
        "metric": {"name": "accuracy", "goal": "maximize"},
        "parameters": {
            "num_train_epochs": {"values": [10, 20, 30]},
            "learning_rate": {"min": 1e-5, "max": 4e-4},
        },
    }
    sweep_id = wandb.sweep(
        sweep_config, project="R21-Modeling", entity='r21_modeling')

    wandb.agent(sweep_id, train.main(sweep=True))
