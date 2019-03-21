# -*- coding: utf-8 -*-

import json
import struct
import subprocess
import yaml

from eccodes import *
from settings import GRIBS_DIR


def float_to_bin(x):
    if x == 0:
        return '0' * 64
    w, sign = (float.hex(x), 0) if x > 0 else (float.hex(x)[1:], 1)
    mantissa, exp = int(w[4:17], 16), int(w[18:])
    return '{}{:011b}{:052b}'.format(sign, exp + 1023, mantissa)


def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])


def calcTamGrade(lats, longs):
    """
    Tamanho da grade

    x = ultima longitude - primeira longitude 
    y = ultima latitude - primeira latitude

    """
    return [((longs[1]) - (longs[0])), ((lats[1]) - (lats[0]))]


def calcDistPontos(grade, ni, nj):
    """
    Distância entre os pontos da grade
    dy = grade[0] / nj
    dx = grade[1] / ni
    """
    return [(float(grade[0]) / float(nj)), (float(grade[1]) / float(ni))]


def verificaPonto(coord, limites, distP):
    if ((coord >= limites[0]) and (coord <= limites[1])):
        return int(round(((coord) - (limites[0])) / distP))
    else:
        exit(1)


def calcIndices(lats, longs, lat, lon, distP):
    """
    Calcula o índice equivalente ao ponto mais próximo da grade
    """
    return [
        [  
            1 if verificaPonto(lon, longs, distP[0]) <= 0 else verificaPonto(lon, longs, distP[0]),
            1 if verificaPonto(lon, longs, distP[0]) <= 0 else verificaPonto(lon, longs, distP[0]) - 1
        ],
        [
            1 if verificaPonto(lat, lats, distP[1]) <= 0 else verificaPonto(lat, lats, distP[1]),
            1 if verificaPonto(lat, lats, distP[1]) <= 0 else verificaPonto(lat, lats, distP[1]) - 1
        ]
    ]


def calcPontosProx(indices, distP, lats, longs):
    """
    Calcula os pontos próximos
    """
    return [
        [longs[0] + indices[0][0] * distP[1], longs[0] + indices[0][1] * distP[1]],
        [lats[0] + indices[1][0] * distP[0], lats[0] + indices[1][1] * distP[0]]
    ]


def calcDistancia(lat, lon, pontos, indices):
    """
    Calcula distância dos pontos próximos
    """
    return [
        {'Distancia': (((lon - pontos[0][0])**2) + ((lat - pontos[1][0])**2)), 'Lat': pontos[1][0], 'Lon': pontos[0][0], 'Pos': indices[1][0] * indices[0][0]},
        {'Distancia': (((lon - pontos[0][0])**2) + ((lat - pontos[1][1])**2)), 'Lat': pontos[1][1], 'Lon': pontos[0][0], 'Pos': indices[1][1] * indices[0][0]},
        {'Distancia': (((lon - pontos[0][1])**2) + ((lat - pontos[1][0])**2)), 'Lat': pontos[1][0], 'Lon': pontos[0][1], 'Pos': indices[1][0] * indices[0][1]},
        {'Distancia': (((lon - pontos[0][1])**2) + ((lat - pontos[1][1])**2)), 'Lat': pontos[1][1], 'Lon': pontos[0][1], 'Pos': indices[1][1] * indices[0][1]}
    ]


def acharMenorDistancia(distancias):
    menor = distancias[0]
    for d in distancias:
        if d['Distancia'] < menor['Distancia']:
            menor = d
    return menor


def pegarValor(indice, param, pk):
    indice -= 1
    i = 1
    f = open(GRIBS_DIR + param, 'rb')
    while 1:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            break
        if int(pk) == i:
            values = codes_get_values(gid)
            break
        else:
            i += 1
    codes_release(gid)
    f.close()
    return values[indice]


def is_binary(filename):
    with open(GRIBS_DIR + filename, 'rb') as f:
        for block in f:
            if b'\0' in block:
                return True
    return False