# -*- coding: utf-8 -*-
import binascii
import json
import os

from django.core.urlresolvers import reverse
from eccodes import *
from GRIB_API.settings import GRIBS_DIR, URL_BASE
from GRIB_API.utils import *
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def GetGribDataView(request, param=None, pk=None):
    lat = request.path.split('/')[-3]
    lon = request.path.split('/')[-2]
   
    i = 1

    f = open(GRIBS_DIR + param)
    while 1:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            break

        if int(pk) == i:
            f_lat = codes_get(gid, 'latitudeOfFirstGridPointInDegrees')
            l_lat = codes_get(gid, 'latitudeOfLastGridPointInDegrees')
            f_lon = codes_get(gid, 'longitudeOfFirstGridPointInDegrees')
            l_lon = codes_get(gid, 'longitudeOfLastGridPointInDegrees')
            ni = codes_get(gid, 'Ni')
            nj = codes_get(gid, 'Nj')
            break
        else:
            i += 1

        codes_release(gid)
    f.close()

    data = {}
    data['Arquivo_Lido'] = param
    data['GRIB_Lido'] = pk

    tamGrade = calcTamGrade([f_lat, l_lat], [f_lon, l_lon])
    distPontos = calcDistPontos(tamGrade, ni, nj)

    indices = calcIndices([f_lat, l_lat], [f_lon, l_lon], float(lat), float(lon), distPontos)
    pontosProximos = calcPontosProx(indices, distPontos, [f_lat, l_lat], [f_lon, l_lon])
    distancias = calcDistancia(float(lat), float(lon), pontosProximos, indices)
    menor = acharMenorDistancia(distancias)
    valor = pegarValor(menor['Pos'], param, pk)

    data['Ponto_Mais_Proximo'] = menor
    data['Valor'] = valor

    return Response(data)


@api_view(['GET'])
def ListFilesView(request):
    data = []
    
    for f in os.listdir(GRIBS_DIR):
        if is_binary(f):
            data.append({'Arquivo': f,'Link': URL_BASE + reverse('getParametros', kwargs={'param': f})})
    return Response({'Data': data})


@api_view(['GET'])
def GetParametrosView(request, param=None):
    if not param:
        return HttpResponseRedirect(reverse('listFiles'))

    f = open(GRIBS_DIR + param)
    parametro = []

    while 1:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            break
        parametro.append(codes_get(gid, 'parameterName'))
        codes_release(gid)
    f.close()

    data = {}
    data['Total'] = len(parametro)
    data['Arquivo_Lido'] = param
    data['Data'] = {}
    for i in xrange(len(parametro)):
        data['Data'][str(i + 1)] = {
            'Id' : i + 1,
            'Parametro' : parametro[i],
            'Link_Grib': URL_BASE + reverse('getGrib', kwargs={'param': param, 'pk': i + 1}),
            'Link_Sections': URL_BASE + reverse('getSections', kwargs={'param': param, 'pk': i + 1})
            }
    return Response(data)


