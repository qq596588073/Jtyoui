#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
# @Time  : 2019/8/4 1:50
# @Author: jtyoui@qq.com
from keras.models import Sequential, load_model
from keras.layers import Embedding, Bidirectional, LSTM, SpatialDropout1D, TimeDistributed, Dense
from keras_contrib.layers import CRF, crf
from keras.optimizers import Adam
from keras.utils.np_utils import np
from keras.callbacks import RemoteMonitor
from jtyoui.neuralNetwork.kerase.AnalyticalData import *
from keras.activations import relu

tag = {'O': 0, 'B-a': 1, 'I-a': 2, 'B-b': 3, 'I-b': 4, 'B-c': 5, 'I-c': 6}
vocab_path_model = 'data/vocab.pkl'
train_vocab_path = 'data/corpus.txt'
train_path = 'data/train.txt'
test_path = 'data/test.txt'
temp_path = 'data/crf.txt'
result_path = 'data/result.txt'
model_path = 'data/model-ner.h5'

# analysis_vocab(train_vocab_path, vocab_path_model)  # 训练vocab，只需要训练一次就够了
vocab = load_vocab(vocab_path_model)
length = analysis_rational_len(train_path, percent=0.93)


def train_model():
    train, label = vocab_train_label(train_path, vocab=vocab, tags=tag, max_chunk_length=length)
    n = np.array(label, dtype=np.float)
    labels = n.reshape((n.shape[0], n.shape[1], 1))
    model = Sequential([
        Embedding(input_dim=len(vocab), output_dim=300, mask_zero=True, input_length=length),
        SpatialDropout1D(0.2),
        Bidirectional(layer=LSTM(units=150, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)),
        TimeDistributed(Dense(len(tag), activation=relu)),
    ])
    crf_ = CRF(units=len(tag), sparse_target=True)
    model.add(crf_)
    model.compile(optimizer=Adam(), loss=crf_.loss_function, metrics=[crf_.accuracy])
    model.fit(x=np.array(train), y=labels, batch_size=12, epochs=8, callbacks=[RemoteMonitor()])
    model.save(model_path)


def predict_model():
    x_test, original = vocab_test(test_path, vocab, length)
    ws = open(temp_path, mode='w', newline='\n')
    tags = dict(zip(tag.values(), tag.keys()))
    custom_objects = {'CRF': CRF, 'crf_loss': crf.crf_loss, 'crf_viterbi_accuracy': crf.crf_viterbi_accuracy}
    model = load_model(model_path, custom_objects=custom_objects)
    for question, tests in zip(original, x_test):
        raw = model.predict([[tests]])[0][-len(question):]
        result = [np.argmax(row) for row in raw]
        answer = tuple(map(lambda x: tags[x], result))
        ma = map(lambda x: x[0] + '\t' + x[1] + '\n', zip(question, answer))
        ws.writelines(ma)
        ws.write('\n')
    ws.flush()
    ws.close()


if __name__ == '__main__':
    train_model()
    predict_model()
    restore_format(crf_path=temp_path, standard_path=result_path)
