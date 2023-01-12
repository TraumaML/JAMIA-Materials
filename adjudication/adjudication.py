"""
author: Bruce Atwood

date: 25 May 2022


This script is used for merging two BRAT annotation .ann files (referent to same .txt file) into one single one.

Entities that are wholly concordant are green as usual (the default in our BRAT .config file)
Entities that diverge in their attributes only are marked as yellow
Entities that differ in extent, including entities that exist in one .ann and not the other, are marked red. 
"""

from pathlib import Path
import click
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, Type, TypeVar
from abc import ABC, abstractmethod
import shutil
import os

T = TypeVar('T')

class Markable(ABC):

    @abstractmethod
    def mark(self, color):
        raise NotImplementedError

    @abstractmethod
    def base(self):
        raise NotImplementedError


@dataclass
class Entity(Markable):
    _: KW_ONLY
    entity_type: str
    text: str
    indexes: list[list[int]] # need multiple to account for sentence fragments
    marking: str = ""

    def mark(self: Type[T], color: str) -> T:
        self.marking = color
        return self

    def base(self: Type[T]) -> T:
        return self.__class__(entity_type=self.entity_type, text = self.text, indexes=self.indexes)


    def to_ann(self, tag_id: str):
        spans = ";".join([" ".join(span) for span in self.indexes])
        append = "_" + self.marking if self.marking else ""
        return tag_id + "\t" + self.entity_type + append + " " + spans + "\t" + self.text + "\n"



# ENTITY TYPES
@dataclass
class Event(Entity):
    entity_type: str = "Event"
    childhood_trauma: bool = False
    factuality: str = "Factual" # options: Factual|Maybe|Unlikely
    event_type: Optional[str] = None # options: Sexual|Physical|Emotional|Other

@dataclass
class Temporal_Frame(Entity):
    entity_type: str = "Temporal_Frame"
    temporal_type: Optional[str] = None # options: Age|Period|Time-of-Life|Event|Date

@dataclass
class Symptom(Entity):
    entity_type: str = "Symptom"
    negation: bool = False
    not_current_symptom: bool = False

@dataclass
class Perpetrator(Entity):
    entity_type: str = "Perpetrator"
    perpetrator_type: Optional[str] = None # options: Family-Member|Colleague|Partner|Other-Known|Other-Unknown

@dataclass
class Substance(Entity):
    entity_type: str = "Substance"

@dataclass
class Relation(Markable):
    arg1: Entity
    arg2: Entity
    relation_type: str
    marking: str = ""

    def mark(self, color):
        return self.__class__(self.arg1, self.arg2, self.relation_type, marking= color)

    def base(self):
        """
        super useful idk what ur talking about
        """
        return self


@dataclass
class Document:
    ann_entities: list = field(default_factory=dict) # starts as dict, turns into list
    ann_relations: list = field(default_factory=list)



def attribute2string(a: int, attribute_type: str ,tag_id: str, text: str="") -> str:
    text = " " + text if text else ""
    return "A" + str(a) + "\t" + attribute_type +" " + tag_id + text + "\n"




def revert_ann(doc: Document) -> list:
    """
    Converts Document back to .ann file
    """
    e = 0 # entity count
    a = 0 # attribute count
    r = 0 # relation count
    new_entity_mapping = []
    file = []

    for entity in doc.ann_entities:

        tag_id = "T"+ str(e)
        new_entity_mapping.append((tag_id, entity)) # entities mutable so can't use dict
        file.append(entity.to_ann(tag_id))
        e += 1 # increment entity count

        # Decompose Attributes
        match entity.entity_type:
            case "Event":
                # childhood_trauma
                if entity.childhood_trauma:
                    file.append(attribute2string(a, "Childhood_Trauma", tag_id))
                    a += 1 # increment attribute count (A1 -> A2 etc.)
                # factuality
                file.append(attribute2string(a, "Factuality",tag_id,entity.factuality))
                a+=1
                # event_type
                if entity.event_type:
                    file.append(attribute2string(a,"Event_Type",tag_id,entity.event_type))
                    a+=1

            case "Symptom":
                # not_current_symptom
                if entity.not_current_symptom:
                    file.append(attribute2string(a,"Not_Current_Symptom", tag_id))
                    a += 1

                # negation
                if entity.negation:
                    file.append(attribute2string(a,"Negation", tag_id))
                    a += 1

            case "Perpetrator":
                if entity.perpetrator_type:
                    file.append(attribute2string(a,"Perpetrator_Type", tag_id, entity.perpetrator_type))
                    a += 1
            case "Temporal_Frame":
                if entity.temporal_type:
                    file.append(attribute2string(a,"Temporal_Type",tag_id,entity.temporal_type))
                    a += 1


    for relation in doc.ann_relations:
        tag_id = "R" + str(r)

        for entity_id, entity in new_entity_mapping:
            if relation.arg1 == entity.base():
                arg1_id = entity_id
            if relation.arg2 == entity.base():
                arg2_id = entity_id

        append = "_" + relation.marking if relation.marking else ""

        file.append(tag_id + "\t" + relation.relation_type + append +" Arg1:" + arg1_id + " Arg2:" + arg2_id + "\n")
        r += 1 # increment relation count


    return file



