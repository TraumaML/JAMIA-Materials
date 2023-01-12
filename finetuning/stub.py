import pandas as pd


def pickle2text(pickle, file):
    with open(file, "a", encoding="utf8") as f:
        text = list(pd.read_pickle(pickle)["note"])
        c= 0
        for note in text:
            f.write(note)
            c+=1
            # if c>50:
            #     break


if __name__ == "__main__":
    pickle2text("/Users/nlp/Desktop/notes.pickle", "/Users/nlp/Desktop/test.txt")