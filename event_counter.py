




def event_counter(documents):
    event_counter = Counter()
    for document in documents.find():
        for _,entity in document["ann_entities"].items():
            if entity["entity_type"] == "event":
                event_counter[entity["event_type"]] += 1
    pprint(event_counter)