import pymongo
import pandas as pd
import spacy
from tqdm import tqdm
from collections import defaultdict
from itertools import combinations, product, zip_longest
import pickle
from pprint import pprint 

nlp = spacy.load('en_core_web_sm')
client = pymongo.MongoClient("localhost", 27017)
db = client.r21
documents = db["documents"]

# Build a ML-ready DF for a single document, with columns representing tokens, the token position, and their associated labels
def spans(doc, simple=True):
    tokens = nlp(doc["text"])  # Extract tokens
    sents = tokens.sents
    with tokens.retokenize() as retokenizer:
        for index, tok in enumerate(tokens):  # treat special cases (deidentified) as single tokens
            if tok.text == "<" and tokens[index + 2].text == ">":
                retokenizer.merge(tokens[index:index + 3])
            elif tok.text == "<" and tokens[index + 3].text == ">" and tokens[index + 2].text == "number":
                retokenizer.merge(tokens[index:index + 4])

    df = pd.DataFrame({"token": [tok.text for tok in tokens],
                        "sentence_id": [i for i,s in enumerate(sents) for _ in range(len(s))],
                        "entity_id": [None for _ in tokens],
                       "position": [int(tok.idx) for tok in tokens],
                       "labels": ["O" for _ in tokens]})
    for entity_id, entity in doc['ann_entities'].items():
        try:
            entity_span = entity["indexes"]  # [['5606','5620']]
        except:
            pprint(entity)
            raise ValueError
        entity_type = entity["entity_type"]

        if not simple: # Otherwise add attributes to entities
            if entity_type == 'symptom':
                if entity['negation']:
                    entity_type += '+neg'
                if entity['not_current_symptom']:
                    entity_type += '+not_current_symptom'
            elif entity_type == 'temporal_frame':
                try:
                    entity_type += '_' + entity['temporal_type']
                except TypeError:
                    pass
            elif entity_type == 'event':
                try:
                    entity_type += '_' + entity['event_type']
                except TypeError:
                    pass
                if entity['childhood_trauma']:
                    entity_type += '+childhood'
            elif entity_type == 'perpetrator':
                try:
                    entity_type += '_' + entity['perpetrator_type']
                except TypeError:
                    pass
        for span in entity_span:

            for index in df.index:  # iterate through df rows

                if df.loc[index, "position"] == int(span[0]):
                    k = 0
                    nrows = df.shape[0]
                    while k <= nrows and df.loc[index + k, "position"] < int(span[1]):
                        df.at[index + k, "labels"] = entity_type
                        df.at[index+k, "entity_id"] = entity_id
                        k += 1
    return df


def simplify_label(label: str) -> str:
    """
    takes a label and returns base entity
    """
    label = label.split("+")[0]
    label = label.split("_")[0]
    if label == "temporal":
        label = "temporal_frame"
    return label


def relation_combination(sentence_text, entities):
    types = defaultdict(list)
    if len(entities) < 2: 
        return pd.DataFrame([], columns=["e1","e2","sentence_text"])

    for entity_id, label in entities: # sort entities base on type
        types[label].append(entity_id)

    perpetrated_by = list(product(types["event"], types["perpetrator"]))
    subevents = product(types['event'], types["event"])
    subevents = [(a,b) for a,b in subevents if a != b]
    grounded_to = list(product(types["event"], types["temporal_frame"]))  # updated annotation guidelines only uses events

    relations = perpetrated_by + subevents + grounded_to
    relations = [(a,b,str(sentence_text)) for a,b in relations]
    return pd.DataFrame(relations, columns = ["e1","e2","sentence_text"])




def build_relation_df(span_df: pd.DataFrame, doc):
    sentence_entities = defaultdict(set) # key is sentence ID, val is list of entities in that sentence
    relation_df = pd.DataFrame([], columns=["e1","e2"])
    sents = list(nlp(doc["text"]).sents)
    for _, row in span_df.iterrows(): #iterating by token
        if row["entity_id"]:
            # for each sentence, make a list of all the entities with their ids and types
            sentence_entities[sents[row["sentence_id"]]].add((row["entity_id"], simplify_label(row["labels"])))

    # build out relation_df by sentence
    for sentence_text, entities in sentence_entities.items():
        df = relation_combination(sentence_text,entities) # all possible relations for this sentence
        relation_df = pd.concat([relation_df, df], ignore_index=True)

    # Make dict of true relations mapping to their relation type
    true_relations = {}
    for _,relation in doc["ann_relations"].items():
        true_relations[(relation["arg1_id"],relation["arg2_id"])] = relation["relation_type"]

    # add labels 
    labels = []
    for _, row in relation_df.iterrows():
        labels.append(true_relations.get((row["e1"], row["e2"]), "no_relation"))
    relation_df["labels"] = labels

    relation_df["e1"] = [doc["ann_entities"][e]["text"] for e in relation_df["e1"]]
    relation_df["e2"] = [doc["ann_entities"][e]["text"] for e in relation_df["e2"]]

    return relation_df

# Not currently using, since we don't really need BIO encoding
def BIO_labels(labels):
    prev = None
    for i, l in enumerate(labels): 
        if l != 'O':
            if prev == l:
                labels[i] = 'I-' + l
            else:
                labels[i] = 'B-' + l
        prev = l
    return labels


# Make sentence IDs collection level, rather than document level
def build_df(df_spans):
    kounter = 0
    prev = 0
    for index, row in df_spans.iterrows():
        current = df_spans.loc[index,"sentence_id"]
        if current != prev:
            prev = current
            kounter += 1
        df_spans.loc[index,"sentence_id"] = kounter
    return df_spans

# Processes a single document (useful for testing)
def singleton():
    doc = documents.find_one()
    spans_df = spans(doc, simple=False)
    return build_df(spans_df), build_relation_df(spans_df,doc)


def full_dataset():
    combined_spans = pd.DataFrame()
    combined_relations = pd.DataFrame()
    for doc in tqdm(documents.find(), total=documents.count_documents({}), desc="Ingesting Documents"):
        spans_df = spans(doc, simple=True)
        relations_df = build_relation_df(spans_df,doc)
        combined_relations = pd.concat([combined_relations,relations_df], ignore_index=True)
        combined_spans = pd.concat([combined_spans, spans_df], ignore_index=True)
    return build_df(combined_spans), combined_relations



if __name__ == "__main__":
    spans, relations = full_dataset()
    spans.to_pickle("spans.pkl")

    # relations.to_pickle("relations.pkl")

    # entities = {("T1","event"), ("T2","event"), ("T3","event"), ("T4","event"),("T5","perpetrator")}
    # df = relation_combination("Says she is used to be the one who is being kicked--is being emotionally abused by family.", entities)
