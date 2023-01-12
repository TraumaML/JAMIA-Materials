import spacy
import scispacy

import pandas as pd
import random

nlp = spacy.load('en_core_web_sm')
sci_nlp = spacy.load("en_core_sci_sm")

pickle_file = "/Users/nlp/Desktop/notes.pickle"


text = "23 year old female with a h/o polysubstance abuse, anxiety and depression NOS with 1 prior Bourne wood hospital admission 3 weeks ago for a drug overdose and potential parasuicidal behavior in that context. Patient was brought in by her boyfriend for a psychiatric evaluation. Patient reports that since her mis- \
    carriage 6 months ago she has found that she relapsed on drugs. Specifically she has relapsed on cocaine, benzodiazepines and opiates (IV heroine). Patient is evasive at times in the interview and of note, per collateral information from \
    her boyfriend James who accompanied the patient, patient self presented seeking inpatient psychiatric care but after learning that she could not smoke in the emergency room had become more interested in potentially leave the ED."

text2 = " You will be given medication for HIV prophylaxis (truvada and kaletra) for the next 3 days. The infectious \
disease doctors will call you tomorrow for follow-up, and the infectious disease \
clinic number is below--you will need to call this for follow-up within the next \
4-5d: 617.726.2748. Return to the ER for fevers, abdominal pain, fainting, or other concerns."
doc = sci_nlp(text)
doc2 = sci_nlp(text2)

sents = list(doc.sents)
sents2 = list(doc2.sents)

print("breakpoint")