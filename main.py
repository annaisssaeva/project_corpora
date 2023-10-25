#импортим все нужные модули
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from pymystem3 import Mystem
m = Mystem()
import ast
import re
import sqlite3
import sqlite3
from flask import Flask, url_for, render_template, request, redirect
import requests
import re
import itertools
from flask import Blueprint

pos_taggers = ('NOUN', 'ADJF', 'ADJS', 'COMP', 'VERB', 'INFN', 'PRTF',
               'PRTS', 'GRND', 'NUMR', 'ADVB', 'NPRO', 'PRED', 'PREP',
               'CONJ', 'PRCL', 'INTJ')

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