@api_view(['GET'])
def GetGribView(request, param=None, pk=None): 
    i = 1

    f = open(GRIBS_DIR + param)
    while 1:
        gid = codes_grib_new_from_file(f)

        if gid is None:
            break

        if int(pk) == i:
            value = codes_get_size(gid, 'values')
            average = codes_get(gid, 'average')
            _min = codes_get(gid, 'min')
            _max = codes_get(gid, 'max')
            f_lat = codes_get(gid, 'latitudeOfFirstGridPointInDegrees')
            l_lat = codes_get(gid, 'latitudeOfLastGridPointInDegrees')
            f_lon = codes_get(gid, 'longitudeOfFirstGridPointInDegrees')
            l_lon = codes_get(gid, 'longitudeOfLastGridPointInDegrees')
            centre = codes_get(gid, 'centre')
            _data = codes_get(gid, 'dataDate')
            parametro = codes_get(gid, 'parameterName')
            elevacao = codes_get(gid, 'level')
            ni = codes_get(gid, 'Ni')
            nj = codes_get(gid, 'Nj')
            stepRange = codes_get(gid, 'stepRange')
            break
        else:
            i += 1

        codes_release(gid)
    f.close()

    data = {}
    data['Arquivo_Lido'] = param
    data['GRIB_Lido'] = pk

    data['Data'] = {}
    data['Data']['Total de Pontos'] = {'valor': value, 'parametro': 'values'}
    data['Data']['Media'] = {'valor': average, 'parametro': 'average'}
    data['Data']['Minimo'] = {'valor': _min, 'parametro': 'min'}
    data['Data']['Maximo'] = {'valor': _max, 'parametro': 'max'}
    data['Data']['Primeira Latitude (Degrees)'] = {'valor': f_lat, 'parametro': 'latitudeOfFirstGridPointInDegrees'}
    data['Data']['Ultima Latitude (Degrees)'] = {'valor': l_lat, 'parametro': 'latitudeOfLastGridPointInDegrees'}
    data['Data']['Primeira Longitude (Degrees)'] = {'valor': f_lon, 'parametro': 'longitudeOfFirstGridPointInDegrees'}
    data['Data']['Ultima Longitude (Degrees)'] = {'valor': l_lon, 'parametro': 'longitudeOfLastGridPointInDegrees'}
    data['Data']['Ultima Longitude (Degrees)'] = {'valor': l_lon, 'parametro': 'longitudeOfLastGridPointInDegrees'}
    data['Data']['Data'] = {'valor': _data, 'parametro': 'dataDate'}
    data['Data']['Centro'] = {'valor': centre, 'parametro': 'centre'}
    data['Data']['Parametro'] = {'valor': parametro, 'parametro': 'parameterName'}
    data['Data']['Elevacao'] = {'valor': elevacao, 'parametro': 'level'}
    data['Data']['Ni'] = {'valor': ni, 'parametro': 'Ni'}
    data['Data']['Nj'] = {'valor': nj, 'parametro': 'Nj'}
    data['Data']['Validade'] = {'valor': stepRange, 'parametro': 'stepRange'}

    return Response(data)


