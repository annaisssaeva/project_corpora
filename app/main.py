#импортим все нужные модули
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from pymystem3 import Mystem
m = Mystem()
import ast
import sqlite3
from flask import Flask, url_for, render_template, request, redirect
import requests
import re
import itertools
from flask import Blueprint

sent_source = {}

with open("anecdotes.txt", "r", encoding="utf-8") as file:
    for source in file.read().split("\n\n\n")[1:]:
        for part in source.split("\n\n")[1:]:
            link = source.split("\n\n")[0]
            for sent in sent_tokenize(part):
                sent_source[sent] = link

def lemmatize(text):
  lemmas = m.lemmatize(text)
  lemm_sample = ''.join(lemmas)
  return lemm_sample

spisok = []
for sent in sent_source:
    sent = lemmatize(sent)
    sent = sent.rstrip()
    spisok.append(lemmatize(sent))

keys = list(sent_source.keys())
values = list(sent_source.values())
myList = list(zip(keys, values))

lemm_tuple = tuple(spisok)

result = []
for item, key in zip(myList, lemm_tuple):
    # Соединение элементов из списка my_tuple и значений из кортежа my_keys
    new_item = item + (key,)
    result.append(new_item)

import sqlite3

conn = sqlite3.connect("db_anectodes.db")
cur = conn.cursor()

cur.execute(
    """
CREATE TABLE IF NOT EXISTS texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    lemm_text TEXT,
    source TEXT

)
"""
)

conn.commit()

def exception(err_sent, error):
    with open("error.txt", "a+") as file:
        data = f"{error}: {err_sent}"
        file.write(data)
        file.write("\n")

def write_to_db(sentence, lemm_sentence, url):
    cur.execute(
        """
        INSERT INTO texts
            (text, lemm_text, source) VALUES (?, ?, ?)
        """,
        (
            sentence,
            lemm_sentence,
            url
        ),
    )
    conn.commit()

for res in result:
    try:
        write_to_db(res[0], res[2], res[1])
    except Exception as e:
        exception(sent, e)

pos_taggers = ('NOUN', 'ADJF', 'ADJS', 'COMP', 'VERB', 'INFN', 'PRTF',
               'PRTS', 'GRND', 'NUMR', 'ADVB', 'NPRO', 'PRED', 'PREP',
               'CONJ', 'PRCL', 'INTJ')


conn.commit()
print("предобработка выполнена")

app = Flask(__name__)

#при переходе на начальную страницу отображаем index.html
@app.route('/index')
def index_page():
    return render_template('index.html')

#при переходе просто на сайт стразу переводим на /index
@app.route('/')
def zero_page():
    return redirect(url_for('index_page'))

#при переходе на страницу /questions показываем страницу questions.html
@app.route('/questions')
def question_page():
    return render_template(
        'questions.html'
    )

#обрабатываем запрос и передаем переменную с ним на страницу с ответами
@app.route('/process', methods=['get'])
def process_page():
    if not request.args:
        return redirect(url_for('question_page'))
    zapros = request.args.get('zapros')

    return redirect(url_for('thanks_page', perem=zapros))


#страница с извинениями
@app.route('/sorry')
def sorry_page():
   return render_template('sorry.html')