def check_membership(objects: list[Markable], others: list[Markable], combined: list[Markable])-> list[Markable]:
    """
    checks all items in objects for membership in others.

    If member, adds to combined, but only when combined is not the one we're checking membership of (add variable)
        if check attributes is True, then it also checks the attributes of the entities as well, not just the base forms.
        marks them as yellow if only the attributes differ
    if not member, marks red, then adds to combined.
    """

    add = others != combined # calculate before combined is altered

    for obj in objects:
        assert isinstance(obj, Markable)
        shared = False

        for other in others:
            assert isinstance(other, Markable)

            if obj.base() == other.base():
                shared = True
                if add: # 1 and 3 pass this test
                    if obj == other: # 3 will always pass this test
                        combined.append(obj)
                    else:
                        combined.append(obj.mark("yellow")) # keeps attrs of doc1 when only attrs differ. Could change this to either never keep attrs or keep the one with with more attrs, doesn't really matter
                break
        if not shared:
            combined.append(obj.mark("red"))
    return combined


def merge_docs(doc1: Document, doc2: Document) -> Document:
    """
    Combines all entities
        marks yellow if their attributes differ, leaving some
        marks red if they are totally different

    Go through relations and find shared ones, marking non shared ones as red
    """

    # Merge Entities
    combined_entities = check_membership(doc1.ann_entities, doc2.ann_entities, []) # 1
    combined_entities = check_membership(doc2.ann_entities, combined_entities, combined_entities) # 2

    # Merge Relations
    combined_relations = check_membership(doc1.ann_relations, doc2.ann_relations, []) # 3
    combined_relations = check_membership(doc2.ann_relations, combined_relations, combined_relations) # 4

    return Document(combined_entities, combined_relations)



def convert_ann(file: list) -> Document:
    """
    Converts a brat annotation .ann file to a doc, which has two attributes:
        a dictionary of entitities, and a dictionary of relations.

    ann_file: .ann file read in as list
    """
    doc = Document()


    for line in file:

        tokens = line.split()

        if tokens[0][0] == "T": # Entity

            # Deal with sentence fragments
            this_id, rest, text = line.strip().split("\t")
            entity_type, *span = rest.split()
            indexes = [tuple(tmp.split()) for tmp in " ".join(span).split(";")]     # self explanatory

            match entity_type:

                case "Symptom":
                    entity = Symptom(text = text,indexes=indexes)

                case "Temporal_Frame":
                    entity = Temporal_Frame(text = text,indexes=indexes)

                case "Perpetrator":
                    entity = Perpetrator(text = text,indexes=indexes)

                case "Event":
                    entity = Event(text = text,indexes=indexes)

                case "Substance":
                    entity = Substance(text = text,indexes=indexes)

            doc.ann_entities[this_id] = entity



        elif tokens[0][0] == "A": # Attribute
            # If the line is an attribute, find the corresponding entity and update (marked by parent_id)
            parent_id = tokens[2]

            match tokens[1]:

                case "Perpetrator_Type":
                    doc.ann_entities[parent_id].perpetrator_type = tokens[3]

                case "Temporal_Type":
                    doc.ann_entities[parent_id].temporal_type = tokens[3]

                case "Event_Type":
                    doc.ann_entities[parent_id].event_type = tokens[3]

                case "Not_Current_Symptom":
                    doc.ann_entities[parent_id].not_current_symptom = True

                case "Childhood_Trauma":
                    doc.ann_entities[parent_id].childhood_trauma = True

                case "Negation":
                    try:
                        doc.ann_entities[parent_id].negation = True
                    except KeyError:
                        pass
                case "Factuality":
                    doc.ann_entities[parent_id].factuality = tokens[3]

        elif tokens[0][0] == "R": # Relation

            relation_type, arg1, arg2 = tokens[1::]
            arg1_id = arg1[5:]
            arg2_id = arg2[5:]
            doc.ann_relations.append(Relation(doc.ann_entities[arg1_id].base(), doc.ann_entities[arg2_id].base(), relation_type))


    doc.ann_entities = list(doc.ann_entities.values())

    return doc


def adjudicate(ann_file1: list, ann_file2: list) -> list:

    doc1 = convert_ann(ann_file1)
    doc2 = convert_ann(ann_file2)
    merged = merge_docs(doc1, doc2)
    return revert_ann(merged)


@click.command()
@click.argument('dir_path', type=click.Path(exists=True), required=True)
def main(dir_path):
    """
    dir_path is path to folder called EHR
    """
    dir_path = Path(dir_path)

    adjudicated = dir_path / "readjudicated"
    if not adjudicated.exists():
        os.mkdir(adjudicated)


    combined = []
    for annotator in ["Mei","Ann","Phil"]:
        combined += (dir_path/annotator).glob("*.ann")

    for index, file in enumerate(combined):


        for i in range(index+1, len(combined)):
            if combined[i].name == file.name:
                output_path = adjudicated/file.name

                with open(combined[i]) as f:
                    one = f.readlines()

                with open(file) as f:
                    two = f.readlines()

                output = adjudicate(two, one)

                with open(output_path, "w", encoding="utf8") as f:
                    for line in output:
                        f.write(line)

                try:
                    shutil.copy(file.with_suffix(".txt"), adjudicated)
                except:
                    shutil.copy(combined[i].with_suffix(".txt"), adjudicated)


if __name__ == '__main__':
    main()