@api_view(['GET'])
def GetSectionsView(request, param=None, pk=None):
    grib = []

    # Section 0
    identifier = []
    totalLength = []
    editionNumber = []

    # Section 1
    section1Length = []
    table2Version = []
    centre = []
    generatingProcessIdentifier = []
    gridDefinition = []
    section1Flags = []
    indicatorOfParameter = []
    indicatorOfTypeOfLevel = []
    yearOfCentury = []
    month = []
    day = []
    hour = []
    minute = []
    unitOfTimeRange = []
    P1 = []
    P2 = []
    timeRangeIndicator = []
    numberIncludedInAverage = []
    numberMissingFromAveragesOrAccumulations = []
    centuryOfReferenceTimeOfData = []
    subCentre = []
    decimalScaleFactor = []

    # Section 2
    section2Length = []
    numberOfVerticalCoordinateValues = []
    pvlLocation = []
    dataRepresentationType = []

    # Section 3
    tableReference = []

    # Section 4
    section4Length = []
    dataFlag = []
    binaryScaleFactor = []
    referenceValue = []
    bitsPerValue = []

    # Section 5
    _7777 = []

    f = open(GRIBS_DIR + param)
    while 1:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            break

        grib.append(gid)

        # Section 0
        identifier.append(codes_get(gid, 'identifier'))
        totalLength.append(codes_get(gid, 'totalLength'))
        editionNumber.append(codes_get(gid, 'editionNumber'))

        # Section 1
        section1Length.append(codes_get(gid, 'section1Length'))
        table2Version.append(codes_get(gid, 'table2Version'))
        centre.append(codes_get(gid, 'centre'))
        generatingProcessIdentifier.append(codes_get(gid, 'generatingProcessIdentifier'))
        gridDefinition.append(codes_get(gid, 'gridDefinition'))
        section1Flags.append(codes_get(gid, 'section1Flags'))
        indicatorOfParameter.append(codes_get(gid, 'indicatorOfParameter'))
        indicatorOfTypeOfLevel.append(codes_get(gid, 'indicatorOfTypeOfLevel'))
        yearOfCentury.append(codes_get(gid, 'yearOfCentury'))
        month.append(codes_get(gid, 'month'))
        day.append(codes_get(gid, 'day'))
        hour.append(codes_get(gid, 'hour'))
        minute.append(codes_get(gid, 'minute'))
        unitOfTimeRange.append(codes_get(gid, 'unitOfTimeRange'))
        P1.append(codes_get(gid, 'P1'))
        P2.append(codes_get(gid, 'P2'))
        P2.append(codes_get(gid, 'P2'))
        timeRangeIndicator.append(codes_get(gid, 'timeRangeIndicator'))
        numberIncludedInAverage.append(codes_get(gid, 'numberIncludedInAverage'))
        numberMissingFromAveragesOrAccumulations.append(codes_get(gid, 'numberMissingFromAveragesOrAccumulations'))
        centuryOfReferenceTimeOfData.append(codes_get(gid, 'centuryOfReferenceTimeOfData'))
        subCentre.append(codes_get(gid, 'subCentre'))
        decimalScaleFactor.append(codes_get(gid, 'decimalScaleFactor'))

        # Section 2
        section2Length.append(codes_get(gid, 'section2Length'))
        numberOfVerticalCoordinateValues.append(codes_get(gid, 'numberOfVerticalCoordinateValues'))
        pvlLocation.append(codes_get(gid, 'pvlLocation'))
        dataRepresentationType.append(codes_get(gid, 'dataRepresentationType'))
        
        # Section 3
        tableReference.append(codes_get(gid, 'tableReference'))

        # Section 4
        section4Length.append(codes_get(gid, 'section4Length'))
        dataFlag.append(codes_get(gid, 'dataFlag'))
        binaryScaleFactor.append(codes_get(gid, 'binaryScaleFactor'))
        referenceValue.append(codes_get(gid, 'referenceValue'))
        bitsPerValue.append(codes_get(gid, 'bitsPerValue'))

        # Section 5
        _7777.append(codes_get(gid, '7777'))
        
        codes_release(gid)
    f.close()

    data = {}
    data['Arquivo_Lido'] = str(param)
    
    # Section 0
    data['Section_0'] = {}
    data['Section_0']['identifier'] = {
        'Decimal': identifier[int(pk) - 1],
        'Binario': bin(int(binascii.hexlify(identifier[int(pk) - 1]), 16)),
        'Hexadecimal': ' '.join([identifier[int(pk) - 1].encode('hex').upper()[i:i+2] for i in range(0, len(identifier[int(pk) - 1].encode('hex').upper()), 2)]),
        'Octeto': '01-04',
        'Descricao' : 'Início da Mensagem'
    }
    data['Section_0']['totalLength'] = {
        'Decimal': totalLength[int(pk) - 1],
        'Binario': bin(totalLength[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(totalLength[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(totalLength[int(pk) - 1]).upper()), 2)]),
        'Octeto': '05-07',
        'Descricao' : 'Tamanho da mensagem em bytes'
    }
    data['Section_0']['editionNumber'] = {
        'Decimal': editionNumber[int(pk) - 1],
        'Binario': bin(editionNumber[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(editionNumber[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(editionNumber[int(pk) - 1]).upper()), 2)]),
        'Octeto': '08-08',
        'Descricao' : 'Edição do GRIB'
    }

    # Section 1
    data['Section_1'] = {}
    data['Section_1']['section1Length'] = {
        'Decimal': section1Length[int(pk) - 1],
        'Binario': bin(section1Length[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(section1Length[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(section1Length[int(pk) - 1]).upper()), 2)]),
        'Octeto': '01-03',
        'Descricao' : 'Tamanho da mensagem em octetos'
    }
    data['Section_1']['table2Version'] = {
        'Decimal': table2Version[int(pk) - 1],
        'Binario': bin(table2Version[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(table2Version[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(table2Version[int(pk) - 1]).upper()), 2)]),
        'Octeto': '04-04',
        'Descricao' : 'Versão da Tabela'
    }
    try:
        int(centre[int(pk) - 1])
    except:
        data['Section_1']['centre'] = {
            'Decimal': centre[int(pk) - 1],
            'Binario': bin(int(binascii.hexlify(centre[int(pk) - 1]), 16)),
            'Hexadecimal': ' '.join([centre[int(pk) - 1].encode('hex').upper()[i:i+2] for i in range(0, len(centre[int(pk) - 1].encode('hex').upper()), 2)]),
            'Octeto': '05-05',
            'Descricao' : 'Centro'
        }
    else:
        data['Section_1']['centre'] = {
            'Decimal': int(centre[int(pk) - 1]),
            'Binario': bin(int(centre[int(pk) - 1])),
            'Hexadecimal': ' '.join([hex(int(centre[int(pk) - 1])).upper()[i:i+2] for i in range(0, len(hex(int(centre[int(pk) - 1])).upper()), 2)]),
            'Octeto': '05-05',
            'Descricao' : 'Centro'
        }
    data['Section_1']['generatingProcessIdentifier'] = {
        'Decimal': generatingProcessIdentifier[int(pk) - 1],
        'Binario': bin(generatingProcessIdentifier[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(generatingProcessIdentifier[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(generatingProcessIdentifier[int(pk) - 1]).upper()), 2)]),
        'Octeto': '06-06',
        'Descricao' : 'Identificação do Processo'
    }
    data['Section_1']['gridDefinition'] = {
        'Decimal': gridDefinition[int(pk) - 1],
        'Binario': bin(gridDefinition[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(gridDefinition[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(gridDefinition[int(pk) - 1]).upper()), 2)]),
        'Octeto': '07-07',
        'Descricao' : 'Definição da grade'
    }
    data['Section_1']['section1Flags'] = {
        'Decimal': section1Flags[int(pk) - 1],
        'Binario': bin(section1Flags[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(section1Flags[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(section1Flags[int(pk) - 1]).upper()), 2)]),
        'Octeto': '08-08',
        'Descricao' : 'Flag da seção 2'
    }
    data['Section_1']['indicatorOfParameter'] = {
        'Decimal': indicatorOfParameter[int(pk) - 1],
        'Binario': bin(indicatorOfParameter[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(indicatorOfParameter[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(indicatorOfParameter[int(pk) - 1]).upper()), 2)]),
        'Octeto': '09-09',
        'Descricao' : 'Parâmetro'
    }
    data['Section_1']['yearOfCentury'] = {
        'Decimal': yearOfCentury[int(pk) - 1],
        'Binario': bin(yearOfCentury[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(yearOfCentury[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(yearOfCentury[int(pk) - 1]).upper()), 2)]),
        'Octeto': '13-13',
        'Descricao' : 'Ano do século'
    }
    data['Section_1']['month'] = {
        'Decimal': month[int(pk) - 1],
        'Binario': bin(month[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(month[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(month[int(pk) - 1]).upper()), 2)]),
        'Octeto': '14-14',
        'Descricao' : 'Mês'
    }
    data['Section_1']['day'] = {
        'Decimal': day[int(pk) - 1],
        'Binario': bin(day[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(day[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(day[int(pk) - 1]).upper()), 2)]),
        'Octeto': '15-15',
        'Descricao' : 'Dia'
    }
    data['Section_1']['hour'] = {
        'Decimal': hour[int(pk) - 1],
        'Binario': bin(hour[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(hour[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(hour[int(pk) - 1]).upper()), 2)]),
        'Octeto': '16-16',
        'Descricao' : 'Hora'
    }
    data['Section_1']['minute'] = {
        'Decimal': minute[int(pk) - 1],
        'Binario': bin(minute[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(minute[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(minute[int(pk) - 1]).upper()), 2)]),
        'Octeto': '17-17',
        'Descricao' : 'Minuto'
    }
    data['Section_1']['unitOfTimeRange'] = {
        'Decimal': unitOfTimeRange[int(pk) - 1],
        'Binario': bin(unitOfTimeRange[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(unitOfTimeRange[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(unitOfTimeRange[int(pk) - 1]).upper()), 2)]),
        'Octeto': '18-18',
        'Descricao' : 'Unidade de tempo (hora)'
    }
    data['Section_1']['P1'] = {
        'Decimal': P1[int(pk) - 1],
        'Binario': bin(P1[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(P1[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(P1[int(pk) - 1]).upper()), 2)]),
        'Octeto': '19-19',
        'Descricao' : 'P1'
    }
    data['Section_1']['P2'] = {
        'Decimal': P2[int(pk) - 1],
        'Binario': bin(P2[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(P2[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(P2[int(pk) - 1]).upper()), 2)]),
        'Octeto': '20-20',
        'Descricao' : 'P2'
    }
    data['Section_1']['timeRangeIndicator'] = {
        'Decimal': timeRangeIndicator[int(pk) - 1],
        'Binario': bin(timeRangeIndicator[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(timeRangeIndicator[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(timeRangeIndicator[int(pk) - 1]).upper()), 2)]),
        'Octeto': '21-21',
        'Descricao' : 'Indicador do período de tempo (Validade do produto na hora de referência + P1)'
    }
    data['Section_1']['numberIncludedInAverage'] = {
        'Decimal': numberIncludedInAverage[int(pk) - 1],
        'Binario': bin(numberIncludedInAverage[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(numberIncludedInAverage[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(numberIncludedInAverage[int(pk) - 1]).upper()), 2)]),
        'Octeto': '22-23',
        'Descricao' : 'Número de incluído na média'
    }
    data['Section_1']['centuryOfReferenceTimeOfData'] = {
        'Decimal': centuryOfReferenceTimeOfData[int(pk) - 1],
        'Binario': bin(centuryOfReferenceTimeOfData[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(centuryOfReferenceTimeOfData[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(centuryOfReferenceTimeOfData[int(pk) - 1]).upper()), 2)]),
        'Octeto': '25-25',
        'Descricao' : 'Século de referência para a data'
    }
    data['Section_1']['numberMissingFromAveragesOrAccumulations'] = {
        'Decimal': numberMissingFromAveragesOrAccumulations[int(pk) - 1],
        'Binario': bin(numberMissingFromAveragesOrAccumulations[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(numberMissingFromAveragesOrAccumulations[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(numberMissingFromAveragesOrAccumulations[int(pk) - 1]).upper()), 2)]),
        'Octeto': '24-24',
        'Descricao' : 'Número de faltantes na média ou acumulado'
    }
    data['Section_1']['decimalScaleFactor'] = {
        'Decimal': decimalScaleFactor[int(pk) - 1],
        'Binario': bin(decimalScaleFactor[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(decimalScaleFactor[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(decimalScaleFactor[int(pk) - 1]).upper()), 2)]),
        'Octeto': '27-28',
        'Descricao' : 'Fator de escala decimal'
    }
    data['Section_1']['subCentre'] = {
        'Decimal': subCentre[int(pk) - 1],
        'Binario': bin(subCentre[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(subCentre[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(subCentre[int(pk) - 1]).upper()), 2)]),
        'Octeto': '26-26',
        'Descricao' : 'Sub-Centro'
    }

    # Section 2
    data['Section_2'] = {}
    data['Section_2']['section2Length'] = {
        'Decimal': section2Length[int(pk) - 1],
        'Binario': bin(section2Length[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(section2Length[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(section2Length[int(pk) - 1]).upper()), 2)]),
        'Octeto': '01-03',
        'Descricao' : 'Tamanho da mensagem em octetos'
    }
    data['Section_2']['numberOfVerticalCoordinateValues'] = {
        'Decimal': numberOfVerticalCoordinateValues[int(pk) - 1],
        'Binario': bin(numberOfVerticalCoordinateValues[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(numberOfVerticalCoordinateValues[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(numberOfVerticalCoordinateValues[int(pk) - 1]).upper()), 2)]),
        'Octeto': '04-04',
        'Descricao' : 'Número de valores na coordenada vertical'
    }
    data['Section_2']['pvlLocation'] = {
        'Decimal': pvlLocation[int(pk) - 1],
        'Binario': bin(pvlLocation[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(pvlLocation[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(pvlLocation[int(pk) - 1]).upper()), 2)]),
        'Octeto': '05-05',
        'Descricao': 'Lista de parâmetros de coordenadas verticais'
    }
    data['Section_2']['dataRepresentationType'] = {
        'Decimal': dataRepresentationType[int(pk) - 1],
        'Binario': bin(dataRepresentationType[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(dataRepresentationType[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(dataRepresentationType[int(pk) - 1]).upper()), 2)]),
        'Octeto': '06-06',
        'Descricao' : 'Tipo da representação dos dados'
    }
    
    # Section 3
    data['Section_3'] = {}
    data['Section_3']['tableReference'] = {
        'Decimal': tableReference[int(pk) - 1],
        'Binario': bin(tableReference[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(tableReference[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(tableReference[int(pk) - 1]).upper()), 2)]),
        'Octeto': '05-06',
        'Descricao' : 'Tabela de referência'
    }

    # Section 4
    data['Section_4'] = {}
    data['Section_4']['section4Length'] = {
        'Decimal': section4Length[int(pk) - 1],
        'Binario': bin(section4Length[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(section4Length[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(section4Length[int(pk) - 1]).upper()), 2)]),
        'Octeto': '01-03',
        'Descricao' : 'Tamanho da seção em octetos'
    }
    data['Section_4']['dataFlag'] = {
        'Decimal': dataFlag[int(pk) - 1],
        'Binario': bin(dataFlag[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(dataFlag[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(dataFlag[int(pk) - 1]).upper()), 2)]),
        'Octeto': '04-04',
        'Descricao' : 'Flag de dados'
    }
    data['Section_4']['binaryScaleFactor'] = {
        'Decimal': binaryScaleFactor[int(pk) - 1],
        'Binario': bin(binaryScaleFactor[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(binaryScaleFactor[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(binaryScaleFactor[int(pk) - 1]).upper()), 2)]),
        'Octeto': '05-06',
        'Descricao' : 'Fator de escala binário'
    }
    data['Section_4']['referenceValue'] = {
        'Decimal': referenceValue[int(pk) - 1],
        'Binario': float_to_bin(referenceValue[int(pk) - 1]),
        'Hexadecimal': ' '.join([float_to_hex(referenceValue[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(float_to_hex(referenceValue[int(pk) - 1]).upper()), 2)]),
        'Octeto': '07-10',
        'Descricao' : 'Valor de referência'
    }
    data['Section_4']['bitsPerValue'] = {
        'Decimal': bitsPerValue[int(pk) - 1],
        'Binario': bin(bitsPerValue[int(pk) - 1]),
        'Hexadecimal': ' '.join([hex(bitsPerValue[int(pk) - 1]).upper()[i:i+2] for i in range(0, len(hex(bitsPerValue[int(pk) - 1]).upper()), 2)]),
        'Octeto': '11-11',
        'Descricao' : 'Número de bits por valor'
    }

    # Section 5
    data['Section_5'] = {}
    data['Section_5']['7777'] = {
        'Decimal': int(_7777[int(pk) - 1]),
        'Binario': bin(int(binascii.hexlify(_7777[int(pk) - 1]), 16)),
        'Hexadecimal': ' '.join([_7777[int(pk) - 1].encode('hex').upper()[i:i+2] for i in range(0, len(_7777[int(pk) - 1].encode('hex').upper()), 2)]),
        'Octeto': '01-04',
        'Descricao' : 'Final de mensagem'
    }
    return Response(data)