#страница с результатами
@app.route('/results/<perem>')
def thanks_page(perem):
    print(f"получена переменная {perem}")

    con = sqlite3.connect('db_anectodes.db')
    cur = con.cursor()

    #определяем функции и с помощью них ищем предложения

    def first_function(word):
        res_sentences = {}
        cur.execute("SELECT * FROM texts")
        rows = cur.fetchall()
        if re.findall(r'"[^\s]+"', word):
            word = re.sub(r'[^А-яЁё]+', ' ', word)
            for row in rows:
                if word in row[1].lower():
                    res_sentences[row[1]] = row[3]

        else:
            if word in pos_taggers:
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for token in tokens:
                        if word in morph.parse(token)[0].tag:
                            if row[1] not in res_sentences:
                                res_sentences[row[1]] = row[3]
            else:
                lemm_word = morph.parse(word)[0].normal_form
                for row in rows:
                    if lemm_word in row[2]:
                        res_sentences[row[1]] = row[3]
        return res_sentences

    def second_function(word):
        word_and_pos = word.split('+')
        cur.execute("SELECT * FROM texts")
        rows = cur.fetchall()
        res_sentences = {}
        for row in rows:
            tokens = word_tokenize(row[1].lower())
            for token in tokens:
                if token == word_and_pos[0] and word_and_pos[1] in morph.parse(token)[0].tag:
                    res_sentences[row[1]] = row[3]
        return res_sentences

    def third_function(word_list):
        cur.execute("SELECT * FROM texts")
        rows = cur.fetchall()
        res_sentences = {}
        if re.findall(r'"[^\s]+"', word_list[0]):
            word_list[0] = re.sub(r'[^А-яЁё]+', '', word_list[0])
            for row in rows:
                tokens = word_tokenize(row[1].lower())
                for index, token in enumerate(tokens):
                    if index < (len(tokens) - 1):
                        if tokens[index] == word_list[0]:
                            if re.findall(r'"[^\s]+"', word_list[1]):
                                word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                if tokens[index + 1] == word_list[1]:
                                    res_sentences[row[1]] = row[3]
                            else:
                                if word_list[1] in pos_taggers:
                                    if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                        if row[1] not in res_sentences:
                                            res_sentences[row[1]] = row[3]
                                elif '+' in word_list[1]:
                                    if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[1] in \
                                            morph.parse(tokens[index + 1])[0].tag:
                                        res_sentences[row[1]] = row[3]
                                else:
                                    lemm_word = morph.parse(word_list[1])[0].normal_form
                                    if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                        res_sentences[row[1]] = row[3]
        else:
            if word_list[0] in pos_taggers:
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if word_list[0] in morph.parse(tokens[index])[0].tag:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if row[1] not in res_sentences:
                                                res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            res_sentences[row[1]] = row[3]
            if '+' in word_list[0]:
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if tokens[index] == word_list[0].split('+')[0] and word_list[0].split('+')[1] in \
                                    morph.parse(tokens[index])[0].tag:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if row[1] not in res_sentences:
                                                res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            res_sentences[row[1]] = row[3]
            else:
                lemm_word = morph.parse(word_list[0])[0].normal_form
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if morph.parse(tokens[index])[0].normal_form == lemm_word:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if row[1] not in res_sentences:
                                                res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            res_sentences[row[1]] = row[3]
        return res_sentences

    def forth_function(word_list):
        cur.execute("SELECT * FROM texts")
        rows = cur.fetchall()
        res_sentences = {}
        if re.findall(r'"[^\s]+"', word_list[0]):
            word_list[0] = re.sub(r'[^А-яЁё]+', '', word_list[0])
            for row in rows:
                tokens = word_tokenize(row[1].lower())
                for index, token in enumerate(tokens):
                    if index < (len(tokens) - 1):
                        if tokens[index] == word_list[0]:
                            if re.findall(r'"[^\s]+"', word_list[1]):
                                word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                if tokens[index + 1] == word_list[1]:
                                    if re.findall(r'"[^\s]+"', word_list[2]):
                                        word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                        if tokens[index + 2] == word_list[2]:
                                            res_sentences[row[1]] = row[3]
                                    else:
                                        if word_list[2] in pos_taggers:
                                            if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                res_sentences[row[1]] = row[3]
                                        if "+" in word_list[2]:
                                            if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                    word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[0].tag:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            lemm_word = morph.parse(word_list[2])[0].normal_form
                                            if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                res_sentences[row[1]] = row[3]
                            else:
                                if word_list[1] in pos_taggers:
                                    if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
                                if '+' in word_list[1]:
                                    if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[1] in \
                                            morph.parse(tokens[index + 1])[0].tag:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
                                else:
                                    lemm_word = morph.parse(word_list[1])[0].normal_form
                                    if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
        else:
            if word_list[0] in pos_taggers:
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if word_list[0] in morph.parse(tokens[index])[0].tag:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
            if '+' in word_list[0]:
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if tokens[index] == word_list[0].split('+')[0] and word_list[0].split('+')[1] in \
                                    morph.parse(tokens[index])[0].tag:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
            else:
                lemm_word = morph.parse(word_list[0])[0].normal_form
                for row in rows:
                    tokens = word_tokenize(row[1].lower())
                    for index, token in enumerate(tokens):
                        if index < (len(tokens) - 1):
                            if morph.parse(tokens[index])[0].normal_form == lemm_word:
                                if re.findall(r'"[^\s]+"', word_list[1]):
                                    word_list[1] = re.sub(r'[^А-яЁё]+', '', word_list[1])
                                    if tokens[index + 1] == word_list[1]:
                                        if re.findall(r'"[^\s]+"', word_list[2]):
                                            word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                            if tokens[index + 2] == word_list[2]:
                                                res_sentences[row[1]] = row[3]
                                        else:
                                            if word_list[2] in pos_taggers:
                                                if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            if '+' in word_list[2]:
                                                if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                        word_list[2].split('+')[1] in morph.parse(tokens[index + 2])[
                                                    0].tag:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                lemm_word = morph.parse(word_list[2])[0].normal_form
                                                if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                    res_sentences[row[1]] = row[3]
                                else:
                                    if word_list[1] in pos_taggers:
                                        if word_list[1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    if '+' in word_list[1]:
                                        if tokens[index + 1] == word_list[1].split('+')[0] and word_list[1].split('+')[
                                            1] in morph.parse(tokens[index + 1])[0].tag:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
                                    else:
                                        lemm_word = morph.parse(word_list[1])[0].normal_form
                                        if morph.parse(tokens[index + 1])[0].normal_form == lemm_word:
                                            if re.findall(r'"[^\s]+"', word_list[2]):
                                                word_list[2] = re.sub(r'[^А-яЁё]+', '', word_list[2])
                                                if tokens[index + 2] == word_list[2]:
                                                    res_sentences[row[1]] = row[3]
                                            else:
                                                if word_list[2] in pos_taggers:
                                                    if word_list[2] in morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                if '+' in word_list[2]:
                                                    if tokens[index + 2] == word_list[2].split('+')[0] and \
                                                            word_list[2].split('+')[1] in \
                                                            morph.parse(tokens[index + 2])[0].tag:
                                                        res_sentences[row[1]] = row[3]
                                                else:
                                                    lemm_word = morph.parse(word_list[2])[0].normal_form
                                                    if morph.parse(tokens[index + 2])[0].normal_form == lemm_word:
                                                        res_sentences[row[1]] = row[3]
        return res_sentences

    def search(input_request):
        input_list = input_request.split()
        if len(input_list) == 1:
            for input_word in input_list:
                if '+' in input_word:
                    return (second_function(input_word))
                else:
                    return (first_function(input_word))
        elif len(input_list) == 2:
            return third_function(input_list)
        elif len(input_list) == 3:
            return forth_function(input_list)

    print("функции обработаны")

    answer = search(perem)

    #если словарь пустой, то прееходим на страницу с извинениями
    if len(answer) == 0:
        otvet = "В корпусе ничего не найдено"
    #если не пустой — записываем все предложения в otvet
    else:
        otvet = ""
        for key in list(dict(answer).keys()):
            otvet += f"\n{key}\n\n Источник: {dict(answer)[key]}\n\n" \
                     f"————————————————————————————————————————————\n"


    if otvet == "В корпусе ничего не найдено":
        return redirect(url_for('sorry_page'))
    else:
        #на странице выводим и запрос, и ответы
        return render_template('results.html', otvet = otvet, zapros = perem)

if __name__ == '__main__':
    app.run(debug=True)
